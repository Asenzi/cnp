from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.models.product_safety import ContentReport, ProductSafetyPunishment, ProductSafetyRetryTask, ProductSafetyReviewLog
from app.models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _risk_rank(level: str | None) -> int:
    try:
        return int(str(level or "L0").upper().replace("L", ""))
    except ValueError:
        return 0


def _set_min_risk(user: User, level: str) -> None:
    if _risk_rank(user.risk_level) < _risk_rank(level):
        user.risk_level = level


def log_review(
    db: Session,
    *,
    user: User | None,
    content_type: str,
    content_value: str | None,
    provider: str,
    provider_result: str,
    final_result: str,
    provider_request_id: str | None = None,
    risk_labels: list[str] | None = None,
    reject_reason: str | None = None,
) -> None:
    db.add(
        ProductSafetyReviewLog(
            user_pk=int(user.id) if user is not None else None,
            content_type=str(content_type or "")[:32],
            content_value=content_value,
            provider=str(provider or "local")[:32],
            provider_request_id=(provider_request_id or None),
            provider_result=str(provider_result or "")[:32],
            risk_labels_json=json.dumps(risk_labels or [], ensure_ascii=False) if risk_labels else None,
            final_result=str(final_result or "")[:32],
            reject_reason=(reject_reason or None),
        )
    )


def count_today_reviews(db: Session, *, user: User, content_type: str) -> int:
    today = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    return int(
        db.scalar(
            select(func.count(ProductSafetyReviewLog.id)).where(
                ProductSafetyReviewLog.user_pk == int(user.id),
                ProductSafetyReviewLog.content_type == content_type,
                ProductSafetyReviewLog.created_at >= today,
            )
        )
        or 0
    )


def enforce_profile_edit_allowed(db: Session, *, user: User, content_type: str) -> None:
    now = _now()
    if user.banned_at is not None:
        raise BusinessException(message="账号已被限制使用", code=4271, status_code=403)
    if user.profile_edit_blocked_until and user.profile_edit_blocked_until > now:
        raise BusinessException(message="由于近期资料修改异常，暂时无法修改", code=4272, status_code=403)

    protection_hours = max(int(settings.PRODUCT_SAFETY_NEW_USER_PROTECTION_HOURS or 0), 0)
    is_new_user = bool(user.created_at and user.created_at > now - timedelta(hours=protection_hours))
    if not is_new_user:
        return

    limit = 1 if content_type in {"avatar", "nickname", "intro"} else 3
    if count_today_reviews(db=db, user=user, content_type=content_type) >= limit:
        raise BusinessException(message="新用户资料修改过于频繁，请明天再试", code=4273, status_code=429)


def punish_user(
    db: Session,
    *,
    user: User,
    punishment_type: str,
    reason: str,
    duration_hours: int | None = None,
    source: str = "system",
) -> None:
    now = _now()
    ends_at = now + timedelta(hours=duration_hours) if duration_hours else None
    if punishment_type == "profile_edit_block":
        user.profile_edit_blocked_until = ends_at
        _set_min_risk(user, "L2")
    elif punishment_type == "mute":
        user.muted_until = ends_at
        _set_min_risk(user, "L3")
    elif punishment_type == "ban":
        user.banned_at = now
        user.is_active = False
        _set_min_risk(user, "L4")
    db.add(user)
    db.add(
        ProductSafetyPunishment(
            user_pk=int(user.id),
            punishment_type=punishment_type,
            reason=reason[:255],
            source=source[:32],
            starts_at=now,
            ends_at=ends_at,
        )
    )


def report_content(
    db: Session,
    *,
    reporter: User,
    target_user: User | None,
    target_type: str,
    target_id: str,
    reason: str | None,
) -> ContentReport:
    report = ContentReport(
        reporter_user_pk=int(reporter.id),
        target_user_pk=int(target_user.id) if target_user is not None else None,
        target_type=str(target_type or "")[:32],
        target_id=str(target_id or "")[:64],
        reason=str(reason or "").strip()[:255] or None,
    )
    db.add(report)
    if target_user is not None and int(target_user.id) != int(reporter.id):
        _set_min_risk(target_user, "L2")
        if target_type in {"user", "avatar", "profile"}:
            target_user.avatar_review_status = "pending"
        db.add(target_user)
    return report


def enqueue_retry(
    db: Session,
    *,
    user: User | None,
    content_type: str,
    content_value: str | None,
    error: str,
    delay_minutes: int = 5,
) -> None:
    db.add(
        ProductSafetyRetryTask(
            user_pk=int(user.id) if user is not None else None,
            content_type=str(content_type or "")[:32],
            content_value=content_value,
            status="pending",
            next_retry_at=_now() + timedelta(minutes=max(int(delay_minutes or 5), 1)),
            last_error=str(error or "")[:255],
        )
    )
