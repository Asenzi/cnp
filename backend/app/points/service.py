from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import BusinessException
from app.crud import (
    ensure_user_points_account,
    get_sys_config_values,
    get_user_by_business_user_id,
    get_user_by_id,
    get_user_points_account,
    get_user_verification,
)
from app.models.member_order import MemberOrder
from app.models.sys_config import SysConfig
from app.models.user import User
from app.models.user_points_account import UserPointsAccount
from app.models.user_points_transaction import UserPointsTransaction
from app.verification.constants import VerificationStatus, VerificationType

POINTS_STATUS_NONE = "none"
POINTS_STATUS_RESERVED = "reserved"
POINTS_STATUS_SPENT = "spent"
POINTS_STATUS_RELEASED = "released"

TASK_DAILY_CHECK_IN = "daily_check_in"
TASK_PUBLISH_RESOURCE = "publish_resource"
TASK_COMPLETE_PROFILE = "complete_profile"
TASK_REAL_NAME_VERIFIED = "real_name_verified"
TASK_INVITE_FRIEND = "invite_friend"

POINTS_RESERVATION_EXPIRE_MINUTES = 30

PROFILE_COMPLETE_FIELDS = (
    "nickname",
    "industry_label",
    "job_title",
    "display_phone",
    "display_wechat",
    "city_name",
    "intro",
)

DEFAULT_TASK_RULES: dict[str, dict[str, Any]] = {
    TASK_DAILY_CHECK_IN: {
        "title": "每日签到",
        "amount": 10,
        "enabled": True,
        "description": "每日签到一次，可获得积分奖励",
        "action": "check_in",
    },
    TASK_PUBLISH_RESOURCE: {
        "title": "发布资源",
        "amount": 20,
        "enabled": True,
        "description": "每成功发布一条资源，可获得积分奖励",
        "action": "publish",
    },
    TASK_COMPLETE_PROFILE: {
        "title": "完善个人信息",
        "amount": 100,
        "enabled": True,
        "description": "首次完整填写个人资料，可获得积分奖励",
        "action": "profile",
    },
    TASK_REAL_NAME_VERIFIED: {
        "title": "身份认证",
        "amount": 200,
        "enabled": True,
        "description": "实名认证审核通过后，可获得积分奖励",
        "action": "verify",
    },
    TASK_INVITE_FRIEND: {
        "title": "邀请好友",
        "amount": 300,
        "enabled": True,
        "description": "每成功邀请一位新用户注册，可获得积分奖励",
        "action": "invite",
    },
}

DEFAULT_MEMBER_DISCOUNT_RULES: dict[str, dict[str, Any]] = {
    "yearly": {
        "enabled": True,
        "required_points": 5000,
        "discount_rate": Decimal("0.80"),
    },
    "quarterly": {
        "enabled": True,
        "required_points": 3000,
        "discount_rate": Decimal("0.85"),
    },
    "monthly": {
        "enabled": True,
        "required_points": 2000,
        "discount_rate": Decimal("0.90"),
    },
}


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_text(value: object) -> str:
    return str(value or "").strip()


def _normalize_positive_int(value: object, default: int = 0, *, min_value: int = 0, max_value: int = 10_000_000) -> int:
    try:
        parsed = int(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed < min_value:
        return min_value
    if parsed > max_value:
        return max_value
    return parsed


def _normalize_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "enabled", "active"}:
            return True
        if normalized in {"0", "false", "no", "off", "disabled", "inactive"}:
            return False
    return default


def _normalize_discount_rate(value: object, default: Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed <= 0 or parsed > 1:
        return default
    return parsed.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _money(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        parsed = Decimal("0.00")
    if parsed < 0:
        parsed = Decimal("0.00")
    return parsed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _discount_price(price: Decimal, rate: Decimal) -> Decimal:
    return (price * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _discount_text(rate: Decimal) -> str:
    fold = (rate * Decimal("10")).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP)
    return f"{fold}折"


def _task_config_key(task_key: str, field: str) -> str:
    return f"points.task.{task_key}.{field}"


def _discount_config_key(plan_id: str, field: str) -> str:
    return f"points.member_discount.{plan_id}.{field}"


def ensure_default_points_configs() -> None:
    default_rows: list[tuple[str, str, str]] = []
    for task_key, rule in DEFAULT_TASK_RULES.items():
        default_rows.append(
            (
                _task_config_key(task_key, "enabled"),
                "1" if rule["enabled"] else "0",
                f"{rule['title']}积分任务是否启用",
            )
        )
        default_rows.append(
            (
                _task_config_key(task_key, "amount"),
                str(int(rule["amount"])),
                f"{rule['title']}奖励积分值",
            )
        )

    for plan_id, rule in DEFAULT_MEMBER_DISCOUNT_RULES.items():
        default_rows.append(
            (
                _discount_config_key(plan_id, "enabled"),
                "1" if rule["enabled"] else "0",
                f"{plan_id}会员是否启用积分折扣",
            )
        )
        default_rows.append(
            (
                _discount_config_key(plan_id, "required_points"),
                str(int(rule["required_points"])),
                f"{plan_id}会员积分抵扣所需积分",
            )
        )
        default_rows.append(
            (
                _discount_config_key(plan_id, "discount_rate"),
                str(rule["discount_rate"]),
                f"{plan_id}会员积分抵扣折后系数",
            )
        )

    with SessionLocal() as db:
        existing_keys = {
            item[0]
            for item in db.execute(select(SysConfig.config_key).where(SysConfig.config_key.in_([row[0] for row in default_rows])))
        }
        changed = False
        for config_key, config_value, description in default_rows:
            if config_key in existing_keys:
                continue
            db.add(
                SysConfig(
                    config_key=config_key,
                    config_value=config_value,
                    config_group="points",
                    description=description,
                )
            )
            changed = True
        if changed:
            db.commit()


def _load_points_rule_values(db: Session) -> dict[str, str]:
    config_keys: set[str] = set()
    for task_key in DEFAULT_TASK_RULES:
        config_keys.add(_task_config_key(task_key, "enabled"))
        config_keys.add(_task_config_key(task_key, "amount"))
    for plan_id in DEFAULT_MEMBER_DISCOUNT_RULES:
        config_keys.add(_discount_config_key(plan_id, "enabled"))
        config_keys.add(_discount_config_key(plan_id, "required_points"))
        config_keys.add(_discount_config_key(plan_id, "discount_rate"))
    return get_sys_config_values(db=db, config_keys=config_keys)


def resolve_points_task_rules(db: Session) -> dict[str, dict[str, Any]]:
    config_values = _load_points_rule_values(db=db)
    resolved: dict[str, dict[str, Any]] = {}
    for task_key, default_rule in DEFAULT_TASK_RULES.items():
        resolved[task_key] = {
            **default_rule,
            "enabled": _normalize_bool(config_values.get(_task_config_key(task_key, "enabled")), bool(default_rule["enabled"])),
            "amount": _normalize_positive_int(
                config_values.get(_task_config_key(task_key, "amount")),
                int(default_rule["amount"]),
                min_value=0,
            ),
        }
    return resolved


def resolve_member_discount_rules(db: Session) -> dict[str, dict[str, Any]]:
    config_values = _load_points_rule_values(db=db)
    resolved: dict[str, dict[str, Any]] = {}
    for plan_id, default_rule in DEFAULT_MEMBER_DISCOUNT_RULES.items():
        rate = _normalize_discount_rate(
            config_values.get(_discount_config_key(plan_id, "discount_rate")),
            default_rule["discount_rate"],
        )
        resolved[plan_id] = {
            "enabled": _normalize_bool(
                config_values.get(_discount_config_key(plan_id, "enabled")),
                bool(default_rule["enabled"]),
            ),
            "required_points": _normalize_positive_int(
                config_values.get(_discount_config_key(plan_id, "required_points")),
                int(default_rule["required_points"]),
                min_value=0,
            ),
            "discount_rate": rate,
            "discount_text": _discount_text(rate),
        }
    return resolved


def _get_points_account(db: Session, *, user_pk: int) -> UserPointsAccount:
    account = get_user_points_account(db=db, user_pk=int(user_pk))
    if account is not None:
        return account
    return ensure_user_points_account(db=db, user_pk=int(user_pk), default_balance=0)


def _get_points_transaction(
    db: Session,
    *,
    user_pk: int,
    biz_type: str,
    biz_key: str,
) -> UserPointsTransaction | None:
    stmt = select(UserPointsTransaction).where(
        UserPointsTransaction.user_pk == int(user_pk),
        UserPointsTransaction.biz_type == _normalize_text(biz_type),
        UserPointsTransaction.biz_key == _normalize_text(biz_key),
    )
    return db.execute(stmt).scalar_one_or_none()


def _serialize_points_record(item: UserPointsTransaction) -> dict[str, Any]:
    meta = None
    if item.meta_json:
        try:
            parsed = json.loads(item.meta_json)
            meta = parsed if isinstance(parsed, dict) else None
        except (TypeError, ValueError):
            meta = None

    return {
        "id": int(item.id),
        "change_amount": int(item.change_amount or 0),
        "balance_after": int(item.balance_after or 0),
        "biz_type": _normalize_text(item.biz_type),
        "biz_key": _normalize_text(item.biz_key),
        "title": _normalize_text(item.title),
        "remark": _normalize_text(item.remark) or None,
        "meta": meta,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def list_user_points_records(
    db: Session,
    *,
    user_pk: int,
    cursor: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 20), 1), 50)
    stmt: Select[tuple[UserPointsTransaction]] = select(UserPointsTransaction).where(
        UserPointsTransaction.user_pk == int(user_pk)
    )
    normalized_cursor = _normalize_text(cursor)
    if normalized_cursor.isdigit():
        stmt = stmt.where(UserPointsTransaction.id < int(normalized_cursor))

    rows = db.execute(
        stmt.order_by(UserPointsTransaction.id.desc()).limit(safe_limit + 1)
    ).scalars().all()
    has_more = len(rows) > safe_limit
    records = rows[:safe_limit]
    next_cursor = str(records[-1].id) if has_more and records else ""

    return {
        "items": [_serialize_points_record(item) for item in records],
        "cursor": normalized_cursor,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": safe_limit,
    }


def _change_points_balance(
    db: Session,
    *,
    user_pk: int,
    delta: int,
    biz_type: str,
    biz_key: str,
    title: str,
    remark: str | None = None,
    meta: dict[str, Any] | None = None,
    use_reserved_balance: bool = False,
    commit: bool = True,
) -> dict[str, Any]:
    normalized_biz_type = _normalize_text(biz_type)
    normalized_biz_key = _normalize_text(biz_key)
    existing = _get_points_transaction(
        db=db,
        user_pk=user_pk,
        biz_type=normalized_biz_type,
        biz_key=normalized_biz_key,
    )
    if existing is not None:
        account = _get_points_account(db=db, user_pk=user_pk)
        return {
            "created": False,
            "balance": int(account.balance or 0),
            "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
            "transaction": _serialize_points_record(existing),
        }

    safe_delta = int(delta or 0)
    account = _get_points_account(db=db, user_pk=user_pk)
    current_balance = int(account.balance or 0)
    current_frozen_balance = int(account.frozen_balance or 0)
    available_balance = current_balance - current_frozen_balance

    if safe_delta < 0:
        spend_amount = abs(safe_delta)
        if use_reserved_balance:
            if current_frozen_balance < spend_amount or current_balance < spend_amount:
                raise BusinessException(message="积分冻结余额不足，无法完成抵扣", code=4807, status_code=400)
            account.frozen_balance = current_frozen_balance - spend_amount
            account.balance = current_balance - spend_amount
        else:
            if available_balance < spend_amount:
                raise BusinessException(message="积分不足，无法完成操作", code=4808, status_code=400)
            account.balance = current_balance - spend_amount
    else:
        account.balance = current_balance + safe_delta

    transaction = UserPointsTransaction(
        user_pk=int(user_pk),
        change_amount=safe_delta,
        balance_after=int(account.balance or 0),
        biz_type=normalized_biz_type,
        biz_key=normalized_biz_key,
        title=_normalize_text(title),
        remark=_normalize_text(remark)[:255] or None,
        meta_json=json.dumps(meta, ensure_ascii=False) if isinstance(meta, dict) else None,
    )
    db.add(account)
    db.add(transaction)

    if commit:
        db.commit()
        db.refresh(account)
        db.refresh(transaction)

    return {
        "created": True,
        "balance": int(account.balance or 0),
        "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
        "transaction": _serialize_points_record(transaction),
    }


def reserve_points_for_member_order(
    db: Session,
    *,
    user_pk: int,
    points_cost: int,
    order_no: str,
    commit: bool = True,
) -> dict[str, int]:
    safe_points_cost = _normalize_positive_int(points_cost, 0)
    account = _get_points_account(db=db, user_pk=user_pk)
    if safe_points_cost <= 0:
        return {
            "balance": int(account.balance or 0),
            "frozen_balance": int(account.frozen_balance or 0),
            "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
        }

    balance = int(account.balance or 0)
    frozen_balance = int(account.frozen_balance or 0)
    available_balance = balance - frozen_balance
    if available_balance < safe_points_cost:
        raise BusinessException(message="积分不足，无法使用积分优惠", code=4801, status_code=400)

    account.frozen_balance = frozen_balance + safe_points_cost
    db.add(account)
    if commit:
        db.commit()
        db.refresh(account)

    return {
        "balance": int(account.balance or 0),
        "frozen_balance": int(account.frozen_balance or 0),
        "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
    }


def release_reserved_points_for_member_order(
    db: Session,
    *,
    user_pk: int,
    points_cost: int,
    commit: bool = True,
) -> dict[str, int]:
    safe_points_cost = _normalize_positive_int(points_cost, 0)
    account = _get_points_account(db=db, user_pk=user_pk)
    if safe_points_cost > 0:
        account.frozen_balance = max(int(account.frozen_balance or 0) - safe_points_cost, 0)
        db.add(account)
        if commit:
            db.commit()
            db.refresh(account)

    return {
        "balance": int(account.balance or 0),
        "frozen_balance": int(account.frozen_balance or 0),
        "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
    }


def consume_points_for_member_order(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
    points_cost: int,
    plan_name: str,
    use_reserved_balance: bool,
    commit: bool = True,
) -> dict[str, Any]:
    safe_points_cost = _normalize_positive_int(points_cost, 0)
    if safe_points_cost <= 0:
        account = _get_points_account(db=db, user_pk=user_pk)
        return {
            "balance": int(account.balance or 0),
            "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
            "transaction": None,
            "created": False,
        }

    return _change_points_balance(
        db=db,
        user_pk=user_pk,
        delta=-safe_points_cost,
        biz_type="member_discount",
        biz_key=_normalize_text(order_no),
        title="会员积分抵扣",
        remark=f"{_normalize_text(plan_name) or '会员'}积分抵扣",
        meta={
            "order_no": _normalize_text(order_no),
            "plan_name": _normalize_text(plan_name),
            "points_cost": safe_points_cost,
        },
        use_reserved_balance=bool(use_reserved_balance),
        commit=commit,
    )


def award_points(
    db: Session,
    *,
    user_pk: int,
    amount: int,
    biz_type: str,
    biz_key: str,
    title: str,
    remark: str | None = None,
    meta: dict[str, Any] | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    safe_amount = _normalize_positive_int(amount, 0)
    if safe_amount <= 0:
        account = _get_points_account(db=db, user_pk=user_pk)
        return {
            "created": False,
            "balance": int(account.balance or 0),
            "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
            "transaction": None,
        }

    return _change_points_balance(
        db=db,
        user_pk=user_pk,
        delta=safe_amount,
        biz_type=biz_type,
        biz_key=biz_key,
        title=title,
        remark=remark,
        meta=meta,
        commit=commit,
    )


def _is_profile_completed(user: User) -> bool:
    for field_name in PROFILE_COMPLETE_FIELDS:
        value = getattr(user, field_name, None)
        if not _normalize_text(value):
            return False
    return True


def grant_profile_completion_points(db: Session, *, user: User) -> dict[str, Any] | None:
    if not _is_profile_completed(user):
        return None

    task_rules = resolve_points_task_rules(db=db)
    task_rule = task_rules[TASK_COMPLETE_PROFILE]
    if not bool(task_rule["enabled"]):
        return None

    return award_points(
        db=db,
        user_pk=int(user.id),
        amount=int(task_rule["amount"]),
        biz_type=TASK_COMPLETE_PROFILE,
        biz_key="completed",
        title=task_rule["title"],
        remark="首次完善个人资料奖励",
        meta={"task_key": TASK_COMPLETE_PROFILE},
    )


def grant_publish_resource_points(db: Session, *, user_pk: int, post_code: str) -> dict[str, Any] | None:
    task_rules = resolve_points_task_rules(db=db)
    task_rule = task_rules[TASK_PUBLISH_RESOURCE]
    if not bool(task_rule["enabled"]):
        return None

    safe_post_code = _normalize_text(post_code).upper()
    if not safe_post_code:
        return None

    return award_points(
        db=db,
        user_pk=int(user_pk),
        amount=int(task_rule["amount"]),
        biz_type=TASK_PUBLISH_RESOURCE,
        biz_key=safe_post_code,
        title=task_rule["title"],
        remark="发布资源奖励",
        meta={"task_key": TASK_PUBLISH_RESOURCE, "post_code": safe_post_code},
    )


def grant_real_name_verification_points(
    db: Session,
    *,
    user_pk: int,
    verification_id: int | None = None,
) -> dict[str, Any] | None:
    task_rules = resolve_points_task_rules(db=db)
    task_rule = task_rules[TASK_REAL_NAME_VERIFIED]
    if not bool(task_rule["enabled"]):
        return None

    record = get_user_verification(
        db=db,
        user_pk=int(user_pk),
        verify_type=VerificationType.REAL_NAME.value,
    )
    if record is None or record.status != VerificationStatus.APPROVED.value:
        return None

    biz_key = str(int(verification_id or record.id or 0)) if int(verification_id or record.id or 0) > 0 else "approved"
    return award_points(
        db=db,
        user_pk=int(user_pk),
        amount=int(task_rule["amount"]),
        biz_type=TASK_REAL_NAME_VERIFIED,
        biz_key=biz_key,
        title=task_rule["title"],
        remark="实名认证通过奖励",
        meta={"task_key": TASK_REAL_NAME_VERIFIED, "verification_id": int(record.id)},
    )


def grant_invite_friend_points(db: Session, *, invitee_user: User) -> dict[str, Any] | None:
    inviter_user_pk = int(invitee_user.inviter_user_pk or 0)
    if inviter_user_pk <= 0 or inviter_user_pk == int(invitee_user.id):
        return None

    task_rules = resolve_points_task_rules(db=db)
    task_rule = task_rules[TASK_INVITE_FRIEND]
    if not bool(task_rule["enabled"]):
        return None

    inviter = get_user_by_id(db=db, user_id=inviter_user_pk)
    if inviter is None:
        return None

    return award_points(
        db=db,
        user_pk=int(inviter.id),
        amount=int(task_rule["amount"]),
        biz_type=TASK_INVITE_FRIEND,
        biz_key=f"invitee:{int(invitee_user.id)}",
        title=task_rule["title"],
        remark="邀请新用户注册奖励",
        meta={
            "task_key": TASK_INVITE_FRIEND,
            "invitee_user_pk": int(invitee_user.id),
            "invitee_user_id": _normalize_text(invitee_user.user_id),
        },
    )


def claim_daily_check_in(db: Session, *, user_pk: int) -> dict[str, Any]:
    task_rules = resolve_points_task_rules(db=db)
    task_rule = task_rules[TASK_DAILY_CHECK_IN]
    if not bool(task_rule["enabled"]):
        raise BusinessException(message="签到功能未开启", code=4802, status_code=400)

    today_key = _utc_now().strftime("%Y-%m-%d")
    result = award_points(
        db=db,
        user_pk=int(user_pk),
        amount=int(task_rule["amount"]),
        biz_type=TASK_DAILY_CHECK_IN,
        biz_key=today_key,
        title=task_rule["title"],
        remark="每日签到奖励",
        meta={"task_key": TASK_DAILY_CHECK_IN, "date": today_key},
    )
    if not bool(result["created"]):
        raise BusinessException(message="今日已签到，请明天再来", code=4803, status_code=400)
    return result


def resolve_member_points_offer(
    db: Session,
    *,
    user_pk: int,
    plan_id: str,
    price_amount: Decimal,
) -> dict[str, Any]:
    rules = resolve_member_discount_rules(db=db)
    rule = rules.get(_normalize_text(plan_id), {})
    account = _get_points_account(db=db, user_pk=int(user_pk))
    current_balance = max(int(account.balance or 0), 0)
    current_frozen = max(int(account.frozen_balance or 0), 0)
    available_balance = max(current_balance - current_frozen, 0)

    enabled = bool(rule.get("enabled"))
    required_points = _normalize_positive_int(rule.get("required_points"), 0)
    discount_rate = rule.get("discount_rate") if isinstance(rule.get("discount_rate"), Decimal) else Decimal("1.0000")

    if not enabled or required_points <= 0 or discount_rate >= Decimal("1.0000"):
        return {
            "enabled": False,
            "required_points": required_points,
            "discount_rate": float(Decimal("1.0000")),
            "discount_text": None,
            "can_use": False,
            "points_balance": current_balance,
            "available_points": available_balance,
            "frozen_points": current_frozen,
            "missing_points": max(required_points - available_balance, 0),
            "original_price": float(price_amount),
            "discounted_price": float(price_amount),
            "saved_amount": 0.0,
        }

    discounted_price = _discount_price(price_amount, discount_rate)
    saved_amount = (price_amount - discounted_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    can_use = available_balance >= required_points

    return {
        "enabled": True,
        "required_points": required_points,
        "discount_rate": float(discount_rate),
        "discount_text": _discount_text(discount_rate),
        "can_use": can_use,
        "points_balance": current_balance,
        "available_points": available_balance,
        "frozen_points": current_frozen,
        "missing_points": max(required_points - available_balance, 0),
        "original_price": float(price_amount),
        "discounted_price": float(discounted_price),
        "saved_amount": float(saved_amount),
    }


def cleanup_expired_member_points_orders(db: Session, *, user_pk: int | None = None) -> int:
    expire_before = _utc_now() - timedelta(minutes=POINTS_RESERVATION_EXPIRE_MINUTES)
    stmt = select(MemberOrder).where(
        MemberOrder.status == "pending",
        MemberOrder.used_points_discount.is_(True),
        MemberOrder.points_cost > 0,
        MemberOrder.points_status == POINTS_STATUS_RESERVED,
        MemberOrder.created_at < expire_before,
    )
    if user_pk is not None:
        stmt = stmt.where(MemberOrder.user_pk == int(user_pk))

    orders = db.execute(stmt).scalars().all()
    released = 0
    for order in orders:
        release_reserved_points_for_member_order(
            db=db,
            user_pk=int(order.user_pk),
            points_cost=int(order.points_cost or 0),
            commit=False,
        )
        order.points_status = POINTS_STATUS_RELEASED
        order.status = "failed"
        db.add(order)
        released += 1

    if released:
        db.commit()
    return released


def get_points_center_overview(db: Session, *, user_pk: int) -> dict[str, Any]:
    user = get_user_by_id(db=db, user_id=int(user_pk))
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    cleanup_expired_member_points_orders(db=db, user_pk=int(user_pk))

    account = _get_points_account(db=db, user_pk=int(user_pk))
    task_rules = resolve_points_task_rules(db=db)
    discount_rules = resolve_member_discount_rules(db=db)

    today_key = _utc_now().strftime("%Y-%m-%d")
    checked_in_today = (
        _get_points_transaction(
            db=db,
            user_pk=int(user_pk),
            biz_type=TASK_DAILY_CHECK_IN,
            biz_key=today_key,
        )
        is not None
    )
    profile_rewarded = (
        _get_points_transaction(
            db=db,
            user_pk=int(user_pk),
            biz_type=TASK_COMPLETE_PROFILE,
            biz_key="completed",
        )
        is not None
    )
    profile_completed = _is_profile_completed(user)
    real_name_record = get_user_verification(
        db=db,
        user_pk=int(user_pk),
        verify_type=VerificationType.REAL_NAME.value,
    )
    real_name_approved = bool(real_name_record and real_name_record.status == VerificationStatus.APPROVED.value)
    real_name_rewarded = bool(
        db.execute(
            select(func.count(UserPointsTransaction.id)).where(
                UserPointsTransaction.user_pk == int(user_pk),
                UserPointsTransaction.biz_type == TASK_REAL_NAME_VERIFIED,
            )
        ).scalar_one()
        or 0
    )
    invite_success_count = int(
        db.execute(
            select(func.count(UserPointsTransaction.id)).where(
                UserPointsTransaction.user_pk == int(user_pk),
                UserPointsTransaction.biz_type == TASK_INVITE_FRIEND,
            )
        ).scalar_one()
        or 0
    )

    records_preview = db.execute(
        select(UserPointsTransaction)
        .where(UserPointsTransaction.user_pk == int(user_pk))
        .order_by(UserPointsTransaction.id.desc())
        .limit(10)
    ).scalars().all()

    membership_discounts = []
    for plan_id, rule in discount_rules.items():
        membership_discounts.append(
            {
                "plan_id": plan_id,
                "enabled": bool(rule["enabled"]),
                "required_points": int(rule["required_points"]),
                "discount_rate": float(rule["discount_rate"]),
                "discount_text": str(rule["discount_text"]),
            }
        )

    tasks = [
        {
            "key": TASK_DAILY_CHECK_IN,
            "title": task_rules[TASK_DAILY_CHECK_IN]["title"],
            "amount": int(task_rules[TASK_DAILY_CHECK_IN]["amount"]),
            "enabled": bool(task_rules[TASK_DAILY_CHECK_IN]["enabled"]),
            "description": task_rules[TASK_DAILY_CHECK_IN]["description"],
            "completed": checked_in_today,
            "action": task_rules[TASK_DAILY_CHECK_IN]["action"],
        },
        {
            "key": TASK_PUBLISH_RESOURCE,
            "title": task_rules[TASK_PUBLISH_RESOURCE]["title"],
            "amount": int(task_rules[TASK_PUBLISH_RESOURCE]["amount"]),
            "enabled": bool(task_rules[TASK_PUBLISH_RESOURCE]["enabled"]),
            "description": task_rules[TASK_PUBLISH_RESOURCE]["description"],
            "completed": False,
            "action": task_rules[TASK_PUBLISH_RESOURCE]["action"],
        },
        {
            "key": TASK_COMPLETE_PROFILE,
            "title": task_rules[TASK_COMPLETE_PROFILE]["title"],
            "amount": int(task_rules[TASK_COMPLETE_PROFILE]["amount"]),
            "enabled": bool(task_rules[TASK_COMPLETE_PROFILE]["enabled"]),
            "description": task_rules[TASK_COMPLETE_PROFILE]["description"],
            "completed": profile_rewarded,
            "eligible": profile_completed,
            "action": task_rules[TASK_COMPLETE_PROFILE]["action"],
        },
        {
            "key": TASK_REAL_NAME_VERIFIED,
            "title": task_rules[TASK_REAL_NAME_VERIFIED]["title"],
            "amount": int(task_rules[TASK_REAL_NAME_VERIFIED]["amount"]),
            "enabled": bool(task_rules[TASK_REAL_NAME_VERIFIED]["enabled"]),
            "description": task_rules[TASK_REAL_NAME_VERIFIED]["description"],
            "completed": real_name_rewarded,
            "eligible": real_name_approved,
            "action": task_rules[TASK_REAL_NAME_VERIFIED]["action"],
        },
        {
            "key": TASK_INVITE_FRIEND,
            "title": task_rules[TASK_INVITE_FRIEND]["title"],
            "amount": int(task_rules[TASK_INVITE_FRIEND]["amount"]),
            "enabled": bool(task_rules[TASK_INVITE_FRIEND]["enabled"]),
            "description": task_rules[TASK_INVITE_FRIEND]["description"],
            "completed_count": invite_success_count,
            "action": task_rules[TASK_INVITE_FRIEND]["action"],
        },
    ]

    return {
        "points": {
            "balance": int(account.balance or 0),
            "available_balance": max(int(account.balance or 0) - int(account.frozen_balance or 0), 0),
            "frozen_balance": int(account.frozen_balance or 0),
        },
        "invite": {
            "invite_code": _normalize_text(user.user_id),
            "inviter_user_pk": int(user.inviter_user_pk or 0) or None,
            "invite_success_count": invite_success_count,
        },
        "tasks": tasks,
        "member_discounts": membership_discounts,
        "records_preview": [_serialize_points_record(item) for item in records_preview],
    }


def resolve_inviter_user_pk(db: Session, *, invite_code: str | None, current_user_pk: int | None = None) -> int | None:
    normalized_invite_code = _normalize_text(invite_code)
    if not normalized_invite_code:
        return None
    inviter = get_user_by_business_user_id(db=db, business_user_id=normalized_invite_code)
    if inviter is None:
        return None
    if current_user_pk and int(inviter.id) == int(current_user_pk):
        return None
    return int(inviter.id)
