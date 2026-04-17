from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from math import log1p
from secrets import token_hex

from sqlalchemy.orm import Session

from app.crud import list_discover_circles, list_joined_circle_codes
from app.schemas.circle import CircleDiscoverItem, CircleDiscoverListData

SUPPORTED_TABS = {"recommend", "nearby", "latest"}


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


def _request_rotation_jitter(*, viewer_user_pk: int, circle_pk: int, request_salt: str) -> float:
    digest = hashlib.sha1(f"{viewer_user_pk}:{circle_pk}:{request_salt}".encode("utf-8")).hexdigest()
    raw_value = int(digest[:8], 16) / 0xFFFFFFFF
    return max(0.0, min(raw_value, 1.0))


def _keyword_bonus(circle, owner, keyword: str | None) -> float:
    normalized_keyword = _normalize_lower(keyword)
    if not normalized_keyword:
        return 0.0

    name = _normalize_lower(circle.name)
    industry = _normalize_lower(circle.industry_label)
    description = _normalize_lower(circle.description)
    owner_name = _normalize_lower(owner.nickname)
    owner_city = _normalize_lower(owner.city_name)

    score = 0.0
    if normalized_keyword and name == normalized_keyword:
        score += 0.35
    elif normalized_keyword and normalized_keyword in name:
        score += 0.28

    if normalized_keyword and normalized_keyword in industry:
        score += 0.18
    if normalized_keyword and normalized_keyword in description:
        score += 0.16
    if normalized_keyword and normalized_keyword in owner_name:
        score += 0.12
    if normalized_keyword and normalized_keyword in owner_city:
        score += 0.08

    return min(score, 0.45)


def _build_reason_tags(
    *,
    same_industry: bool,
    same_city: bool,
    owner_verified: bool,
    is_joined: bool,
    member_count: int,
    post_count: int,
) -> list[str]:
    tags: list[str] = []
    if same_industry:
        tags.append("行业匹配")
    if same_city:
        tags.append("同城圈子")
    if owner_verified:
        tags.append("圈主已认证")
    if member_count >= 20:
        tags.append("成员活跃")
    if post_count >= 5:
        tags.append("最近有内容")
    if is_joined:
        tags.append("已加入")
    return tags[:3]


def _shuffle_recommend_rows(
    *,
    rows: list[tuple[float, tuple]],
    viewer_user_pk: int,
    request_salt: str,
    window_size: int,
) -> list[tuple[float, tuple]]:
    if not request_salt or len(rows) <= 1:
        return rows

    safe_window_size = min(max(int(window_size or 0), 1), len(rows))
    head_rows = rows[:safe_window_size]
    tail_rows = rows[safe_window_size:]

    def shuffle_key(item: tuple[float, tuple]) -> float:
        circle = item[1][0]
        return _request_rotation_jitter(
            viewer_user_pk=int(viewer_user_pk),
            circle_pk=int(circle.id),
            request_salt=request_salt,
        )

    unjoined_head_rows = [row for row in head_rows if not bool(row[1][5])]
    joined_head_rows = [row for row in head_rows if bool(row[1][5])]

    shuffled_head_rows = sorted(unjoined_head_rows, key=shuffle_key, reverse=True) + sorted(
        joined_head_rows,
        key=shuffle_key,
        reverse=True,
    )
    return shuffled_head_rows + tail_rows


def _prioritize_fresh_rows(
    *,
    rows: list[tuple[float, tuple]],
    excluded_circle_codes: set[str],
    window_size: int,
) -> list[tuple[float, tuple]]:
    if not excluded_circle_codes or len(rows) <= 1:
        return rows

    fresh_rows = [
        row for row in rows
        if _normalize_text(row[1][0].circle_code) not in excluded_circle_codes
    ]
    repeat_rows = [
        row for row in rows
        if _normalize_text(row[1][0].circle_code) in excluded_circle_codes
    ]
    safe_window_size = min(max(int(window_size or 0), 1), len(rows))
    if len(fresh_rows) < safe_window_size:
        return rows
    return fresh_rows + repeat_rows


def list_circle_discover_recommendations(
    db: Session,
    *,
    viewer,
    tab: str,
    offset: int,
    limit: int,
    keyword: str | None = None,
    city_name: str | None = None,
    industry_label: str | None = None,
    request_id: str | None = None,
    exclude_circle_codes: list[str] | None = None,
) -> dict:
    normalized_tab = tab if tab in SUPPORTED_TABS else "recommend"
    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 1), 50)
    active_request_id = _normalize_text(request_id)
    if normalized_tab == "recommend" and not active_request_id:
        active_request_id = token_hex(8)
    excluded_circle_code_set = {
        _normalize_text(item)
        for item in (exclude_circle_codes or [])
        if _normalize_text(item)
    }
    effective_city_name = _normalize_text(city_name) or _normalize_text(viewer.city_name)
    viewer_industry = _normalize_lower(viewer.industry_label)
    viewer_city = _normalize_lower(effective_city_name)
    joined_circle_codes = list_joined_circle_codes(db=db, user_pk=int(viewer.id))
    # Determine parameters for fetching circles based on tab
    fetch_city_name = None
    fetch_order_by = "default"
    
    if normalized_tab == "nearby" and effective_city_name:
        fetch_city_name = effective_city_name
        fetch_order_by = "nearby"
    elif normalized_tab == "latest":
        fetch_order_by = "latest"
    
    rows = list_discover_circles(
        db=db, 
        keyword=keyword,
        city_name=fetch_city_name,
        industry_label=industry_label,
        order_by=fetch_order_by
    )

    now = datetime.now(UTC).replace(tzinfo=None)
    scored_rows: list[tuple[float, tuple]] = []

    for circle, owner in rows:
        member_count = int(circle.member_count or 0)
        post_count = int(circle.post_count or 0)
        created_days = _days_since(circle.created_at, now=now)
        active_days = _days_since(circle.last_active_at, now=now)
        popularity_score = _clamp_score((log1p(member_count) / 6.0) + (log1p(post_count) / 7.0))
        activity_score = _clamp_score((1 - min(active_days, 30.0) / 30.0) + min(post_count / 20.0, 0.25))
        freshness_score = _clamp_score(1 - min(created_days, 30.0) / 30.0)
        same_industry = bool(viewer_industry) and _normalize_lower(circle.industry_label) == viewer_industry
        same_city = bool(viewer_city) and _normalize_lower(owner.city_name) == viewer_city
        owner_verified = bool(owner.is_verified)
        is_joined = _normalize_text(circle.circle_code) in joined_circle_codes
        keyword_score = _keyword_bonus(circle, owner, keyword)
        joined_penalty = 0.38 if is_joined else 0.0

        if normalized_tab == "nearby":
            score = (
                0.45 * float(same_city)
                + 0.22 * activity_score
                + 0.14 * popularity_score
                + 0.10 * freshness_score
                + 0.09 * float(owner_verified)
                + keyword_score
                - joined_penalty
            )
        elif normalized_tab == "latest":
            score = (
                0.42 * freshness_score
                + 0.24 * activity_score
                + 0.16 * popularity_score
                + 0.10 * float(owner_verified)
                + 0.08 * float(same_city)
                + keyword_score
                - joined_penalty
            )
        else:
            score = (
                0.26 * float(same_industry)
                + 0.18 * float(same_city)
                + 0.22 * popularity_score
                + 0.18 * activity_score
                + 0.08 * freshness_score
                + 0.08 * float(owner_verified)
                + keyword_score
                - joined_penalty
            )

        scored_rows.append(
            (
                float(score),
                (
                    circle,
                    owner,
                    same_industry,
                    same_city,
                    owner_verified,
                    is_joined,
                    member_count,
                    post_count,
                ),
            )
        )

    # Sort based on tab
    if normalized_tab == "latest":
        # For latest tab, sort by creation date (newest first), then ensure unjoined circles first
        scored_rows.sort(
            key=lambda item: (
                item[1][5],  # is_joined: unjoined first (False < True)
                -(item[1][0].created_at or datetime.min).timestamp(),
                item[1][0].id,
            )
        )
    else:
        # For recommend and nearby tabs, use the existing scoring-based sort
        scored_rows.sort(
            key=lambda item: (
                item[1][5],  # is_joined: unjoined first
                -item[0],
                -int(item[1][0].post_count or 0),
                -int(item[1][0].member_count or 0),
                item[1][0].created_at or datetime.min,
                item[1][0].id,
            )
        )

    if normalized_tab == "recommend":
        scored_rows = _prioritize_fresh_rows(
            rows=scored_rows,
            excluded_circle_codes=excluded_circle_code_set,
            window_size=min(max(safe_limit, 10), len(scored_rows)),
        )

    if normalized_tab == "recommend" and active_request_id:
        scored_rows = _shuffle_recommend_rows(
            rows=scored_rows,
            viewer_user_pk=int(viewer.id),
            request_salt=active_request_id,
            window_size=min(max(safe_limit * 2, 10), len(scored_rows)),
        )

    total = len(scored_rows)
    page_rows = scored_rows[safe_offset : safe_offset + safe_limit]

    items = [
        CircleDiscoverItem(
            circle_code=_normalize_text(circle.circle_code),
            name=_normalize_text(circle.name),
            industry_label=_normalize_text(circle.industry_label),
            description=_normalize_text(circle.description),
            cover_url=_normalize_text(circle.cover_url),
            avatar_url=_normalize_text(circle.avatar_url or circle.cover_url),
            join_type=_normalize_text(circle.join_type) or "free",
            join_price=float(circle.join_price or 0),
            member_count=member_count,
            post_count=post_count,
            owner_user_id=_normalize_text(owner.user_id),
            owner_nickname=_normalize_text(owner.nickname),
            owner_avatar_url=_normalize_text(owner.avatar_url),
            owner_city_name=_normalize_text(owner.city_name) or None,
            owner_is_verified=owner_verified,
            is_joined=is_joined,
            reason_tags=_build_reason_tags(
                same_industry=same_industry,
                same_city=same_city,
                owner_verified=owner_verified,
                is_joined=is_joined,
                member_count=member_count,
                post_count=post_count,
            ),
            score=round(score, 4),
            last_active_at=circle.last_active_at,
            created_at=circle.created_at,
        ).model_dump(mode="json")
        for score, (circle, owner, same_industry, same_city, owner_verified, is_joined, member_count, post_count) in page_rows
    ]

    payload = CircleDiscoverListData(
        items=items,
        total=total,
        offset=safe_offset,
        limit=safe_limit,
        has_more=(safe_offset + len(items)) < total,
        tab=normalized_tab,
        city_name=effective_city_name or None,
        request_id=active_request_id or None,
    )
    return payload.model_dump(mode="json")
