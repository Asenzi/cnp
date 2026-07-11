from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from secrets import token_hex
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.models.circle import Circle
from app.models.circle_join_request import CircleJoinRequest
from app.models.split_rule import SplitRule
from app.models.split_transaction import SplitTransaction
from app.models.settlement_ledger import SettlementLedger
from app.models.sys_config import SysConfig
from app.models.user import User
from app.models.user_settlement import UserSettlement
from app.models.withdrawal_order import WithdrawalOrder
from app.payment.service import PAY_CHANNEL_WXPAY, _dict_to_xml, _sign_wechat_v2, _xml_to_dict

BIZ_CIRCLE_JOIN = "circle_join"
ROLE_CIRCLE_OWNER = "circle_owner"
STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_CANCELLED = "cancelled"
STATUS_RETURNED = "returned"
STATUS_READY = "ready"
STATUS_EXTERNAL_FAILED = "external_failed"
WITHDRAWAL_PENDING = "pending"
WITHDRAWAL_SUCCESS = "success"
WITHDRAWAL_FAILED = "failed"

DEFAULT_SERVICE_FEE_RATE = Decimal("0.10")
DEFAULT_AUTO_SETTLE_ENABLED = True
DEFAULT_WECHAT_PROFIT_SHARING_ENABLED = False


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_lower(value: str | None) -> str:
    return _normalize_text(value).lower()


def _to_decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _money(value: Any) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    safe_value = value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
    return safe_value.isoformat()


def _serialize_decimal(value: Any) -> float:
    return float(_money(value))


def _bool_config(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = _normalize_lower(value)
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _get_or_create_config(
    db: Session,
    *,
    config_key: str,
    default_value: str,
    description: str,
) -> SysConfig:
    row = db.scalar(select(SysConfig).where(SysConfig.config_key == config_key).limit(1))
    if row is not None:
        return row
    row = SysConfig(
        config_key=config_key,
        config_value=default_value,
        config_group="settlement",
        description=description,
    )
    db.add(row)
    db.flush()
    return row


def get_admin_split_config(db: Session) -> dict[str, Any]:
    service_fee = _get_or_create_config(
        db,
        config_key="settlement.circle_join.service_fee_rate",
        default_value=str(DEFAULT_SERVICE_FEE_RATE),
        description="付费入圈技术服务费比例，0.10 表示 10%",
    )
    auto_settle = _get_or_create_config(
        db,
        config_key="settlement.circle_join.auto_settle_enabled",
        default_value="1" if DEFAULT_AUTO_SETTLE_ENABLED else "0",
        description="付费入圈通过后是否自动记账到圈主收益",
    )
    wechat_profit_sharing = _get_or_create_config(
        db,
        config_key="settlement.circle_join.wechat_profit_sharing_enabled",
        default_value="1" if settings.WECHAT_PAY_PROFIT_SHARING_ENABLED else "0",
        description="付费入圈通过后是否发起微信真实分账",
    )
    db.commit()
    rate = _resolve_service_fee_rate(db)
    updated_values = [
        value
        for value in (
            service_fee.updated_at,
            auto_settle.updated_at,
            wechat_profit_sharing.updated_at,
        )
        if value is not None
    ]
    return {
        "biz_type": BIZ_CIRCLE_JOIN,
        "service_fee_rate": float(rate),
        "receiver_rate": float((Decimal("1.00") - rate).quantize(Decimal("0.0001"))),
        "auto_settle_enabled": _bool_config(auto_settle.config_value, DEFAULT_AUTO_SETTLE_ENABLED),
        "wechat_profit_sharing_enabled": _bool_config(
            wechat_profit_sharing.config_value,
            DEFAULT_WECHAT_PROFIT_SHARING_ENABLED,
        ),
        "updated_at": _serialize_datetime(max(updated_values) if updated_values else None),
    }


def update_admin_split_config(
    db: Session,
    *,
    service_fee_rate: float | str | Decimal,
    auto_settle_enabled: bool,
    wechat_profit_sharing_enabled: bool | None = None,
) -> dict[str, Any]:
    rate = _to_decimal(service_fee_rate, DEFAULT_SERVICE_FEE_RATE).quantize(Decimal("0.0001"))
    if rate < Decimal("0") or rate >= Decimal("1"):
        raise BusinessException(message="技术服务费比例必须在 0 到 1 之间", code=4621, status_code=400)

    service_fee = _get_or_create_config(
        db,
        config_key="settlement.circle_join.service_fee_rate",
        default_value=str(DEFAULT_SERVICE_FEE_RATE),
        description="付费入圈技术服务费比例，0.10 表示 10%",
    )
    service_fee.config_value = str(rate)
    service_fee.config_group = "settlement"
    service_fee.description = "付费入圈技术服务费比例，0.10 表示 10%"

    auto_settle = _get_or_create_config(
        db,
        config_key="settlement.circle_join.auto_settle_enabled",
        default_value="1",
        description="付费入圈通过后是否自动记账到圈主收益",
    )
    auto_settle.config_value = "1" if bool(auto_settle_enabled) else "0"
    auto_settle.config_group = "settlement"
    auto_settle.description = "付费入圈通过后是否自动记账到圈主收益"

    wechat_profit_sharing = _get_or_create_config(
        db,
        config_key="settlement.circle_join.wechat_profit_sharing_enabled",
        default_value="1" if settings.WECHAT_PAY_PROFIT_SHARING_ENABLED else "0",
        description="付费入圈通过后是否发起微信真实分账",
    )
    wechat_profit_sharing.config_value = "1" if bool(wechat_profit_sharing_enabled) else "0"
    wechat_profit_sharing.config_group = "settlement"
    wechat_profit_sharing.description = "付费入圈通过后是否发起微信真实分账"

    _upsert_split_rule(db, receiver_rate=(Decimal("1.00") - rate).quantize(Decimal("0.0001")))
    db.commit()
    return get_admin_split_config(db)


def _resolve_service_fee_rate(db: Session) -> Decimal:
    row = db.scalar(
        select(SysConfig).where(SysConfig.config_key == "settlement.circle_join.service_fee_rate").limit(1)
    )
    rate = _to_decimal(row.config_value if row is not None else None, DEFAULT_SERVICE_FEE_RATE).quantize(Decimal("0.0001"))
    if rate < Decimal("0") or rate >= Decimal("1"):
        return DEFAULT_SERVICE_FEE_RATE
    return rate


def _resolve_auto_settle_enabled(db: Session) -> bool:
    row = db.scalar(
        select(SysConfig).where(SysConfig.config_key == "settlement.circle_join.auto_settle_enabled").limit(1)
    )
    return _bool_config(row.config_value if row is not None else None, DEFAULT_AUTO_SETTLE_ENABLED)


def is_wechat_profit_sharing_enabled(db: Session) -> bool:
    row = db.scalar(
        select(SysConfig)
        .where(SysConfig.config_key == "settlement.circle_join.wechat_profit_sharing_enabled")
        .limit(1)
    )
    return _bool_config(
        row.config_value if row is not None else None,
        bool(settings.WECHAT_PAY_PROFIT_SHARING_ENABLED),
    )


def _upsert_split_rule(db: Session, *, receiver_rate: Decimal) -> SplitRule:
    row = db.scalar(
        select(SplitRule)
        .where(SplitRule.biz_type == BIZ_CIRCLE_JOIN, SplitRule.role_type == ROLE_CIRCLE_OWNER)
        .limit(1)
    )
    if row is None:
        row = SplitRule(
            biz_type=BIZ_CIRCLE_JOIN,
            role_type=ROLE_CIRCLE_OWNER,
            split_type="percentage",
            split_value=receiver_rate,
            priority=100,
            enabled=True,
            description="付费入圈圈主分账比例",
        )
        db.add(row)
    else:
        row.split_type = "percentage"
        row.split_value = receiver_rate
        row.enabled = True
        row.description = "付费入圈圈主分账比例"
    return row


def _ensure_settlement(db: Session, *, user_pk: int) -> UserSettlement:
    row = db.scalar(
        select(UserSettlement).where(UserSettlement.user_pk == int(user_pk)).with_for_update().limit(1)
    )
    if row is not None:
        return row
    row = UserSettlement(user_pk=int(user_pk))
    db.add(row)
    db.flush()
    return row


def _record_ledger(
    db: Session,
    *,
    user_pk: int,
    change_amount: Decimal,
    account: UserSettlement,
    biz_type: str,
    biz_key: str,
    title: str,
    remark: str | None = None,
) -> SettlementLedger | None:
    normalized_biz_type = _normalize_text(biz_type)
    normalized_biz_key = _normalize_text(biz_key)
    existing = db.scalar(
        select(SettlementLedger)
        .where(
            SettlementLedger.user_pk == int(user_pk),
            SettlementLedger.biz_type == normalized_biz_type,
            SettlementLedger.biz_key == normalized_biz_key,
        )
        .limit(1)
    )
    if existing is not None:
        return existing
    row = SettlementLedger(
        user_pk=int(user_pk),
        change_amount=_money(change_amount),
        available_after=_money(account.available_balance),
        frozen_after=_money(account.frozen_balance),
        biz_type=normalized_biz_type,
        biz_key=normalized_biz_key,
        title=_normalize_text(title),
        remark=_normalize_text(remark) or None,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise BusinessException(message="结算流水已存在，请勿重复操作", code=4650, status_code=409)
    return row


def _generate_withdrawal_order_no() -> str:
    return f"W{_now().strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


def _get_split_by_order(db: Session, *, order_no: str) -> SplitTransaction | None:
    normalized_order_no = _normalize_text(order_no)
    if not normalized_order_no:
        return None
    return db.scalar(
        select(SplitTransaction)
        .where(
            SplitTransaction.order_no == normalized_order_no,
            SplitTransaction.biz_type == BIZ_CIRCLE_JOIN,
            SplitTransaction.role_type == ROLE_CIRCLE_OWNER,
        )
        .limit(1)
    )


def _generate_external_split_order_no(row: SplitTransaction) -> str:
    base_order = _normalize_text(row.order_no)[-24:] or str(row.id)
    return f"PS{int(row.id)}{base_order}"[:64]


def _wechat_receiver_payload(owner: User) -> dict[str, Any]:
    openid = _normalize_text(owner.wechat_openid)
    if not openid:
        raise BusinessException(message="圈主未绑定微信，无法发起微信分账", code=4631, status_code=409)
    return {
        "type": "PERSONAL_OPENID",
        "account": openid,
        "relation_type": "SERVICE_PROVIDER",
        "custom_relation": "圈主",
    }


def _wechat_request(
    *,
    url: str,
    params: dict[str, str],
    require_cert: bool = False,
) -> dict[str, str]:
    api_key = _normalize_text(settings.WECHAT_PAY_API_V2_KEY)
    if not api_key:
        raise BusinessException(message="微信支付 API v2 密钥未配置", code=4632, status_code=500)
    params["sign"] = _sign_wechat_v2(params, api_key=api_key)
    request = urllib.request.Request(
        url,
        data=_dict_to_xml(params).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )
    context = None
    if require_cert:
        cert_path = _normalize_text(settings.WECHAT_PAY_CERT_PATH)
        key_path = _normalize_text(settings.WECHAT_PAY_KEY_PATH)
        if not cert_path or not key_path:
            raise BusinessException(message="微信支付证书未配置，无法发起真实分账", code=4633, status_code=503)
        context = ssl.create_default_context()
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    try:
        if context is None:
            response_ctx = urllib.request.urlopen(request, timeout=15)  # noqa: S310
        else:
            response_ctx = urllib.request.urlopen(request, timeout=15, context=context)  # noqa: S310
        with response_ctx as response:
            return _xml_to_dict(response.read().decode("utf-8", errors="ignore"))
    except (OSError, urllib.error.URLError) as exc:
        raise BusinessException(message="微信分账请求失败", code=4634, status_code=502) from exc


def _ensure_wechat_profit_receiver(owner: User) -> dict[str, str]:
    app_id = _normalize_text(settings.WECHAT_PAY_APP_ID) or _normalize_text(settings.WECHAT_MINI_APP_ID)
    mch_id = _normalize_text(settings.WECHAT_PAY_MCH_ID)
    add_receiver_url = _normalize_text(settings.WECHAT_PAY_PROFIT_SHARING_ADD_RECEIVER_URL)
    if not app_id or not mch_id or not add_receiver_url:
        raise BusinessException(message="微信分账接收方配置不完整", code=4635, status_code=500)
    receiver = _wechat_receiver_payload(owner)
    result = _wechat_request(
        url=add_receiver_url,
        params={
            "appid": app_id,
            "mch_id": mch_id,
            "nonce_str": _now().strftime("%Y%m%d%H%M%S%f"),
            "receiver": json.dumps(receiver, ensure_ascii=False, separators=(",", ":")),
        },
        require_cert=False,
    )
    return_code = _normalize_text(result.get("return_code")).upper()
    result_code = _normalize_text(result.get("result_code")).upper()
    err_code = _normalize_text(result.get("err_code")).upper()
    if return_code == "SUCCESS" and (result_code == "SUCCESS" or err_code == "RECEIVER_ALREADY_EXIST"):
        return result
    raise BusinessException(
        message=f"微信分账接收方添加失败：{result.get('err_code_des') or result.get('return_msg') or err_code or 'unknown'}",
        code=4636,
        status_code=502,
    )


def _execute_wechat_profit_sharing(
    *,
    row: SplitTransaction,
    join_request: CircleJoinRequest,
    owner: User,
) -> bool:
    transaction_id = _normalize_text(join_request.transaction_id)
    if not transaction_id:
        row.channel = PAY_CHANNEL_WXPAY
        row.external_status = "ready"
        row.external_error = "缺少微信支付 transaction_id，等待支付回调后重试"
        return False

    app_id = _normalize_text(settings.WECHAT_PAY_APP_ID) or _normalize_text(settings.WECHAT_MINI_APP_ID)
    mch_id = _normalize_text(settings.WECHAT_PAY_MCH_ID)
    profit_sharing_url = _normalize_text(settings.WECHAT_PAY_PROFIT_SHARING_URL)
    if not app_id or not mch_id or not profit_sharing_url:
        raise BusinessException(message="微信真实分账配置不完整", code=4637, status_code=500)

    receiver = _wechat_receiver_payload(owner)
    amount_fen = int((_money(row.split_amount) * Decimal("100")).quantize(Decimal("1")))
    if amount_fen <= 0:
        return False

    _ensure_wechat_profit_receiver(owner)
    external_order_no = _normalize_text(row.external_order_no) or _generate_external_split_order_no(row)
    receivers = [
        {
            "type": receiver["type"],
            "account": receiver["account"],
            "amount": amount_fen,
            "description": "圈脉链付费入圈圈主收益",
        }
    ]
    result = _wechat_request(
        url=profit_sharing_url,
        params={
            "appid": app_id,
            "mch_id": mch_id,
            "nonce_str": _now().strftime("%Y%m%d%H%M%S%f"),
            "transaction_id": transaction_id,
            "out_order_no": external_order_no,
            "receivers": json.dumps(receivers, ensure_ascii=False, separators=(",", ":")),
        },
        require_cert=True,
    )
    if (
        _normalize_text(result.get("return_code")).upper() == "SUCCESS"
        and _normalize_text(result.get("result_code")).upper() == "SUCCESS"
    ):
        row.channel = PAY_CHANNEL_WXPAY
        row.receiver_openid = receiver["account"]
        row.external_transaction_id = transaction_id
        row.external_order_no = external_order_no
        row.external_status = "success"
        row.external_error = None
        return True

    raise BusinessException(
        message=f"微信真实分账失败：{result.get('err_code_des') or result.get('return_msg') or result.get('err_code') or 'unknown'}",
        code=4638,
        status_code=502,
    )


def _mark_external_split_failed(row: SplitTransaction, exc: Exception) -> None:
    row.channel = PAY_CHANNEL_WXPAY
    row.external_status = STATUS_EXTERNAL_FAILED
    row.external_error = str(getattr(exc, "message", None) or exc)[:1000]
    row.split_status = STATUS_EXTERNAL_FAILED


def create_or_update_circle_join_split(
    db: Session,
    *,
    join_request: CircleJoinRequest,
    circle: Circle,
) -> SplitTransaction | None:
    amount = _money(join_request.amount)
    order_no = _normalize_text(join_request.order_no)
    if amount <= Decimal("0.00") or not order_no:
        return None

    service_fee_rate = _resolve_service_fee_rate(db)
    receiver_rate = (Decimal("1.00") - service_fee_rate).quantize(Decimal("0.0001"))
    _upsert_split_rule(db, receiver_rate=receiver_rate)

    service_fee_amount = _money(amount * service_fee_rate)
    receiver_amount = _money(amount - service_fee_amount)
    row = _get_split_by_order(db, order_no=order_no)
    if row is None:
        row = SplitTransaction(
            order_no=order_no,
            biz_type=BIZ_CIRCLE_JOIN,
            split_from_user_pk=int(join_request.user_pk),
            split_to_user_pk=int(circle.owner_user_pk),
            role_type=ROLE_CIRCLE_OWNER,
            total_amount=amount,
            split_amount=receiver_amount,
            platform_fee=service_fee_amount,
            split_status=STATUS_PENDING,
            channel="internal",
            freeze_until=None,
            remark=f"付费入圈分账，技术服务费 {service_fee_rate * Decimal('100')}%",
        )
        db.add(row)
    elif row.split_status in {STATUS_PENDING, STATUS_READY, STATUS_EXTERNAL_FAILED}:
        row.split_from_user_pk = int(join_request.user_pk)
        row.split_to_user_pk = int(circle.owner_user_pk)
        row.total_amount = amount
        row.split_amount = receiver_amount
        row.platform_fee = service_fee_amount
        row.remark = f"付费入圈分账，技术服务费 {service_fee_rate * Decimal('100')}%"
    db.flush()
    return row


def settle_circle_join_split(
    db: Session,
    *,
    join_request: CircleJoinRequest,
    circle: Circle,
) -> SplitTransaction | None:
    row = create_or_update_circle_join_split(db, join_request=join_request, circle=circle)
    if row is None:
        return None
    if row.split_status == STATUS_SUCCESS:
        return row
    if row.split_status in {STATUS_CANCELLED, STATUS_RETURNED}:
        return row
    if not _resolve_auto_settle_enabled(db):
        row.split_status = STATUS_READY
        db.flush()
        return row

    if (
        is_wechat_profit_sharing_enabled(db)
        and _normalize_lower(join_request.pay_channel) == PAY_CHANNEL_WXPAY
    ):
        owner = db.scalar(select(User).where(User.id == int(circle.owner_user_pk)).limit(1))
        if owner is None:
            row.split_status = STATUS_EXTERNAL_FAILED
            row.external_status = STATUS_EXTERNAL_FAILED
            row.external_error = "圈主用户不存在，无法发起微信真实分账"
            db.flush()
            return row
        try:
            if not _execute_wechat_profit_sharing(row=row, join_request=join_request, owner=owner):
                row.split_status = STATUS_READY
                db.flush()
                return row
        except Exception as exc:  # noqa: BLE001
            _mark_external_split_failed(row, exc)
            db.flush()
            return row

    settlement = _ensure_settlement(db, user_pk=int(row.split_to_user_pk))
    split_amount = _money(row.split_amount)
    settlement.available_balance = _money(settlement.available_balance) + split_amount
    settlement.total_income = _money(settlement.total_income) + split_amount
    row.split_status = STATUS_SUCCESS
    row.executed_at = _now()
    _record_ledger(
        db,
        user_pk=int(row.split_to_user_pk),
        change_amount=split_amount,
        account=settlement,
        biz_type="circle_join_income",
        biz_key=_normalize_text(row.order_no),
        title="付费入圈收益",
        remark=_normalize_text(row.remark),
    )
    db.flush()
    return row


def cancel_circle_join_split(
    db: Session,
    *,
    join_request: CircleJoinRequest,
    reason: str,
) -> SplitTransaction | None:
    row = _get_split_by_order(db, order_no=_normalize_text(join_request.order_no))
    if row is None:
        return None
    if row.split_status == STATUS_SUCCESS:
        settlement = _ensure_settlement(db, user_pk=int(row.split_to_user_pk))
        split_amount = _money(row.split_amount)
        settlement.available_balance = max(
            Decimal("0.00"),
            _money(settlement.available_balance) - split_amount,
        )
        settlement.total_income = max(
            Decimal("0.00"),
            _money(settlement.total_income) - split_amount,
        )
        row.split_status = STATUS_RETURNED
        row.remark = f"{_normalize_text(row.remark)}；{reason}".strip("；")
        _record_ledger(
            db,
            user_pk=int(row.split_to_user_pk),
            change_amount=-split_amount,
            account=settlement,
            biz_type="circle_join_income_return",
            biz_key=_normalize_text(row.order_no),
            title="付费入圈收益退回",
            remark=reason,
        )
    elif row.split_status not in {STATUS_CANCELLED, STATUS_RETURNED}:
        row.split_status = STATUS_CANCELLED
        row.remark = f"{_normalize_text(row.remark)}；{reason}".strip("；")
    db.flush()
    return row


def get_user_income_overview(
    db: Session,
    *,
    user_pk: int,
    limit: int = 20,
) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 20), 1), 50)
    account = db.scalar(select(UserSettlement).where(UserSettlement.user_pk == int(user_pk)).limit(1))
    if account is None:
        account = UserSettlement(user_pk=int(user_pk))
        db.add(account)
        db.flush()

    rows = db.scalars(
        select(SplitTransaction)
        .where(SplitTransaction.split_to_user_pk == int(user_pk))
        .order_by(SplitTransaction.created_at.desc(), SplitTransaction.id.desc())
        .limit(safe_limit)
    ).all()
    pending_amount = db.scalar(
        select(func.coalesce(func.sum(SplitTransaction.split_amount), 0))
        .where(
            SplitTransaction.split_to_user_pk == int(user_pk),
            SplitTransaction.split_status.in_([STATUS_PENDING, STATUS_READY, STATUS_EXTERNAL_FAILED]),
        )
    )

    return {
        "account": {
            "available_balance": _serialize_decimal(account.available_balance),
            "frozen_balance": _serialize_decimal(account.frozen_balance),
            "pending_amount": _serialize_decimal(pending_amount),
            "total_income": _serialize_decimal(account.total_income),
            "total_withdrawn": _serialize_decimal(account.total_withdrawn),
            "updated_at": _serialize_datetime(account.updated_at),
        },
        "items": [
            {
                "id": int(item.id),
                "order_no": _normalize_text(item.order_no),
                "biz_type": _normalize_text(item.biz_type),
                "total_amount": _serialize_decimal(item.total_amount),
                "platform_fee": _serialize_decimal(item.platform_fee),
                "split_amount": _serialize_decimal(item.split_amount),
                "split_status": _normalize_text(item.split_status),
                "channel": _normalize_text(item.channel),
                "external_status": _normalize_text(item.external_status),
                "executed_at": _serialize_datetime(item.executed_at),
                "created_at": _serialize_datetime(item.created_at),
                "remark": _normalize_text(item.remark),
            }
            for item in rows
        ],
    }


def list_user_settlement_ledgers(
    db: Session,
    *,
    user_pk: int,
    limit: int = 30,
) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 30), 1), 100)
    rows = db.scalars(
        select(SettlementLedger)
        .where(SettlementLedger.user_pk == int(user_pk))
        .order_by(SettlementLedger.created_at.desc(), SettlementLedger.id.desc())
        .limit(safe_limit)
    ).all()
    return {
        "items": [
            {
                "id": int(item.id),
                "change_amount": _serialize_decimal(item.change_amount),
                "available_after": _serialize_decimal(item.available_after),
                "frozen_after": _serialize_decimal(item.frozen_after),
                "biz_type": _normalize_text(item.biz_type),
                "biz_key": _normalize_text(item.biz_key),
                "title": _normalize_text(item.title),
                "remark": _normalize_text(item.remark),
                "created_at": _serialize_datetime(item.created_at),
            }
            for item in rows
        ]
    }


def create_user_withdrawal(
    db: Session,
    *,
    user_pk: int,
    amount: float | str | Decimal,
    withdraw_type: str = "wechat",
    withdraw_account: str | None = None,
) -> dict[str, Any]:
    withdraw_amount = _money(amount)
    if withdraw_amount <= Decimal("0.00"):
        raise BusinessException(message="提现金额必须大于 0", code=4651, status_code=400)
    if withdraw_amount < Decimal("1.00"):
        raise BusinessException(message="单次提现金额不能低于 1 元", code=4652, status_code=400)
    account = _ensure_settlement(db, user_pk=user_pk)
    if _money(account.available_balance) < withdraw_amount:
        raise BusinessException(message="可提现余额不足", code=4653, status_code=409)

    account.available_balance = _money(account.available_balance) - withdraw_amount
    account.frozen_balance = _money(account.frozen_balance) + withdraw_amount
    order = WithdrawalOrder(
        order_no=_generate_withdrawal_order_no(),
        user_pk=int(user_pk),
        amount=withdraw_amount,
        fee=Decimal("0.00"),
        actual_amount=withdraw_amount,
        withdraw_type=_normalize_lower(withdraw_type) or "wechat",
        withdraw_account=_normalize_text(withdraw_account) or None,
        status=WITHDRAWAL_PENDING,
        remark="用户申请提现，等待后台人工打款确认",
    )
    db.add(order)
    db.flush()
    _record_ledger(
        db,
        user_pk=user_pk,
        change_amount=-withdraw_amount,
        account=account,
        biz_type="withdrawal_apply",
        biz_key=order.order_no,
        title="申请提现",
        remark="余额转入提现冻结",
    )
    db.commit()
    db.refresh(order)
    return _serialize_withdrawal(order)


def _serialize_withdrawal(order: WithdrawalOrder, user: User | None = None) -> dict[str, Any]:
    payload = {
        "id": int(order.id),
        "order_no": _normalize_text(order.order_no),
        "user_pk": int(order.user_pk),
        "amount": _serialize_decimal(order.amount),
        "fee": _serialize_decimal(order.fee),
        "actual_amount": _serialize_decimal(order.actual_amount),
        "withdraw_type": _normalize_text(order.withdraw_type),
        "withdraw_account": _normalize_text(order.withdraw_account),
        "status": _normalize_text(order.status),
        "transaction_id": _normalize_text(order.transaction_id),
        "remark": _normalize_text(order.remark),
        "processed_at": _serialize_datetime(order.processed_at),
        "created_at": _serialize_datetime(order.created_at),
        "updated_at": _serialize_datetime(order.updated_at),
    }
    if user is not None:
        payload.update(
            {
                "user_id": _normalize_text(user.user_id),
                "nickname": _normalize_text(user.nickname),
                "phone": _normalize_text(user.phone),
            }
        )
    return payload


def list_user_withdrawals(db: Session, *, user_pk: int, limit: int = 30) -> dict[str, Any]:
    safe_limit = min(max(int(limit or 30), 1), 100)
    rows = db.scalars(
        select(WithdrawalOrder)
        .where(WithdrawalOrder.user_pk == int(user_pk))
        .order_by(WithdrawalOrder.created_at.desc(), WithdrawalOrder.id.desc())
        .limit(safe_limit)
    ).all()
    return {"items": [_serialize_withdrawal(item) for item in rows]}


def list_admin_split_transactions(
    db: Session,
    *,
    keyword: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = min(max(int(page_size or 20), 1), 100)
    offset = (safe_page - 1) * safe_page_size
    normalized_keyword = _normalize_text(keyword)
    normalized_status = _normalize_lower(status)
    payer = aliased(User)
    receiver = aliased(User)

    where_conditions = [SplitTransaction.biz_type == BIZ_CIRCLE_JOIN]
    if normalized_status:
        where_conditions.append(SplitTransaction.split_status == normalized_status)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                SplitTransaction.order_no.like(pattern),
                payer.user_id.like(pattern),
                payer.nickname.like(pattern),
                receiver.user_id.like(pattern),
                receiver.nickname.like(pattern),
            )
        )

    stmt = (
        select(SplitTransaction, payer, receiver, CircleJoinRequest, Circle)
        .join(payer, payer.id == SplitTransaction.split_from_user_pk)
        .join(receiver, receiver.id == SplitTransaction.split_to_user_pk)
        .outerjoin(CircleJoinRequest, CircleJoinRequest.order_no == SplitTransaction.order_no)
        .outerjoin(Circle, Circle.circle_code == CircleJoinRequest.circle_code)
        .where(*where_conditions)
        .order_by(SplitTransaction.created_at.desc(), SplitTransaction.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    )
    rows = db.execute(stmt).all()
    total = int(
        db.scalar(
            select(func.count(SplitTransaction.id))
            .select_from(SplitTransaction)
            .join(payer, payer.id == SplitTransaction.split_from_user_pk)
            .join(receiver, receiver.id == SplitTransaction.split_to_user_pk)
            .where(*where_conditions)
        )
        or 0
    )

    return {
        "items": [
            {
                "id": int(item.id),
                "order_no": _normalize_text(item.order_no),
                "biz_type": _normalize_text(item.biz_type),
                "circle_code": _normalize_text(join_request.circle_code if join_request else ""),
                "circle_name": _normalize_text(circle.name if circle else ""),
                "payer_user_id": _normalize_text(payer_user.user_id),
                "payer_nickname": _normalize_text(payer_user.nickname),
                "receiver_user_id": _normalize_text(receiver_user.user_id),
                "receiver_nickname": _normalize_text(receiver_user.nickname),
                "total_amount": _serialize_decimal(item.total_amount),
                "platform_fee": _serialize_decimal(item.platform_fee),
                "split_amount": _serialize_decimal(item.split_amount),
                "split_status": _normalize_text(item.split_status),
                "external_transaction_id": _normalize_text(item.external_transaction_id),
                "external_order_no": _normalize_text(item.external_order_no),
                "external_status": _normalize_text(item.external_status),
                "external_error": _normalize_text(item.external_error),
                "executed_at": _serialize_datetime(item.executed_at),
                "created_at": _serialize_datetime(item.created_at),
                "remark": _normalize_text(item.remark),
            }
            for item, payer_user, receiver_user, join_request, circle in rows
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def retry_admin_split_transaction(db: Session, *, split_id: int) -> dict[str, Any]:
    row = db.scalar(select(SplitTransaction).where(SplitTransaction.id == int(split_id)).limit(1))
    if row is None:
        raise BusinessException(message="分账订单不存在", code=4641, status_code=404)
    if row.split_status in {STATUS_SUCCESS, STATUS_CANCELLED, STATUS_RETURNED}:
        raise BusinessException(message="当前分账状态不允许重试", code=4642, status_code=409)

    join_request = db.scalar(select(CircleJoinRequest).where(CircleJoinRequest.order_no == row.order_no).limit(1))
    if join_request is None:
        raise BusinessException(message="入圈申请不存在，无法重试分账", code=4643, status_code=404)
    circle = db.scalar(select(Circle).where(Circle.circle_code == join_request.circle_code).limit(1))
    if circle is None:
        raise BusinessException(message="圈子不存在，无法重试分账", code=4644, status_code=404)

    result = settle_circle_join_split(db, join_request=join_request, circle=circle)
    db.commit()
    if result is None:
        raise BusinessException(message="该订单无需分账", code=4645, status_code=409)
    return {
        "id": int(result.id),
        "order_no": _normalize_text(result.order_no),
        "split_status": _normalize_text(result.split_status),
        "external_status": _normalize_text(result.external_status),
        "external_error": _normalize_text(result.external_error),
        "executed_at": _serialize_datetime(result.executed_at),
    }


def list_admin_settlement_accounts(
    db: Session,
    *,
    keyword: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = min(max(int(page_size or 20), 1), 100)
    offset = (safe_page - 1) * safe_page_size
    normalized_keyword = _normalize_text(keyword)

    where_conditions = []
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                User.user_id.like(pattern),
                User.nickname.like(pattern),
                User.phone.like(pattern),
            )
        )
    rows = db.execute(
        select(UserSettlement, User)
        .join(User, User.id == UserSettlement.user_pk)
        .where(*where_conditions)
        .order_by(UserSettlement.total_income.desc(), UserSettlement.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).all()
    total = int(
        db.scalar(
            select(func.count(UserSettlement.id))
            .select_from(UserSettlement)
            .join(User, User.id == UserSettlement.user_pk)
            .where(*where_conditions)
        )
        or 0
    )
    return {
        "items": [
            {
                "id": int(account.id),
                "user_pk": int(user.id),
                "user_id": _normalize_text(user.user_id),
                "nickname": _normalize_text(user.nickname),
                "phone": _normalize_text(user.phone),
                "available_balance": _serialize_decimal(account.available_balance),
                "frozen_balance": _serialize_decimal(account.frozen_balance),
                "total_income": _serialize_decimal(account.total_income),
                "total_withdrawn": _serialize_decimal(account.total_withdrawn),
                "updated_at": _serialize_datetime(account.updated_at),
            }
            for account, user in rows
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def list_admin_withdrawals(
    db: Session,
    *,
    keyword: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = min(max(int(page_size or 20), 1), 100)
    offset = (safe_page - 1) * safe_page_size
    normalized_keyword = _normalize_text(keyword)
    normalized_status = _normalize_lower(status)

    where_conditions = []
    if normalized_status:
        where_conditions.append(WithdrawalOrder.status == normalized_status)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                WithdrawalOrder.order_no.like(pattern),
                User.user_id.like(pattern),
                User.nickname.like(pattern),
                User.phone.like(pattern),
            )
        )
    rows = db.execute(
        select(WithdrawalOrder, User)
        .join(User, User.id == WithdrawalOrder.user_pk)
        .where(*where_conditions)
        .order_by(WithdrawalOrder.created_at.desc(), WithdrawalOrder.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).all()
    total = int(
        db.scalar(
            select(func.count(WithdrawalOrder.id))
            .select_from(WithdrawalOrder)
            .join(User, User.id == WithdrawalOrder.user_pk)
            .where(*where_conditions)
        )
        or 0
    )
    return {
        "items": [_serialize_withdrawal(order, user) for order, user in rows],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def review_admin_withdrawal(
    db: Session,
    *,
    withdrawal_id: int,
    action: str,
    transaction_id: str | None = None,
    remark: str | None = None,
) -> dict[str, Any]:
    order = db.scalar(
        select(WithdrawalOrder).where(WithdrawalOrder.id == int(withdrawal_id)).with_for_update().limit(1)
    )
    if order is None:
        raise BusinessException(message="提现订单不存在", code=4654, status_code=404)
    if order.status != WITHDRAWAL_PENDING:
        raise BusinessException(message="当前提现状态不允许审核", code=4655, status_code=409)
    account = _ensure_settlement(db, user_pk=int(order.user_pk))
    amount = _money(order.amount)
    if _money(account.frozen_balance) < amount:
        raise BusinessException(message="冻结余额不足，请人工核对账目", code=4656, status_code=409)

    normalized_action = _normalize_lower(action)
    if normalized_action == "approve":
        account.frozen_balance = _money(account.frozen_balance) - amount
        account.total_withdrawn = _money(account.total_withdrawn) + amount
        order.status = WITHDRAWAL_SUCCESS
        order.transaction_id = _normalize_text(transaction_id) or None
        order.remark = _normalize_text(remark) or "后台确认已人工打款"
        order.processed_at = _now()
        _record_ledger(
            db,
            user_pk=int(order.user_pk),
            change_amount=Decimal("0.00"),
            account=account,
            biz_type="withdrawal_success",
            biz_key=order.order_no,
            title="提现成功",
            remark=order.remark,
        )
    elif normalized_action == "reject":
        account.frozen_balance = _money(account.frozen_balance) - amount
        account.available_balance = _money(account.available_balance) + amount
        order.status = WITHDRAWAL_FAILED
        order.remark = _normalize_text(remark) or "提现已驳回，金额退回余额"
        order.processed_at = _now()
        _record_ledger(
            db,
            user_pk=int(order.user_pk),
            change_amount=amount,
            account=account,
            biz_type="withdrawal_reject",
            biz_key=order.order_no,
            title="提现退回",
            remark=order.remark,
        )
    else:
        raise BusinessException(message="提现审核动作无效", code=4657, status_code=400)

    db.commit()
    db.refresh(order)
    return _serialize_withdrawal(order)
