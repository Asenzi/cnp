from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_id
from app.models.user import User
from app.models.user_interest import UserInterest
from app.network import (
    list_network_filter_options,
    list_network_recommendations,
    save_network_feedback,
    save_network_impressions,
)
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


def _serialize_interested_user(user: User, interest: UserInterest, request: Request) -> dict:
    business_user_id = str(user.user_id or "").strip()
    name = str(user.nickname or "").strip() or "未命名用户"
    intro = str(user.intro or "").strip()
    industry_label = str(user.industry_label or "").strip()
    company_name = str(user.company_name or "").strip()
    job_title = str(user.job_title or "").strip()
    city_name = str(user.city_name or "").strip()
    detail_line = _join_non_empty(industry_label, company_name, job_title) or city_name or "暂未完善行业"
    avatar = _public_avatar_url(user.avatar_url, request)
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
    tab: str = Query(default="recommend"),
    request_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    keyword: str | None = Query(default=None),
    city_name: str | None = Query(default=None),
    industry_label: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    exclude_user_ids: str | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    excluded_ids = [item.strip() for item in str(exclude_user_ids or "").split(",") if item and item.strip()]
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
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
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
    
    # 切换感兴趣状态
    is_interested = toggle_user_interest(
        db=db,
        user_pk=viewer.id,
        target_user_pk=target_pk,
        desired_state=desired,
    )
    
    return success_response(
        data={"is_interested": is_interested},
        message="已标记为感兴趣" if is_interested else "已取消感兴趣",
    )
