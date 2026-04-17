from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from functools import wraps
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.crud import ensure_user_wallet, get_circle_by_code, get_user_by_id
from app.models.circle import Circle
from app.models.content_review import ContentReview
from app.models.resource_post import ResourcePost
from app.models.user import User
from app.points import grant_profile_completion_points
from app.post.service import create_resource_post, update_resource_post
from app.schemas.review import (
    AdminContentReviewListData,
    AdminContentReviewListItem,
)

REVIEW_TYPE_PROFILE = "profile"
REVIEW_TYPE_CIRCLE = "circle"
REVIEW_TYPE_POST = "post"

REVIEW_ACTION_CREATE = "create"
REVIEW_ACTION_UPDATE = "update"

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUS_AUTO_APPROVED = "auto_approved"

TRIGGER_REASON_RISK = "risk_keywords"
TRIGGER_REASON_MONTHLY_LIMIT = "monthly_limit"

MONTHLY_FREE_CHANGE_LIMIT = 2
CHANGE_REVIEW_FEE = Decimal("9.99")

RISK_KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "反国家": (
        "推翻国家",
        "颠覆国家",
        "分裂国家",
        "反党",
        "反政府",
        "反国家",
        "台独",
        "港独",
        "疆独",
    ),
    "反社会": (
        "报复社会",
        "无差别伤人",
        "炸学校",
        "炸地铁",
        "教人自杀",
        "教人犯罪",
        "恐怖袭击",
    ),
    "男女对立": (
        "挑起男女对立",
        "厌女",
        "厌男",
        "仇女",
        "仇男",
        "拳师",
        "集美都",
        "男人都该",
        "女人都该",
    ),
    "低劣恶俗": (
        "约炮",
        "招嫖",
        "援交",
        "黄色视频",
        "成人色情网",
        "裸聊",
        "下流",
        "低俗",
        "恶俗",
        "擦边",
    ),
}


def _is_missing_content_reviews_table(exc: ProgrammingError) -> bool:
    error_code = None
    if getattr(exc, "orig", None) is not None:
        orig_args = getattr(exc.orig, "args", ())
        if orig_args:
            error_code = orig_args[0]
    if error_code != 1146:
        return False
    return "content_reviews" in str(exc).lower()


def _extract_session(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Session | None:
    db = kwargs.get("db")
    if isinstance(db, Session):
        return db
    for arg in args:
        if isinstance(arg, Session):
            return arg
    return None


def _raise_review_storage_not_ready(exc: ProgrammingError) -> None:
    raise BusinessException(
        message="审核功能尚未初始化，请先执行数据库迁移后再使用",
        code=5717,
        status_code=503,
    ) from exc


def _guard_content_review_storage(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProgrammingError as exc:
            if not _is_missing_content_reviews_table(exc):
                raise
            db = _extract_session(args, kwargs)
            if db is not None:
                db.rollback()
            _raise_review_storage_not_ready(exc)

    return wrapper


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_lower(value: str | None) -> str:
    return _normalize_text(value).lower()


def _json_load_dict(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _json_load_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item or "").strip()]


def _json_dump(value: Any) -> str | None:
    if value in (None, "", [], {}):
        return None
    return json.dumps(value, ensure_ascii=False)


def _month_range(now: datetime | None = None) -> tuple[datetime, datetime]:
    safe_now = now or _utc_now()
    start = safe_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _collect_risk_tags(*texts: str | None) -> list[str]:
    merged = "\n".join(_normalize_lower(item) for item in texts if _normalize_text(item))
    if not merged:
        return []

    risk_tags: list[str] = []
    for tag, keywords in RISK_KEYWORD_GROUPS.items():
        if any(_normalize_lower(keyword) in merged for keyword in keywords):
            risk_tags.append(tag)
    return risk_tags


def _profile_current_payload(user: User, fields: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_name in fields.keys():
        result[field_name] = getattr(user, field_name)
    return result


def _circle_current_payload(circle: Circle, fields: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_name in fields.keys():
        result[field_name] = getattr(circle, field_name)
    return result


def _post_current_payload(post: ResourcePost) -> dict[str, Any]:
    images = _json_load_list(post.images_json)
    return {
        "mode": str(post.mode or "").strip(),
        "title": str(post.title or "").strip(),
        "description": str(post.description or "").strip(),
        "industry_label": str(post.industry_label or "").strip(),
        "images": images,
    }


def _count_monthly_submissions(
    db: Session,
    *,
    review_type: str,
    submitter_user_pk: int,
    target_circle_code: str | None = None,
) -> int:
    month_start, month_end = _month_range()
    stmt = select(func.count(ContentReview.id)).where(
        ContentReview.review_type == review_type,
        ContentReview.submitter_user_pk == int(submitter_user_pk),
        ContentReview.created_at >= month_start,
        ContentReview.created_at < month_end,
    )
    if target_circle_code:
        stmt = stmt.where(ContentReview.target_circle_code == _normalize_text(target_circle_code))
    value = db.execute(stmt).scalar_one_or_none()
    return int(value or 0)


def _find_pending_review(
    db: Session,
    *,
    review_type: str,
    submitter_user_pk: int,
    target_circle_code: str | None = None,
    target_post_code: str | None = None,
) -> ContentReview | None:
    stmt = select(ContentReview).where(
        ContentReview.review_type == review_type,
        ContentReview.submitter_user_pk == int(submitter_user_pk),
        ContentReview.status == REVIEW_STATUS_PENDING,
    )
    if target_circle_code is not None:
        stmt = stmt.where(ContentReview.target_circle_code == _normalize_text(target_circle_code))
    if target_post_code is not None:
        stmt = stmt.where(ContentReview.target_post_code == _normalize_text(target_post_code).upper())
    return db.execute(stmt.order_by(ContentReview.id.desc()).limit(1)).scalar_one_or_none()


def _ensure_wallet_fee_paid(db: Session, *, user: User, amount: Decimal) -> None:
    wallet = ensure_user_wallet(db=db, user_pk=int(user.id), default_balance=user.balance or 0)
    wallet_balance = Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))
    if wallet_balance < amount:
        raise BusinessException(
            message=f"本月已超过免费修改次数，需支付审核费 ¥{amount:.2f}，请先充值钱包余额",
            code=5701,
            status_code=400,
            data={
                "required_amount": float(amount),
                "wallet_balance": float(wallet_balance),
            },
        )
    wallet.balance = (wallet_balance - amount).quantize(Decimal("0.01"))
    db.add(wallet)


def _build_review_meta(review: ContentReview, risk_tags: list[str]) -> dict[str, Any]:
    return {
        "review_id": int(review.id),
        "review_type": str(review.review_type or ""),
        "review_status": str(review.status or ""),
        "review_required": str(review.status or "") == REVIEW_STATUS_PENDING,
        "fee_paid": bool(review.fee_paid),
        "fee_amount": float(Decimal(str(review.review_fee_amount or 0)).quantize(Decimal("0.01"))),
        "risk_tags": risk_tags,
        "trigger_reason": str(review.trigger_reason or "").strip() or None,
    }


@_guard_content_review_storage
def submit_profile_update_review(
    db: Session,
    *,
    user: User,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise BusinessException(message="没有可更新的字段", code=4222, status_code=400)
    if _find_pending_review(
        db=db,
        review_type=REVIEW_TYPE_PROFILE,
        submitter_user_pk=int(user.id),
    ):
        raise BusinessException(message="当前有个人资料审核中的申请，请先等待处理结果", code=5702, status_code=400)

    monthly_count = _count_monthly_submissions(
        db=db,
        review_type=REVIEW_TYPE_PROFILE,
        submitter_user_pk=int(user.id),
    )
    over_limit = monthly_count >= MONTHLY_FREE_CHANGE_LIMIT
    current_payload = _profile_current_payload(user, updates)
    risk_tags = _collect_risk_tags(
        updates.get("nickname"),
        updates.get("intro"),
        updates.get("industry_label"),
        updates.get("company_name"),
        updates.get("job_title"),
        updates.get("city_name"),
    )
    review_required = over_limit or bool(risk_tags)
    now = _utc_now()
    fee_amount = CHANGE_REVIEW_FEE if over_limit else Decimal("0.00")

    review = ContentReview(
        review_type=REVIEW_TYPE_PROFILE,
        action_type=REVIEW_ACTION_UPDATE,
        status=REVIEW_STATUS_PENDING if review_required else REVIEW_STATUS_AUTO_APPROVED,
        submitter_user_pk=int(user.id),
        target_user_pk=int(user.id),
        review_fee_amount=fee_amount,
        fee_paid=bool(over_limit),
        trigger_reason=TRIGGER_REASON_MONTHLY_LIMIT if over_limit else (TRIGGER_REASON_RISK if risk_tags else None),
        risk_tags_json=_json_dump(risk_tags),
        submit_payload_json=_json_dump(updates),
        current_payload_json=_json_dump(current_payload),
        reviewed_at=None if review_required else now,
    )

    if over_limit:
        _ensure_wallet_fee_paid(db=db, user=user, amount=CHANGE_REVIEW_FEE)

    if not review_required:
        for field_name, field_value in updates.items():
            setattr(user, field_name, field_value)
        db.add(user)

    db.add(review)
    db.commit()
    db.refresh(review)
    if not review_required:
        db.refresh(user)
        try:
            grant_profile_completion_points(db=db, user=user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning(f"Failed to grant profile completion points. user_pk={user.id}, error={exc}")

    return {
        "review": _build_review_meta(review, risk_tags),
    }


@_guard_content_review_storage
def submit_circle_update_review(
    db: Session,
    *,
    circle: Circle,
    owner: User,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if not updates:
        raise BusinessException(message="没有可更新的字段", code=5703, status_code=400)
    if _find_pending_review(
        db=db,
        review_type=REVIEW_TYPE_CIRCLE,
        submitter_user_pk=int(owner.id),
        target_circle_code=circle.circle_code,
    ):
        raise BusinessException(message="当前圈子已有审核中的资料变更，请先等待处理结果", code=5704, status_code=400)

    monthly_count = _count_monthly_submissions(
        db=db,
        review_type=REVIEW_TYPE_CIRCLE,
        submitter_user_pk=int(owner.id),
        target_circle_code=circle.circle_code,
    )
    over_limit = monthly_count >= MONTHLY_FREE_CHANGE_LIMIT
    current_payload = _circle_current_payload(circle, updates)
    risk_tags = _collect_risk_tags(
        updates.get("name"),
        updates.get("industry_label"),
        updates.get("description"),
        updates.get("rules_text"),
    )
    review_required = over_limit or bool(risk_tags)
    now = _utc_now()
    fee_amount = CHANGE_REVIEW_FEE if over_limit else Decimal("0.00")

    review = ContentReview(
        review_type=REVIEW_TYPE_CIRCLE,
        action_type=REVIEW_ACTION_UPDATE,
        status=REVIEW_STATUS_PENDING if review_required else REVIEW_STATUS_AUTO_APPROVED,
        submitter_user_pk=int(owner.id),
        target_circle_code=str(circle.circle_code or "").strip(),
        review_fee_amount=fee_amount,
        fee_paid=bool(over_limit),
        trigger_reason=TRIGGER_REASON_MONTHLY_LIMIT if over_limit else (TRIGGER_REASON_RISK if risk_tags else None),
        risk_tags_json=_json_dump(risk_tags),
        submit_payload_json=_json_dump(updates),
        current_payload_json=_json_dump(current_payload),
        reviewed_at=None if review_required else now,
    )

    if over_limit:
        _ensure_wallet_fee_paid(db=db, user=owner, amount=CHANGE_REVIEW_FEE)

    if not review_required:
        for field_name, field_value in updates.items():
            setattr(circle, field_name, field_value)
        db.add(circle)

    db.add(review)
    db.commit()
    db.refresh(review)
    if not review_required:
        db.refresh(circle)

    return {
        "review": _build_review_meta(review, risk_tags),
    }


@_guard_content_review_storage
def submit_post_review(
    db: Session,
    *,
    author: User,
    action_type: Literal["create", "update"],
    payload: dict[str, Any],
    target_post_code: str | None = None,
) -> dict[str, Any]:
    normalized_target_post_code = _normalize_text(target_post_code).upper() or None
    if action_type == REVIEW_ACTION_UPDATE and not normalized_target_post_code:
        raise BusinessException(message="资源编号不能为空", code=5705, status_code=400)
    if (
        action_type == REVIEW_ACTION_UPDATE
        and _find_pending_review(
            db=db,
            review_type=REVIEW_TYPE_POST,
            submitter_user_pk=int(author.id),
            target_post_code=normalized_target_post_code,
        )
    ):
        raise BusinessException(message="当前资源已有审核中的修改申请，请先等待处理结果", code=5706, status_code=400)

    risk_tags = _collect_risk_tags(
        payload.get("title"),
        payload.get("description"),
        payload.get("industry_label"),
    )
    if not risk_tags:
        return {
            "review_required": False,
            "review": None,
        }

    current_payload = None
    if action_type == REVIEW_ACTION_UPDATE and normalized_target_post_code:
        row = db.execute(
            select(ResourcePost).where(ResourcePost.post_code == normalized_target_post_code).limit(1)
        ).scalar_one_or_none()
        if row is not None:
            current_payload = _post_current_payload(row)

    review = ContentReview(
        review_type=REVIEW_TYPE_POST,
        action_type=action_type,
        status=REVIEW_STATUS_PENDING,
        submitter_user_pk=int(author.id),
        target_post_code=normalized_target_post_code,
        review_fee_amount=Decimal("0.00"),
        fee_paid=False,
        trigger_reason=TRIGGER_REASON_RISK,
        risk_tags_json=_json_dump(risk_tags),
        submit_payload_json=_json_dump(payload),
        current_payload_json=_json_dump(current_payload),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "review_required": True,
        "review": _build_review_meta(review, risk_tags),
    }


def _resolve_target_label(review: ContentReview, submit_payload: dict[str, Any] | None) -> str | None:
    payload = submit_payload or {}
    if review.review_type == REVIEW_TYPE_PROFILE:
        return _normalize_text(payload.get("nickname")) or "个人资料变更"
    if review.review_type == REVIEW_TYPE_CIRCLE:
        return _normalize_text(payload.get("name")) or _normalize_text(review.target_circle_code)
    if review.review_type == REVIEW_TYPE_POST:
        return _normalize_text(payload.get("title")) or _normalize_text(review.target_post_code)
    return None


def _build_admin_review_item(db: Session, review: ContentReview) -> AdminContentReviewListItem | None:
    submitter = get_user_by_id(db=db, user_id=int(review.submitter_user_pk))
    if submitter is None:
        return None

    submit_payload = _json_load_dict(review.submit_payload_json)
    current_payload = _json_load_dict(review.current_payload_json)
    risk_tags = _json_load_list(review.risk_tags_json)
    return AdminContentReviewListItem(
        id=int(review.id),
        review_type=str(review.review_type or ""),
        action_type=str(review.action_type or ""),
        status=str(review.status or ""),
        submitter_user_pk=int(submitter.id),
        submitter_user_id=str(submitter.user_id or "").strip(),
        submitter_nickname=str(submitter.nickname or "").strip(),
        target_user_pk=int(review.target_user_pk) if review.target_user_pk else None,
        target_circle_code=_normalize_text(review.target_circle_code) or None,
        target_post_code=_normalize_text(review.target_post_code) or None,
        target_label=_resolve_target_label(review, submit_payload),
        review_fee_amount=float(Decimal(str(review.review_fee_amount or 0)).quantize(Decimal("0.01"))),
        fee_paid=bool(review.fee_paid),
        trigger_reason=_normalize_text(review.trigger_reason) or None,
        risk_tags=risk_tags,
        reject_reason=_normalize_text(review.reject_reason) or None,
        submit_payload=submit_payload,
        current_payload=current_payload,
        created_at=review.created_at,
        reviewed_at=review.reviewed_at,
    )


@_guard_content_review_storage
def list_admin_content_reviews(
    db: Session,
    *,
    review_type: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> AdminContentReviewListData:
    safe_page = max(int(page or 1), 1)
    safe_page_size = min(max(int(page_size or 20), 1), 100)
    offset = (safe_page - 1) * safe_page_size

    where_conditions = []
    normalized_review_type = _normalize_text(review_type)
    normalized_status = _normalize_text(status)
    if normalized_review_type:
        where_conditions.append(ContentReview.review_type == normalized_review_type)
    if normalized_status:
        where_conditions.append(ContentReview.status == normalized_status)

    rows = db.execute(
        select(ContentReview)
        .where(*where_conditions)
        .order_by(ContentReview.created_at.desc(), ContentReview.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).scalars().all()
    total = int(
        db.execute(
            select(func.count(ContentReview.id)).where(*where_conditions)
        ).scalar_one()
        or 0
    )

    items = [item for row in rows if (item := _build_admin_review_item(db=db, review=row)) is not None]
    return AdminContentReviewListData(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


def _apply_profile_payload(user: User, payload: dict[str, Any]) -> None:
    for field_name, field_value in payload.items():
        setattr(user, field_name, field_value)


def _apply_circle_payload(circle: Circle, payload: dict[str, Any]) -> None:
    for field_name, field_value in payload.items():
        setattr(circle, field_name, field_value)


@_guard_content_review_storage
def review_content_submission(
    db: Session,
    *,
    review_id: int,
    action: Literal["approve", "reject"],
    reject_reason: str | None,
    admin_id: int,
) -> AdminContentReviewListItem:
    review = db.execute(
        select(ContentReview).where(ContentReview.id == int(review_id)).limit(1)
    ).scalar_one_or_none()
    if review is None:
        raise BusinessException(message="审核记录不存在", code=5707, status_code=404)
    if _normalize_text(review.status) != REVIEW_STATUS_PENDING:
        raise BusinessException(message="当前审核记录已处理，请勿重复操作", code=5708, status_code=400)

    normalized_reason = _normalize_text(reject_reason)[:255] if _normalize_text(reject_reason) else None
    if action == "reject" and not normalized_reason:
        raise BusinessException(message="驳回时必须填写驳回原因", code=5709, status_code=400)

    payload = _json_load_dict(review.submit_payload_json)
    if payload is None:
        raise BusinessException(message="审核记录缺少提交内容", code=5710, status_code=400)

    if action == "reject":
        review.status = REVIEW_STATUS_REJECTED
        review.reject_reason = normalized_reason
        review.reviewed_by_admin_id = int(admin_id)
        review.reviewed_at = _utc_now()
        db.add(review)
        db.commit()
        db.refresh(review)
        db.refresh(user)
        try:
            grant_profile_completion_points(db=db, user=user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning(f"Failed to grant profile completion points after review approve. user_pk={user.id}, error={exc}")
        item = _build_admin_review_item(db=db, review=review)
        if item is None:
            raise BusinessException(message="审核关联用户不存在", code=5711, status_code=404)
        return item

    if review.review_type == REVIEW_TYPE_PROFILE:
        user = get_user_by_id(db=db, user_id=int(review.target_user_pk or review.submitter_user_pk))
        if user is None:
            raise BusinessException(message="资料审核关联用户不存在", code=5712, status_code=404)
        _apply_profile_payload(user, payload)
        db.add(user)
        review.status = REVIEW_STATUS_APPROVED
        review.reject_reason = None
        review.reviewed_by_admin_id = int(admin_id)
        review.reviewed_at = _utc_now()
        db.add(review)
        db.commit()
        db.refresh(review)
    elif review.review_type == REVIEW_TYPE_CIRCLE:
        circle_code = _normalize_text(review.target_circle_code)
        circle = get_circle_by_code(db=db, circle_code=circle_code)
        if circle is None:
            raise BusinessException(message="圈子审核关联圈子不存在", code=5713, status_code=404)
        _apply_circle_payload(circle, payload)
        db.add(circle)
        review.status = REVIEW_STATUS_APPROVED
        review.reject_reason = None
        review.reviewed_by_admin_id = int(admin_id)
        review.reviewed_at = _utc_now()
        db.add(review)
        db.commit()
        db.refresh(review)
    elif review.review_type == REVIEW_TYPE_POST:
        submitter = get_user_by_id(db=db, user_id=int(review.submitter_user_pk))
        if submitter is None:
            raise BusinessException(message="资源审核关联用户不存在", code=5714, status_code=404)
        if _normalize_text(review.action_type) == REVIEW_ACTION_CREATE:
            created = create_resource_post(
                db=db,
                author=submitter,
                mode=str(payload.get("mode") or "").strip(),
                title=str(payload.get("title") or "").strip(),
                description=str(payload.get("description") or "").strip(),
                industry_label=str(payload.get("industry_label") or "").strip() or None,
                images=payload.get("images") if isinstance(payload.get("images"), list) else [],
            )
            review.target_post_code = _normalize_text(created.get("post_code"))
        else:
            target_post_code = _normalize_text(review.target_post_code)
            if not target_post_code:
                raise BusinessException(message="资源审核缺少目标资源编号", code=5715, status_code=400)
            update_resource_post(
                db=db,
                viewer_user_pk=int(submitter.id),
                post_code=target_post_code,
                mode=str(payload.get("mode") or "").strip(),
                title=str(payload.get("title") or "").strip(),
                description=str(payload.get("description") or "").strip(),
                industry_label=str(payload.get("industry_label") or "").strip() or None,
                images=payload.get("images") if isinstance(payload.get("images"), list) else [],
            )
        review.status = REVIEW_STATUS_APPROVED
        review.reject_reason = None
        review.reviewed_by_admin_id = int(admin_id)
        review.reviewed_at = _utc_now()
        db.add(review)
        db.commit()
        db.refresh(review)
    else:
        raise BusinessException(message="不支持的审核类型", code=5716, status_code=400)

    item = _build_admin_review_item(db=db, review=review)
    if item is None:
        raise BusinessException(message="审核关联用户不存在", code=5711, status_code=404)
    return item
