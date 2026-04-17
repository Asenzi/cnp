import base64
import hashlib
import json
from datetime import UTC, datetime
from math import log1p
from secrets import token_hex
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.models.circle import Circle
from app.models.resource_post import ResourcePost, ResourcePostLike
from app.models.resource_post_circle_sync import ResourcePostCircleSync
from app.models.user import User
from app.models.user_circle_membership import UserCircleMembership
from app.payment import resolve_member_snapshot
from app.points import grant_publish_resource_points

SUPPORTED_POST_MODES = {"cooperate", "resource", "venue"}
SUPPORTED_SORT_KEYS = {"latest", "popular"}
SUPPORTED_MANAGE_STATUS = {"active", "offline"}
SUPPORTED_CIRCLE_SYNC_STATUS = {"pending", "approved", "rejected", "cancelled"}


def _normalize_circle_codes(circle_codes: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in circle_codes or []:
        code = _normalize_text(item).upper()[:16]
        if not code or code in seen:
            continue
        seen.add(code)
        normalized.append(code)
    return normalized


def _resolve_circle_sync_limit(db: Session, *, user: User) -> int:
    if not bool(user.is_verified):
        return 0
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(user.id))
    if bool(member_snapshot.get("is_member")):
        return 5
    return 1


def _serialize_circle_sync(
    sync: ResourcePostCircleSync,
    *,
    circle: Circle | None = None,
) -> dict[str, Any]:
    return {
        "id": int(sync.id),
        "circle_code": _normalize_text(sync.circle_code),
        "circle_name": _normalize_text(circle.name if circle else ""),
        "status": _normalize_text(sync.status) or "pending",
        "reject_reason": _normalize_text(sync.reject_reason),
        "reviewed_at": sync.reviewed_at.isoformat() if sync.reviewed_at else None,
        "created_at": sync.created_at.isoformat() if sync.created_at else None,
    }


def _load_post_circle_sync_rows(
    db: Session,
    *,
    post_pk: int,
) -> list[tuple[ResourcePostCircleSync, Circle | None]]:
    rows = db.execute(
        select(ResourcePostCircleSync, Circle)
        .outerjoin(Circle, Circle.circle_code == ResourcePostCircleSync.circle_code)
        .where(ResourcePostCircleSync.post_pk == int(post_pk))
        .order_by(ResourcePostCircleSync.created_at.desc(), ResourcePostCircleSync.id.desc())
    ).all()
    return [(sync, circle) for sync, circle in rows]


def _get_related_circle_codes(db: Session, *, post_pk: int) -> set[str]:
    rows = db.execute(
        select(ResourcePostCircleSync.circle_code).where(ResourcePostCircleSync.post_pk == int(post_pk))
    ).all()
    return {
        _normalize_text(item[0]).upper()
        for item in rows
        if _normalize_text(item[0])
    }


def _refresh_circle_post_counts(db: Session, *, circle_codes: set[str] | list[str]) -> None:
    normalized_codes = {code for code in (_normalize_text(item).upper() for item in circle_codes) if code}
    if not normalized_codes:
        return

    count_rows = db.execute(
        select(ResourcePostCircleSync.circle_code, func.count(ResourcePostCircleSync.id))
        .join(ResourcePost, ResourcePost.id == ResourcePostCircleSync.post_pk)
        .where(
            ResourcePostCircleSync.circle_code.in_(normalized_codes),
            ResourcePostCircleSync.status == "approved",
            ResourcePost.status == "active",
        )
        .group_by(ResourcePostCircleSync.circle_code)
    ).all()
    count_map = {
        _normalize_text(circle_code).upper(): int(count or 0)
        for circle_code, count in count_rows
        if _normalize_text(circle_code)
    }

    circles = db.execute(select(Circle).where(Circle.circle_code.in_(normalized_codes))).scalars().all()
    now = datetime.now(UTC).replace(tzinfo=None)
    for circle in circles:
        next_count = int(count_map.get(_normalize_text(circle.circle_code).upper(), 0))
        circle.post_count = next_count
        if next_count > 0:
            circle.last_active_at = now
        db.add(circle)


def _sync_post_to_circles(
    db: Session,
    *,
    post: ResourcePost,
    author: User,
    sync_circle_codes: list[str] | None,
) -> list[dict[str, Any]]:
    normalized_codes = _normalize_circle_codes(sync_circle_codes)
    sync_limit = _resolve_circle_sync_limit(db=db, user=author)
    if normalized_codes and sync_limit <= 0:
        raise BusinessException(message="完成实名认证后才可同步资源到圈子", code=5463, status_code=400)
    if len(normalized_codes) > sync_limit:
        raise BusinessException(
            message=f"当前账号最多可同时同步 {sync_limit} 个圈子",
            code=5464,
            status_code=400,
        )

    joined_circle_codes = {
        _normalize_text(item).upper()
        for item in db.execute(
            select(UserCircleMembership.circle_code).where(
                UserCircleMembership.user_pk == int(author.id),
                UserCircleMembership.is_active.is_(True),
            )
        ).scalars().all()
        if _normalize_text(item)
    }

    if any(code not in joined_circle_codes for code in normalized_codes):
        raise BusinessException(message="仅可同步到自己已加入的圈子", code=5465, status_code=400)

    circles = db.execute(
        select(Circle).where(
            Circle.circle_code.in_(normalized_codes),
            Circle.status == "active",
        )
    ).scalars().all()
    circle_map = {
        _normalize_text(circle.circle_code).upper(): circle
        for circle in circles
        if _normalize_text(circle.circle_code)
    }
    missing_codes = [code for code in normalized_codes if code not in circle_map]
    if missing_codes:
        raise BusinessException(message="部分圈子不存在或不可同步", code=5466, status_code=400)

    existing_rows = db.execute(
        select(ResourcePostCircleSync).where(ResourcePostCircleSync.post_pk == int(post.id))
    ).scalars().all()
    existing_map = {
        _normalize_text(item.circle_code).upper(): item
        for item in existing_rows
        if _normalize_text(item.circle_code)
    }
    selected_set = set(normalized_codes)
    affected_codes = set(existing_map.keys()) | selected_set
    now = datetime.now(UTC).replace(tzinfo=None)

    for code, row in existing_map.items():
        if code not in selected_set and row.status != "cancelled":
            row.status = "cancelled"
            row.reviewed_by_user_pk = None
            row.reviewed_at = now
            row.reject_reason = None
            db.add(row)

    for code in normalized_codes:
        row = existing_map.get(code)
        if row is None:
            row = ResourcePostCircleSync(
                post_pk=int(post.id),
                circle_code=code,
                request_user_pk=int(author.id),
                status="pending",
            )
            db.add(row)
            continue

        if row.status in {"cancelled", "rejected"}:
            row.status = "pending"
            row.reviewed_by_user_pk = None
            row.reviewed_at = None
            row.reject_reason = None
            db.add(row)

    _refresh_circle_post_counts(db=db, circle_codes=affected_codes)
    db.flush()

    sync_rows = _load_post_circle_sync_rows(db=db, post_pk=int(post.id))
    return [
        _serialize_circle_sync(sync, circle=circle)
        for sync, circle in sync_rows
        if _normalize_text(sync.status) != "cancelled"
    ]


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_lower(value: str | None) -> str:
    return _normalize_text(value).lower()


def _clamp_score(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _days_since(value: datetime | None, *, now: datetime) -> float:
    if value is None:
        return 365.0
    safe_value = value
    if safe_value.tzinfo is not None:
        safe_value = safe_value.astimezone(UTC).replace(tzinfo=None)
    return max((now - safe_value).total_seconds(), 0.0) / 86400.0


def _datetime_timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    safe_value = value
    if safe_value.tzinfo is not None:
        safe_value = safe_value.astimezone(UTC).replace(tzinfo=None)
    return max(safe_value.timestamp(), 0.0)


def _request_rotation_jitter(*, viewer_user_pk: int, post_pk: int, request_salt: str) -> float:
    digest = hashlib.sha1(f"{viewer_user_pk}:{post_pk}:{request_salt}".encode("utf-8")).hexdigest()
    raw_value = int(digest[:8], 16) / 0xFFFFFFFF
    return max(0.0, min(raw_value, 1.0))


def _resource_keyword_bonus(post: ResourcePost, author: User, keyword: str | None) -> float:
    normalized_keyword = _normalize_lower(keyword)
    if not normalized_keyword:
        return 0.0

    title = _normalize_lower(post.title)
    description = _normalize_lower(post.description)
    industry = _normalize_lower(post.industry_label or author.industry_label)
    author_name = _normalize_lower(author.nickname)
    author_city = _normalize_lower(author.city_name)

    score = 0.0
    if title == normalized_keyword:
        score += 0.34
    elif normalized_keyword in title:
        score += 0.28

    if normalized_keyword in description:
        score += 0.18
    if normalized_keyword in industry:
        score += 0.16
    if normalized_keyword in author_name:
        score += 0.10
    if normalized_keyword in author_city:
        score += 0.06

    return min(score, 0.44)


def _prioritize_fresh_post_rows(
    *,
    rows: list[tuple[float, tuple[ResourcePost, User, bool, bool, bool]]],
    excluded_post_codes: set[str],
    window_size: int,
) -> list[tuple[float, tuple[ResourcePost, User, bool, bool, bool]]]:
    if not excluded_post_codes or len(rows) <= 1:
        return rows

    fresh_rows = [
        row for row in rows
        if _normalize_text(row[1][0].post_code).upper() not in excluded_post_codes
    ]
    repeat_rows = [
        row for row in rows
        if _normalize_text(row[1][0].post_code).upper() in excluded_post_codes
    ]
    safe_window_size = min(max(int(window_size or 0), 1), len(rows))
    if len(fresh_rows) < safe_window_size:
        return rows
    return fresh_rows + repeat_rows


def _shuffle_resource_rows(
    *,
    rows: list[tuple[float, tuple[ResourcePost, User, bool, bool, bool]]],
    viewer_user_pk: int,
    request_salt: str,
    window_size: int,
) -> list[tuple[float, tuple[ResourcePost, User, bool, bool, bool]]]:
    if not request_salt or len(rows) <= 1:
        return rows

    safe_window_size = min(max(int(window_size or 0), 1), len(rows))
    head_rows = rows[:safe_window_size]
    tail_rows = rows[safe_window_size:]

    def shuffle_key(item: tuple[float, tuple[ResourcePost, User, bool, bool, bool]]) -> float:
        post = item[1][0]
        return _request_rotation_jitter(
            viewer_user_pk=int(viewer_user_pk),
            post_pk=int(post.id),
            request_salt=request_salt,
        )

    pinned_rows = [row for row in head_rows if bool(row[1][0].is_pinned)]
    regular_rows = [row for row in head_rows if not bool(row[1][0].is_pinned)]
    shuffled_head_rows = sorted(pinned_rows, key=shuffle_key, reverse=True) + sorted(
        regular_rows,
        key=shuffle_key,
        reverse=True,
    )
    return shuffled_head_rows + tail_rows


def _encode_cursor(offset: int) -> str | None:
    if offset <= 0:
        return None
    payload = json.dumps({"offset": int(offset)}, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
        return max(int(payload.get("offset", 0)), 0)
    except Exception:  # noqa: BLE001
        return 0


def _format_time_text(raw_time: datetime | None) -> str:
    if not raw_time:
        return ""

    now = datetime.now(UTC).replace(tzinfo=None)
    target = raw_time.replace(tzinfo=None) if raw_time.tzinfo else raw_time
    delta = now - target
    total_seconds = max(int(delta.total_seconds()), 0)
    total_days = total_seconds // (24 * 3600)

    if total_days <= 0:
        if total_seconds < 60:
            return "刚刚"
        if total_seconds < 3600:
            return f"{max(total_seconds // 60, 1)}分钟前"
        return f"{max(total_seconds // 3600, 1)}小时前"
    if total_days == 1:
        return "昨天"
    if total_days <= 6:
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[target.weekday()]
    return target.strftime("%m-%d")


def _parse_images(images_json: str | None) -> list[str]:
    if not images_json:
        return []
    try:
        parsed = json.loads(images_json)
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item or "").strip()]


def _build_images_json(images: list[str]) -> str | None:
    normalized = [str(item or "").strip()[:255] for item in images if str(item or "").strip()]
    if not normalized:
        return None
    return json.dumps(normalized[:9], ensure_ascii=False)


def _generate_post_code(db: Session) -> str:
    for _ in range(8):
        code = f"RP{token_hex(4).upper()}"
        exists = db.execute(select(ResourcePost.id).where(ResourcePost.post_code == code)).scalar_one_or_none()
        if exists is None:
            return code
    raise BusinessException(message="生成资源编号失败，请稍后重试", code=5451, status_code=500)


def _serialize_post(
    post: ResourcePost,
    author: User,
    *,
    liked: bool = False,
    viewer_user_pk: int | None = None,
    circle_syncs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    is_author = bool(viewer_user_pk is not None and int(post.author_user_pk) == int(viewer_user_pk))
    payload = {
        "post_code": str(post.post_code),
        "mode": str(post.mode or "cooperate"),
        "industry_label": str(post.industry_label or "").strip(),
        "title": str(post.title or "").strip(),
        "description": str(post.description or "").strip(),
        "images": _parse_images(post.images_json),
        "view_count": int(post.view_count or 0),
        "like_count": int(post.like_count or 0),
        "comment_count": int(post.comment_count or 0),
        "status": str(post.status or "active"),
        "is_pinned": bool(post.is_pinned),
        "pinned_at": post.pinned_at.isoformat() if post.pinned_at else None,
        "liked": bool(liked),
        "is_author": is_author,
        "time_text": _format_time_text(post.created_at),
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "author": {
            "user_id": str(author.user_id or "").strip(),
            "company_name": str(author.company_name or "").strip(),
            "job_title": str(author.job_title or "").strip(),
            "nickname": str(author.nickname or "").strip() or "未命名用户",
            "avatar_url": str(author.avatar_url or "").strip() or "/static/logo.png",
            "role": str(author.industry_label or "").strip() or "商务人士",
            "is_verified": bool(author.is_verified),
        },
    }
    if circle_syncs is not None:
        payload["circle_syncs"] = circle_syncs
    return payload


def _resolve_post_with_author(db: Session, *, post_code: str) -> tuple[ResourcePost, User]:
    safe_code = str(post_code or "").strip().upper()
    if not safe_code:
        raise BusinessException(message="资源编号不能为空", code=5455, status_code=400)
    row = db.execute(
        select(ResourcePost, User)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(ResourcePost.post_code == safe_code)
        .limit(1)
    ).first()
    if row is None:
        raise BusinessException(message="资源不存在", code=5456, status_code=404)
    return row


def _assert_manage_author(post: ResourcePost, viewer_user_pk: int) -> None:
    if int(post.author_user_pk) != int(viewer_user_pk):
        raise BusinessException(message="仅作者可操作该资源", code=5457, status_code=403)
    if str(post.status or "") == "deleted":
        raise BusinessException(message="资源已删除", code=5458, status_code=400)


def list_resource_filter_options(db: Session) -> dict[str, Any]:
    rows = db.execute(
        select(ResourcePost.industry_label)
        .where(
            ResourcePost.status == "active",
            ResourcePost.industry_label.is_not(None),
            ResourcePost.industry_label != "",
        )
        .group_by(ResourcePost.industry_label)
        .order_by(func.max(ResourcePost.created_at).desc())
        .limit(30)
    ).all()
    industries = [str(row[0]).strip() for row in rows if str(row[0] or "").strip()]
    return {
        "modes": ["cooperate", "resource", "venue"],
        "sorts": ["latest", "popular"],
        "industries": industries,
    }


def list_resource_posts(
    db: Session,
    *,
    viewer_user_pk: int,
    mode: str | None,
    keyword: str | None,
    industry_label: str | None,
    sort_key: str | None,
    request_id: str | None,
    exclude_post_codes: list[str] | None,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    safe_mode = str(mode or "").strip().lower()
    safe_keyword = str(keyword or "").strip()
    safe_industry = str(industry_label or "").strip()
    safe_sort = str(sort_key or "latest").strip().lower()
    if safe_sort not in SUPPORTED_SORT_KEYS:
        safe_sort = "latest"

    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)
    active_request_id = _normalize_text(request_id) or token_hex(8)
    excluded_post_code_set = {
        _normalize_text(item).upper()
        for item in (exclude_post_codes or [])
        if _normalize_text(item)
    }

    viewer = db.execute(select(User).where(User.id == int(viewer_user_pk)).limit(1)).scalar_one_or_none()
    if viewer is None:
        raise BusinessException(message="鐢ㄦ埛涓嶅瓨鍦?", code=4041, status_code=404)
    viewer_industry = _normalize_lower(viewer.industry_label)
    viewer_city = _normalize_lower(viewer.city_name)

    where_conditions = [ResourcePost.status == "active", User.is_active.is_(True)]
    if safe_mode in SUPPORTED_POST_MODES:
        where_conditions.append(ResourcePost.mode == safe_mode)
    if safe_industry:
        where_conditions.append(ResourcePost.industry_label == safe_industry)
    if safe_keyword:
        like_keyword = f"%{safe_keyword}%"
        where_conditions.append(
            or_(
                ResourcePost.title.like(like_keyword),
                ResourcePost.description.like(like_keyword),
                ResourcePost.industry_label.like(like_keyword),
                User.nickname.like(like_keyword),
            )
        )

    base_query = (
        select(ResourcePost, User)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(*where_conditions)
    )

    rows = db.execute(base_query).all()

    now = datetime.now(UTC).replace(tzinfo=None)
    scored_rows: list[tuple[float, tuple[ResourcePost, User, bool, bool, bool]]] = []
    for post, author in rows:
        same_industry = bool(viewer_industry) and (
            _normalize_lower(post.industry_label) == viewer_industry
            or _normalize_lower(author.industry_label) == viewer_industry
        )
        same_city = bool(viewer_city) and _normalize_lower(author.city_name) == viewer_city
        author_verified = bool(author.is_verified)
        pinned_bonus = 0.18 if bool(post.is_pinned) else 0.0
        freshness_days = _days_since(post.created_at, now=now)
        freshness_score = _clamp_score(1 - min(freshness_days, 21.0) / 21.0)
        popularity_score = _clamp_score(
            (log1p(max(int(post.view_count or 0), 0)) / 6.4)
            + (log1p(max(int(post.like_count or 0), 0)) / 4.6)
            + (log1p(max(int(post.comment_count or 0), 0)) / 4.2)
        )
        keyword_score = _resource_keyword_bonus(post=post, author=author, keyword=safe_keyword)

        if safe_sort == "popular":
            score = (
                0.40 * popularity_score
                + 0.18 * float(same_industry)
                + 0.10 * float(same_city)
                + 0.14 * freshness_score
                + 0.08 * float(author_verified)
                + pinned_bonus
                + keyword_score
            )
        else:
            score = (
                0.34 * freshness_score
                + 0.20 * popularity_score
                + 0.18 * float(same_industry)
                + 0.10 * float(same_city)
                + 0.08 * float(author_verified)
                + pinned_bonus
                + keyword_score
            )

        scored_rows.append(
            (
                float(score),
                (
                    post,
                    author,
                    same_industry,
                    same_city,
                    author_verified,
                ),
            )
        )

    if safe_sort == "popular":
        scored_rows.sort(
            key=lambda item: (
                not bool(item[1][0].is_pinned),
                -_datetime_timestamp(item[1][0].pinned_at),
                -item[0],
                -int(item[1][0].like_count or 0),
                -int(item[1][0].view_count or 0),
                -int(item[1][0].comment_count or 0),
                -_datetime_timestamp(item[1][0].created_at),
                -int(item[1][0].id or 0),
            )
        )
    else:
        scored_rows.sort(
            key=lambda item: (
                not bool(item[1][0].is_pinned),
                -_datetime_timestamp(item[1][0].pinned_at),
                -item[0],
                -_datetime_timestamp(item[1][0].created_at),
                -int(item[1][0].view_count or 0),
                -int(item[1][0].like_count or 0),
                -int(item[1][0].id or 0),
            )
        )

    scored_rows = _prioritize_fresh_post_rows(
        rows=scored_rows,
        excluded_post_codes=excluded_post_code_set if offset <= 0 else set(),
        window_size=min(max(safe_limit, 10), len(scored_rows)),
    )
    scored_rows = _shuffle_resource_rows(
        rows=scored_rows,
        viewer_user_pk=int(viewer_user_pk),
        request_salt=active_request_id,
        window_size=min(max(safe_limit * 2, 10), len(scored_rows)),
    )

    total = len(scored_rows)
    has_more = total > (offset + safe_limit)
    page_rows = scored_rows[offset : offset + safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    post_ids = [int(post.id) for _, (post, _, _, _, _) in page_rows]
    liked_set: set[int] = set()
    if post_ids:
        liked_rows = db.execute(
            select(ResourcePostLike.post_pk).where(
                and_(
                    ResourcePostLike.user_pk == int(viewer_user_pk),
                    ResourcePostLike.post_pk.in_(post_ids),
                )
            )
        ).all()
        liked_set = {int(item[0]) for item in liked_rows}

    items = [
        _serialize_post(
            post=post,
            author=author,
            liked=(int(post.id) in liked_set),
            viewer_user_pk=viewer_user_pk,
        )
        for _, (post, author, _, _, _) in page_rows
    ]
    return {
        "request_id": active_request_id,
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def create_resource_post(
    db: Session,
    *,
    author: User,
    mode: str,
    title: str,
    description: str,
    industry_label: str | None,
    images: list[str],
    sync_circle_codes: list[str] | None = None,
) -> dict[str, Any]:
    safe_mode = str(mode or "").strip().lower()
    if safe_mode not in SUPPORTED_POST_MODES:
        safe_mode = "cooperate"

    safe_title = str(title or "").strip()
    safe_description = str(description or "").strip()
    if not safe_title:
        raise BusinessException(message="标题不能为空", code=5452, status_code=400)
    if len(safe_title) > 120:
        raise BusinessException(message="标题不能超过120字", code=5453, status_code=400)
    if not safe_description:
        raise BusinessException(message="内容不能为空", code=5454, status_code=400)

    safe_industry = str(industry_label or "").strip()[:64] or str(author.industry_label or "").strip()[:64]
    post = ResourcePost(
        post_code=_generate_post_code(db=db),
        author_user_pk=int(author.id),
        mode=safe_mode,
        industry_label=safe_industry or None,
        title=safe_title,
        description=safe_description,
        images_json=_build_images_json(images=images),
        view_count=0,
        like_count=0,
        comment_count=0,
        status="active",
        is_pinned=False,
        pinned_at=None,
    )
    db.add(post)
    db.flush()
    circle_syncs = _sync_post_to_circles(
        db=db,
        post=post,
        author=author,
        sync_circle_codes=sync_circle_codes,
    )
    db.commit()
    db.refresh(post)
    try:
        grant_publish_resource_points(
            db=db,
            user_pk=int(author.id),
            post_code=str(post.post_code or ""),
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning(f"Failed to grant publish resource points. user_pk={author.id}, post_pk={post.id}, error={exc}")
    return _serialize_post(
        post=post,
        author=author,
        liked=False,
        viewer_user_pk=int(author.id),
        circle_syncs=circle_syncs,
    )


def update_resource_post(
    db: Session,
    *,
    viewer_user_pk: int,
    post_code: str,
    mode: str,
    title: str,
    description: str,
    industry_label: str | None,
    images: list[str],
    sync_circle_codes: list[str] | None = None,
) -> dict[str, Any]:
    post, author = _resolve_post_with_author(db=db, post_code=post_code)
    _assert_manage_author(post=post, viewer_user_pk=viewer_user_pk)

    safe_mode = str(mode or "").strip().lower()
    if safe_mode not in SUPPORTED_POST_MODES:
        safe_mode = "cooperate"
    safe_title = str(title or "").strip()
    safe_description = str(description or "").strip()
    if not safe_title:
        raise BusinessException(message="标题不能为空", code=5452, status_code=400)
    if len(safe_title) > 120:
        raise BusinessException(message="标题不能超过120字", code=5453, status_code=400)
    if not safe_description:
        raise BusinessException(message="内容不能为空", code=5454, status_code=400)

    post.mode = safe_mode
    post.title = safe_title
    post.description = safe_description
    post.industry_label = str(industry_label or "").strip()[:64] or None
    post.images_json = _build_images_json(images=images)
    circle_syncs = _sync_post_to_circles(
        db=db,
        post=post,
        author=author,
        sync_circle_codes=sync_circle_codes,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize_post(
        post=post,
        author=author,
        liked=False,
        viewer_user_pk=viewer_user_pk,
        circle_syncs=circle_syncs,
    )


def get_resource_post_detail(db: Session, *, viewer_user_pk: int, post_code: str) -> dict[str, Any]:
    post, author = _resolve_post_with_author(db=db, post_code=post_code)

    is_author = int(post.author_user_pk) == int(viewer_user_pk)
    if str(post.status or "") == "deleted":
        raise BusinessException(message="资源不存在", code=5456, status_code=404)
    if str(post.status or "") != "active" and not is_author:
        raise BusinessException(message="资源已下架", code=5459, status_code=404)

    liked = (
        db.execute(
            select(ResourcePostLike.id).where(
                and_(
                    ResourcePostLike.post_pk == int(post.id),
                    ResourcePostLike.user_pk == int(viewer_user_pk),
                )
            )
        ).scalar_one_or_none()
        is not None
    )
    circle_syncs = None
    if is_author:
        circle_syncs = [
            _serialize_circle_sync(sync, circle=circle)
            for sync, circle in _load_post_circle_sync_rows(db=db, post_pk=int(post.id))
            if _normalize_text(sync.status) != "cancelled"
        ]
    return _serialize_post(
        post=post,
        author=author,
        liked=liked,
        viewer_user_pk=viewer_user_pk,
        circle_syncs=circle_syncs,
    )


def increase_resource_post_view(db: Session, *, post_code: str, viewer_user_pk: int) -> dict[str, Any]:
    post, _ = _resolve_post_with_author(db=db, post_code=post_code)
    if str(post.status or "") == "deleted":
        raise BusinessException(message="资源不存在", code=5456, status_code=404)
    if str(post.status or "") != "active" and int(post.author_user_pk) != int(viewer_user_pk):
        raise BusinessException(message="资源已下架", code=5459, status_code=404)
    post.view_count = int(post.view_count or 0) + 1
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "post_code": str(post.post_code),
        "view_count": int(post.view_count or 0),
    }


def set_resource_post_like(
    db: Session,
    *,
    viewer_user_pk: int,
    post_code: str,
    liked: bool,
) -> dict[str, Any]:
    post, _ = _resolve_post_with_author(db=db, post_code=post_code)
    if str(post.status or "") != "active":
        raise BusinessException(message="仅可对上架资源点赞", code=5460, status_code=400)

    row = db.execute(
        select(ResourcePostLike).where(
            and_(
                ResourcePostLike.post_pk == int(post.id),
                ResourcePostLike.user_pk == int(viewer_user_pk),
            )
        )
    ).scalar_one_or_none()

    if liked:
        if row is None:
            row = ResourcePostLike(
                post_pk=int(post.id),
                user_pk=int(viewer_user_pk),
            )
            db.add(row)
            post.like_count = int(post.like_count or 0) + 1
            db.add(post)
            db.commit()
            db.refresh(post)
    else:
        if row is not None:
            db.delete(row)
            post.like_count = max(int(post.like_count or 0) - 1, 0)
            db.add(post)
            db.commit()
            db.refresh(post)

    return {
        "post_code": str(post.post_code),
        "liked": bool(liked),
        "like_count": int(post.like_count or 0),
    }


def list_my_resource_posts(
    db: Session,
    *,
    viewer_user_pk: int,
    status: str | None,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)
    safe_status = str(status or "").strip().lower()

    where_conditions = [
        ResourcePost.author_user_pk == int(viewer_user_pk),
        ResourcePost.status != "deleted",
    ]
    if safe_status in SUPPORTED_MANAGE_STATUS:
        where_conditions.append(ResourcePost.status == safe_status)

    rows = db.execute(
        select(ResourcePost, User)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(*where_conditions)
        .order_by(
            ResourcePost.is_pinned.desc(),
            ResourcePost.pinned_at.desc(),
            ResourcePost.created_at.desc(),
            ResourcePost.id.desc(),
        )
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()

    total = (
        db.execute(
            select(func.count())
            .select_from(ResourcePost)
            .where(*where_conditions)
        ).scalar_one()
        or 0
    )

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    items = [
        _serialize_post(
            post=post,
            author=author,
            liked=False,
            viewer_user_pk=viewer_user_pk,
        )
        for post, author in rows
    ]
    return {
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def list_user_resource_posts(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_pk: int,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    where_conditions = [
        ResourcePost.author_user_pk == int(target_user_pk),
        ResourcePost.status == "active",
    ]

    rows = db.execute(
        select(ResourcePost, User)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(*where_conditions)
        .order_by(
            ResourcePost.is_pinned.desc(),
            ResourcePost.pinned_at.desc(),
            ResourcePost.created_at.desc(),
            ResourcePost.id.desc(),
        )
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()

    total = (
        db.execute(
            select(func.count())
            .select_from(ResourcePost)
            .where(*where_conditions)
        ).scalar_one()
        or 0
    )

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    post_ids = [int(post.id) for post, _ in rows]
    liked_set: set[int] = set()
    if post_ids:
        liked_rows = db.execute(
            select(ResourcePostLike.post_pk).where(
                and_(
                    ResourcePostLike.user_pk == int(viewer_user_pk),
                    ResourcePostLike.post_pk.in_(post_ids),
                )
            )
        ).all()
        liked_set = {int(item[0]) for item in liked_rows}

    items = [
        _serialize_post(
            post=post,
            author=author,
            liked=(int(post.id) in liked_set),
            viewer_user_pk=viewer_user_pk,
        )
        for post, author in rows
    ]

    return {
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def list_circle_resource_posts(
    db: Session,
    *,
    viewer_user_pk: int,
    circle_code: str,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    safe_circle_code = _normalize_text(circle_code).upper()
    if not safe_circle_code:
        raise BusinessException(message="圈子编号不能为空", code=5467, status_code=400)
    circle = db.execute(
        select(Circle).where(Circle.circle_code == safe_circle_code, Circle.status == "active")
    ).scalar_one_or_none()
    if circle is None:
        raise BusinessException(message="圈子不存在", code=4043, status_code=404)

    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    rows = db.execute(
        select(ResourcePostCircleSync, ResourcePost, User)
        .join(ResourcePost, ResourcePost.id == ResourcePostCircleSync.post_pk)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(
            ResourcePostCircleSync.circle_code == safe_circle_code,
            ResourcePostCircleSync.status == "approved",
            ResourcePost.status == "active",
            User.is_active.is_(True),
        )
        .order_by(
            ResourcePostCircleSync.reviewed_at.desc(),
            ResourcePost.created_at.desc(),
            ResourcePost.id.desc(),
        )
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()

    total = (
        db.execute(
            select(func.count())
            .select_from(ResourcePostCircleSync)
            .join(ResourcePost, ResourcePost.id == ResourcePostCircleSync.post_pk)
            .join(User, User.id == ResourcePost.author_user_pk)
            .where(
                ResourcePostCircleSync.circle_code == safe_circle_code,
                ResourcePostCircleSync.status == "approved",
                ResourcePost.status == "active",
                User.is_active.is_(True),
            )
        ).scalar_one()
        or 0
    )

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    post_ids = [int(post.id) for _, post, _ in rows]
    liked_set: set[int] = set()
    if post_ids:
        liked_rows = db.execute(
            select(ResourcePostLike.post_pk).where(
                and_(
                    ResourcePostLike.user_pk == int(viewer_user_pk),
                    ResourcePostLike.post_pk.in_(post_ids),
                )
            )
        ).all()
        liked_set = {int(item[0]) for item in liked_rows}

    items = [
        _serialize_post(
            post=post,
            author=author,
            liked=(int(post.id) in liked_set),
            viewer_user_pk=viewer_user_pk,
            circle_syncs=[
                {
                    "id": int(sync.id),
                    "circle_code": safe_circle_code,
                    "status": "approved",
                    "created_at": sync.created_at.isoformat() if sync.created_at else None,
                    "reviewed_at": sync.reviewed_at.isoformat() if sync.reviewed_at else None,
                    "reject_reason": "",
                    "circle_name": "",
                }
            ],
        )
        for sync, post, author in rows
    ]
    return {
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def list_pending_circle_post_syncs(
    db: Session,
    *,
    circle_code: str,
    owner_user_pk: int,
) -> list[dict[str, Any]]:
    safe_circle_code = _normalize_text(circle_code).upper()
    if not safe_circle_code:
        raise BusinessException(message="圈子编号不能为空", code=5467, status_code=400)

    circle = db.execute(
        select(Circle).where(Circle.circle_code == safe_circle_code, Circle.status == "active")
    ).scalar_one_or_none()
    if circle is None:
        raise BusinessException(message="圈子不存在", code=4043, status_code=404)
    if int(circle.owner_user_pk) != int(owner_user_pk):
        raise BusinessException(message="仅圈主可查看同步审核", code=5468, status_code=403)

    rows = db.execute(
        select(ResourcePostCircleSync, ResourcePost, User)
        .join(ResourcePost, ResourcePost.id == ResourcePostCircleSync.post_pk)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(
            ResourcePostCircleSync.circle_code == safe_circle_code,
            ResourcePostCircleSync.status == "pending",
            ResourcePost.status != "deleted",
        )
        .order_by(ResourcePostCircleSync.created_at.desc(), ResourcePostCircleSync.id.desc())
    ).all()

    return [
        {
            "sync_id": int(sync.id),
            "post_code": _normalize_text(post.post_code),
            "mode": _normalize_text(post.mode) or "cooperate",
            "industry_label": _normalize_text(post.industry_label),
            "title": _normalize_text(post.title),
            "description": _normalize_text(post.description),
            "images": _parse_images(post.images_json),
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "requested_at": sync.created_at.isoformat() if sync.created_at else None,
            "author": {
                "user_id": _normalize_text(author.user_id),
                "nickname": _normalize_text(author.nickname) or "未命名用户",
                "avatar_url": _normalize_text(author.avatar_url) or "/static/logo.png",
                "company_name": _normalize_text(author.company_name),
                "job_title": _normalize_text(author.job_title),
                "industry_label": _normalize_text(author.industry_label),
                "is_verified": bool(author.is_verified),
            },
        }
        for sync, post, author in rows
    ]


def review_circle_post_sync(
    db: Session,
    *,
    circle_code: str,
    sync_id: int,
    owner_user_pk: int,
    action: str,
    reject_reason: str | None,
) -> dict[str, Any]:
    safe_circle_code = _normalize_text(circle_code).upper()
    if not safe_circle_code:
        raise BusinessException(message="圈子编号不能为空", code=5467, status_code=400)

    circle = db.execute(
        select(Circle).where(Circle.circle_code == safe_circle_code, Circle.status == "active")
    ).scalar_one_or_none()
    if circle is None:
        raise BusinessException(message="圈子不存在", code=4043, status_code=404)
    if int(circle.owner_user_pk) != int(owner_user_pk):
        raise BusinessException(message="仅圈主可审核同步资源", code=5469, status_code=403)

    sync = db.execute(
        select(ResourcePostCircleSync).where(
            ResourcePostCircleSync.id == int(sync_id),
            ResourcePostCircleSync.circle_code == safe_circle_code,
        )
    ).scalar_one_or_none()
    if sync is None:
        raise BusinessException(message="同步申请不存在", code=5470, status_code=404)
    if _normalize_text(sync.status) != "pending":
        raise BusinessException(message="该同步申请已处理", code=5471, status_code=400)

    safe_action = _normalize_lower(action)
    if safe_action not in {"approve", "reject"}:
        raise BusinessException(message="仅支持 approve/reject", code=5472, status_code=400)

    sync.status = "approved" if safe_action == "approve" else "rejected"
    sync.reviewed_by_user_pk = int(owner_user_pk)
    sync.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    sync.reject_reason = _normalize_text(reject_reason)[:255] if safe_action == "reject" else None
    db.add(sync)
    _refresh_circle_post_counts(db=db, circle_codes={safe_circle_code})
    db.commit()
    db.refresh(sync)
    return _serialize_circle_sync(sync, circle=circle)


def set_resource_post_status(
    db: Session,
    *,
    viewer_user_pk: int,
    post_code: str,
    status: str,
) -> dict[str, Any]:
    post, author = _resolve_post_with_author(db=db, post_code=post_code)
    _assert_manage_author(post=post, viewer_user_pk=viewer_user_pk)
    related_circle_codes = _get_related_circle_codes(db=db, post_pk=int(post.id))

    safe_status = str(status or "").strip().lower()
    if safe_status not in SUPPORTED_MANAGE_STATUS:
        raise BusinessException(message="状态仅支持 active/offline", code=5461, status_code=400)

    post.status = safe_status
    if safe_status != "active":
        post.is_pinned = False
        post.pinned_at = None
    db.add(post)
    _refresh_circle_post_counts(db=db, circle_codes=related_circle_codes)
    db.commit()
    db.refresh(post)
    return _serialize_post(post=post, author=author, liked=False, viewer_user_pk=viewer_user_pk)


def set_resource_post_pin(
    db: Session,
    *,
    viewer_user_pk: int,
    post_code: str,
    pinned: bool,
) -> dict[str, Any]:
    post, author = _resolve_post_with_author(db=db, post_code=post_code)
    _assert_manage_author(post=post, viewer_user_pk=viewer_user_pk)
    if str(post.status or "") != "active" and pinned:
        raise BusinessException(message="下架资源不能置顶", code=5462, status_code=400)

    post.is_pinned = bool(pinned)
    post.pinned_at = datetime.now(UTC).replace(tzinfo=None) if post.is_pinned else None
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize_post(post=post, author=author, liked=False, viewer_user_pk=viewer_user_pk)


def delete_resource_post(db: Session, *, viewer_user_pk: int, post_code: str) -> dict[str, Any]:
    post, _ = _resolve_post_with_author(db=db, post_code=post_code)
    _assert_manage_author(post=post, viewer_user_pk=viewer_user_pk)
    related_circle_codes = _get_related_circle_codes(db=db, post_pk=int(post.id))
    post.status = "deleted"
    post.is_pinned = False
    post.pinned_at = None
    db.add(post)
    _refresh_circle_post_counts(db=db, circle_codes=related_circle_codes)
    db.commit()
    return {
        "post_code": str(post.post_code),
        "deleted": True,
    }
