from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id, get_optional_current_user_id
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.profile_display import public_avatar_url, public_intro, public_nickname
from app.core.response import success_response
from app.crud import get_user_by_id
from app.models.user import User
from app.models.user_interest import UserInterest
from app.models.notification import Notification
from app.models.resource_post import ResourcePost
from app.network import (
    list_network_filter_options,
    list_network_recommendations,
    save_network_feedback,
    save_network_impressions,
)
from app.payment import resolve_member_snapshot
from app.schemas.network import NetworkFeedbackRequest, NetworkImpressionsBatchRequest

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/ping", summary="Network module health check")
def network_ping():
    return success_response(message="network module ready")


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="User not found", code=4041, status_code=404)
    return user


def _public_avatar_url(avatar_url: str | None, request: Request) -> str:
    normalized = str(avatar_url or settings.DEFAULT_AVATAR_URL or "/static/logo.png").strip()
    if not normalized or normalized == "/static/logo.png" or normalized.endswith("/static/logo.png"):
        return settings.DEFAULT_AVATAR_URL
    if normalized.startswith(("http://", "https://")):
        return normalized
    if not normalized.startswith("/"):
        return normalized
    return f"{str(request.base_url).rstrip('/')}{normalized}"


def _join_non_empty(*values: str | None) -> str:
    return " / ".join(str(item or "").strip() for item in values if str(item or "").strip())


def _parse_offset_cursor(cursor: str | None) -> int:
    try:
        return max(int(str(cursor or "").strip() or "0"), 0)
    except (TypeError, ValueError):
        return 0


def _city_name_candidates(city_name: str | None) -> list[str]:
    normalized = str(city_name or "").strip()
    if not normalized:
        return []

    candidates = [normalized]
    if normalized.endswith("市") and len(normalized) > 1:
        candidates.append(normalized[:-1])
    else:
        candidates.append(f"{normalized}市")

    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _encode_public_cursor(offset: int) -> str:
    return str(max(int(offset or 0), 0))


def _serialize_public_network_user(user: User, request: Request, db: Session, viewer_user_pk: int | None = None) -> dict:
    business_user_id = str(user.user_id or "").strip()
    name = public_nickname(user)
    industry_label = str(user.industry_label or "").strip()
    city_name = str(user.city_name or "").strip()
    company_name = str(user.company_name or "").strip()
    job_title = str(user.job_title or "").strip()
    detail_line = _join_non_empty(industry_label, company_name, job_title) or "暂未填写行业/职位"
    avatar = _public_avatar_url(public_avatar_url(user), request)
    circle_tags = [item for item in (industry_label, city_name) if item][:2]
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(user.id))

    # 查询用户发布的资源数量
    post_count = db.scalar(
        select(func.count(ResourcePost.id))
        .where(
            ResourcePost.author_user_pk == user.id,
            ResourcePost.status == "active"
        )
    ) or 0

    # 查询是否已关注
    is_followed = False
    if viewer_user_pk:
        from app.crud.network import get_user_follows
        follow_status = get_user_follows(
            db=db,
            follower_user_pk=viewer_user_pk,
            following_user_pks={int(user.id)}
        )
        is_followed = follow_status.get(int(user.id), False)

    return {
        "id": business_user_id,
        "userId": business_user_id,
        "user_id": business_user_id,
        "businessUserId": business_user_id,
        "business_user_id": business_user_id,
        "nickname": name,
        "name": name,
        "avatar": avatar,
        "avatar_url": avatar,
        "intro": public_intro(user) or "",
        "industry_label": industry_label,
        "city_name": city_name,
        "company_name": company_name,
        "job_title": job_title,
        "detailLine": detail_line,
        "detail_line": detail_line,
        "circleTags": circle_tags,
        "circle_tags": circle_tags,
        "circle_names": circle_tags,
        "is_verified": bool(user.is_verified),
        "verifyType": "lv1" if bool(user.is_verified) else "",
        "verifyText": "已认证" if bool(user.is_verified) else "",
        "is_member": bool(member_snapshot["is_member"]),
        "member_opened": bool(member_snapshot["member_opened"]),
        "is_vip": bool(member_snapshot["is_vip"]),
        "vip_opened": bool(member_snapshot["vip_opened"]),
        "member_status": str(member_snapshot["member_status"]),
        "vip_status": str(member_snapshot["vip_status"]),
        "member_expire_at": member_snapshot["member_expire_at"],
        "vip_expire_at": member_snapshot["vip_expire_at"],
        "member_plan_id": str(member_snapshot["member_plan_id"]),
        "member_plan_name": str(member_snapshot["member_plan_name"]),
        "is_followed": is_followed,
        "followed": is_followed,
        "active_text": "最近活跃",
        "activeText": "最近活跃",
        "reason_tags": ["推荐人脉"],
        "post_count": post_count,
        "postCount": post_count,
        "posts_count": post_count,
    }


def _list_public_network_recommendations(
    db: Session,
    *,
    request: Request,
    cursor: str | None,
    limit: int,
    keyword: str | None,
    city_name: str | None,
    industry_label: str | None,
    viewer_user_pk: int | None = None,
) -> dict:
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _parse_offset_cursor(cursor)
    safe_keyword = str(keyword or "").strip()
    safe_city = str(city_name or "").strip()
    safe_industry = str(industry_label or "").strip()
    conditions = [User.is_active.is_(True)]
    base_conditions = list(conditions)
    if safe_city and safe_city != "全国":
        conditions.append(User.city_name.in_(_city_name_candidates(safe_city)))
    if safe_industry:
        conditions.append(User.industry_label == safe_industry)
        base_conditions.append(User.industry_label == safe_industry)
    if safe_keyword:
        like_keyword = f"%{safe_keyword}%"
        keyword_condition = (
            (User.nickname.like(like_keyword))
            | (User.company_name.like(like_keyword))
            | (User.job_title.like(like_keyword))
            | (User.industry_label.like(like_keyword))
            | (User.city_name.like(like_keyword))
        )
        conditions.append(keyword_condition)
        base_conditions.append(keyword_condition)
    def _fetch_rows(active_conditions: list) -> list[User]:
        return db.execute(
            select(User)
            .where(*active_conditions)
            .order_by(User.is_verified.desc(), User.updated_at.desc(), User.created_at.desc(), User.id.desc())
            .offset(offset)
            .limit(safe_limit + 1)
        ).scalars().all()

    rows = _fetch_rows(conditions)
    if not rows and safe_city and safe_city != "全国":
        rows = _fetch_rows(base_conditions)
    page_rows = rows[:safe_limit]
    has_more = len(rows) > safe_limit
    return {
        "request_id": "",
        "items": [_serialize_public_network_user(user, request, db, viewer_user_pk) for user in page_rows],
        "next_cursor": _encode_public_cursor(offset + len(page_rows)) if has_more else "",
        "has_more": has_more,
    }


def _serialize_interested_user(user: User, interest: UserInterest, request: Request) -> dict:
    business_user_id = str(user.user_id or "").strip()
    name = public_nickname(user)
    intro = public_intro(user) or ""
    industry_label = str(user.industry_label or "").strip()
    company_name = str(user.company_name or "").strip()
    job_title = str(user.job_title or "").strip()
    city_name = str(user.city_name or "").strip()
    detail_line = _join_non_empty(industry_label, company_name, job_title) or "暂未填写行业/职位"
    avatar = _public_avatar_url(public_avatar_url(user), request)
    circle_tags = [intro] if intro else [item for item in (industry_label, city_name) if item][:2]

    return {
        "id": business_user_id,
        "userId": business_user_id,
        "user_id": business_user_id,
        "businessUserId": business_user_id,
        "business_user_id": business_user_id,
        "nickname": name,
        "name": name,
        "avatar": avatar,
        "avatar_url": avatar,
        "intro": intro,
        "industry_label": industry_label,
        "city_name": city_name,
        "company_name": company_name,
        "job_title": job_title,
        "detailLine": detail_line,
        "detail_line": detail_line,
        "circleTags": circle_tags,
        "circle_tags": circle_tags,
        "circle_names": circle_tags,
        "is_verified": bool(user.is_verified),
        "verifyType": "lv1" if bool(user.is_verified) else "",
        "verifyText": "已认证" if bool(user.is_verified) else "",
        "is_interested": True,
        "interested": True,
        "active_text": "最近活跃",
        "activeText": "最近活跃",
        "created_at": interest.created_at.isoformat() if interest.created_at else None,
    }


@router.get("/recommendations", summary="Get network recommendations")
def get_network_recommendations(
    request: Request,
    tab: str = Query(default="recommend"),
    request_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    keyword: str | None = Query(default=None),
    city_name: str | None = Query(default=None),
    industry_label: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    exclude_user_ids: str | None = Query(default=None),
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    excluded_ids = [item.strip() for item in str(exclude_user_ids or "").split(",") if item and item.strip()]

    # 如果未登录，使用简单的公开推荐
    if user_id is None:
        payload = _list_public_network_recommendations(
            db=db,
            request=request,
            cursor=cursor,
            limit=limit,
            keyword=keyword,
            city_name=city_name,
            industry_label=industry_label,
            viewer_user_pk=None,
        )
        return success_response(data=payload)

    # 登录用户使用完整的推荐逻辑
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    payload = list_network_recommendations(
        db=db,
        viewer=viewer,
        tab=tab,
        request_id=request_id,
        cursor=cursor,
        limit=limit,
        keyword=keyword,
        city_name=city_name,
        industry_label=industry_label,
        domain=domain,
        exclude_business_user_ids=excluded_ids,
    )
    return success_response(data=payload)


@router.get("/filters", summary="Get network filter options")
def get_network_filters(
    db: Session = Depends(db_session),
):
    payload = list_network_filter_options(db=db)
    return success_response(data=payload)


@router.post("/impressions/batch", summary="Report network recommendation impressions")
def report_network_impressions_batch(
    payload: NetworkImpressionsBatchRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    recorded = save_network_impressions(
        db=db,
        viewer=viewer,
        target_business_user_ids=payload.target_user_ids,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
    )
    return success_response(
        data={"recorded": recorded},
        message="impressions recorded",
    )


@router.post("/feedback", summary="Report network recommendation feedback")
def report_network_feedback(
    payload: NetworkFeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    saved = save_network_feedback(
        db=db,
        viewer=viewer,
        target_business_user_id=payload.target_user_id,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
        event_type=payload.event_type,
        ext=payload.ext,
    )
    return success_response(
        data={"saved": bool(saved)},
        message="feedback recorded" if saved else "feedback ignored",
    )


@router.get("/interests", summary="List interested network users")
def get_network_interests(
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    offset = _parse_offset_cursor(cursor)
    safe_limit = min(max(int(limit or 20), 1), 50)

    stmt = (
        select(UserInterest, User)
        .join(User, User.id == UserInterest.target_user_pk)
        .where(
            UserInterest.user_pk == int(viewer.id),
            User.is_active.is_(True),
        )
        .order_by(UserInterest.created_at.desc(), UserInterest.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    )
    rows = db.execute(stmt).all()
    page_rows = rows[:safe_limit]
    has_more = len(rows) > safe_limit
    items = [
        _serialize_interested_user(user=target_user, interest=interest, request=request)
        for interest, target_user in page_rows
    ]

    return success_response(
        data={
            "items": items,
            "next_cursor": str(offset + len(items)) if has_more else "",
            "has_more": has_more,
        }
    )



@router.post("/interest/toggle", summary="Toggle user interest status")
def toggle_interest(
    target_user_id: str = Query(..., description="Target user business ID"),
    desired: bool | None = Query(default=None, description="Desired interest state"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """切换对目标用户的感兴趣状态"""
    from app.crud.network import map_business_user_ids_to_pks, toggle_user_interest
    
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    
    # 将business_user_id转换为user_pk
    mapping = map_business_user_ids_to_pks(db=db, business_user_ids={target_user_id})
    target_pk = mapping.get(target_user_id)
    
    if not target_pk:
        raise BusinessException(message="Target user not found", code=4042, status_code=404)
    
    if target_pk == viewer.id:
        raise BusinessException(message="Cannot mark yourself as interested", code=4003, status_code=400)
    
    existing_interest = db.scalar(
        select(UserInterest.id).where(
            UserInterest.user_pk == int(viewer.id),
            UserInterest.target_user_pk == int(target_pk),
        )
    )

    # 切换感兴趣状态
    is_interested = toggle_user_interest(
        db=db,
        user_pk=viewer.id,
        target_user_pk=target_pk,
        desired_state=desired,
    )

    if is_interested and existing_interest is None:
        db.add(
            Notification(
                user_pk=int(target_pk),
                actor_user_pk=int(viewer.id),
                type="collection",
                title="新的人脉收藏",
                content=f"{public_nickname(viewer)}收藏了你",
                link_type="user",
                link_id=str(viewer.user_id or "").strip(),
                is_read=False,
            )
        )
        db.commit()
    
    return success_response(
        data={"is_interested": is_interested, "is_collected": is_interested},
        message="已收藏" if is_interested else "已取消收藏",
    )


@router.post("/follow/toggle", summary="Toggle user follow status")
def toggle_follow(
    target_user_id: str = Query(..., description="Target user business ID"),
    desired: bool | None = Query(default=None, description="Desired follow state"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """切换对目标用户的关注状态"""
    from app.crud.network import map_business_user_ids_to_pks, toggle_user_follow
    from app.models.user_follow import UserFollow

    viewer = _require_current_user(db=db, current_user_pk=user_id)

    # 将business_user_id转换为user_pk
    mapping = map_business_user_ids_to_pks(db=db, business_user_ids={target_user_id})
    target_pk = mapping.get(target_user_id)

    if not target_pk:
        raise BusinessException(message="Target user not found", code=4042, status_code=404)

    if target_pk == viewer.id:
        raise BusinessException(message="Cannot follow yourself", code=4003, status_code=400)

    existing_follow = db.scalar(
        select(UserFollow.id).where(
            UserFollow.follower_user_pk == int(viewer.id),
            UserFollow.following_user_pk == int(target_pk),
        )
    )

    # 切换关注状态
    is_followed = toggle_user_follow(
        db=db,
        follower_user_pk=viewer.id,
        following_user_pk=target_pk,
        desired_state=desired,
    )

    if is_followed and existing_follow is None:
        db.add(
            Notification(
                user_pk=int(target_pk),
                actor_user_pk=int(viewer.id),
                type="network",
                title="新的人脉关注",
                content=f"{public_nickname(viewer)}关注了你",
                link_type="user",
                link_id=str(viewer.user_id or "").strip(),
                is_read=False,
            )
        )
        db.commit()

    return success_response(
        data={"is_followed": is_followed},
        message="关注成功" if is_followed else "已取消关注",
    )
