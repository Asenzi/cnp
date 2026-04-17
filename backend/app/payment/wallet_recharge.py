from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.crud import ensure_user_wallet, get_sys_config_values, get_user_by_id
from app.models.wallet_recharge_order import WalletRechargeOrder
from app.payment.service import (
    PAY_CHANNEL_WXPAY,
    _prepare_wxpay_params,
    _resolve_pay_app_id,
    _verify_wechat_v2_sign,
    _xml_to_dict,
    handle_wechat_pay_notify_xml as _handle_member_wechat_pay_notify_xml,
)

ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_FAILED = "failed"

PAY_CHANNEL_MOCK = "mock"


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _generate_recharge_order_no() -> str:
    return f"R{_utc_now_naive().strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


def _to_decimal_amount(value: object, *, field_name: str = "amount") -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001
        raise BusinessException(message=f"{field_name} 格式错误", code=4561, status_code=400) from exc
    amount = amount.quantize(Decimal("0.01"))
    if amount <= Decimal("0.00"):
        raise BusinessException(message="充值金额必须大于 0", code=4562, status_code=400)
    if amount > Decimal("200000.00"):
        raise BusinessException(message="单笔充值金额超出限制", code=4563, status_code=400)
    return amount


def _to_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "active"}:
            return True
        if normalized in {"0", "false", "no", "off", "inactive"}:
            return False
    return default


def _is_wallet_recharge_schema_missing(exc: Exception) -> bool:
    message = str(exc or "").lower()
    if "wallet_recharge_orders" not in message:
        return False
    return ("doesn't exist" in message) or ("does not exist" in message) or ("unknown column" in message)


def _resolve_recharge_payment_options(db: Session) -> dict:
    config_values = get_sys_config_values(
        db=db,
        config_keys={
            "wallet.recharge.default_channel",
            "wallet.recharge.wxpay_enabled",
            "wallet.recharge.mock_enabled",
        },
    )
    app_id_ready = bool(_resolve_pay_app_id())
    merchant_ready = bool(str(settings.WECHAT_PAY_MCH_ID or "").strip() and str(settings.WECHAT_PAY_API_V2_KEY or "").strip())
    wxpay_enabled_by_config = _to_bool(config_values.get("wallet.recharge.wxpay_enabled"), settings.WECHAT_PAY_ENABLED)
    wxpay_enabled = bool(wxpay_enabled_by_config and app_id_ready and merchant_ready)
    mock_enabled = _to_bool(config_values.get("wallet.recharge.mock_enabled"), True)

    channels = [
        {
            "key": PAY_CHANNEL_WXPAY,
            "label": "微信支付",
            "enabled": wxpay_enabled,
        },
        {
            "key": PAY_CHANNEL_MOCK,
            "label": "模拟支付",
            "enabled": mock_enabled,
        },
    ]
    enabled_channel_keys = [item["key"] for item in channels if item["enabled"]]
    if not enabled_channel_keys:
        channels[1]["enabled"] = True
        enabled_channel_keys = [PAY_CHANNEL_MOCK]

    default_channel = str(config_values.get("wallet.recharge.default_channel") or PAY_CHANNEL_WXPAY).strip().lower()
    if default_channel not in enabled_channel_keys:
        default_channel = enabled_channel_keys[0]

    return {
        "default_channel": default_channel,
        "channels": channels,
    }


def _get_recharge_order_by_order_no(db: Session, *, order_no: str) -> WalletRechargeOrder | None:
    stmt = select(WalletRechargeOrder).where(WalletRechargeOrder.order_no == order_no)
    return db.execute(stmt).scalar_one_or_none()


def _serialize_recharge_order(order: WalletRechargeOrder) -> dict:
    return {
        "id": int(order.id),
        "order_no": str(order.order_no),
        "amount": float(Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))),
        "pay_channel": str(order.pay_channel or ""),
        "status": str(order.status or ""),
        "transaction_id": str(order.transaction_id or ""),
        "remark": str(order.remark or ""),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


def _confirm_paid_recharge_order(
    db: Session,
    *,
    order: WalletRechargeOrder,
    transaction_id: str | None = None,
    ext_payload: dict | None = None,
) -> dict:
    status = str(order.status or "").strip().lower()
    wallet = ensure_user_wallet(db=db, user_pk=int(order.user_pk), default_balance=0)

    if status == ORDER_STATUS_PAID:
        return {
            "order_no": str(order.order_no),
            "already_paid": True,
            "wallet_balance": float(Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))),
        }

    if status != ORDER_STATUS_PENDING:
        raise BusinessException(message="充值订单状态异常，无法确认", code=4570, status_code=400)

    now = _utc_now_naive()
    recharge_amount = Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))
    wallet_balance = Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))
    wallet.balance = (wallet_balance + recharge_amount).quantize(Decimal("0.01"))

    order.status = ORDER_STATUS_PAID
    order.paid_at = now
    order.transaction_id = str(transaction_id or "").strip()[:64] or None
    ext = ext_payload if isinstance(ext_payload, dict) else {}
    if order.transaction_id:
        ext["transaction_id"] = order.transaction_id
    if ext:
        order.remark = json.dumps(ext, ensure_ascii=False)[:4000]
    db.add(order)
    db.add(wallet)
    db.commit()
    db.refresh(order)
    db.refresh(wallet)

    return {
        "order_no": str(order.order_no),
        "already_paid": False,
        "wallet_balance": float(Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))),
    }


def create_wallet_recharge(
    db: Session,
    *,
    user_pk: int,
    amount: Decimal | int | float | str,
    pay_channel: str | None = None,
    request_client_ip: str | None = None,
    request_base_url: str | None = None,
) -> dict:
    user = get_user_by_id(db=db, user_id=user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    recharge_amount = _to_decimal_amount(amount)

    try:
        payment_options = _resolve_recharge_payment_options(db=db)
        enabled_channels = {
            str(item["key"]): bool(item["enabled"]) for item in payment_options["channels"]
        }
        normalized_pay_channel = str(pay_channel or payment_options["default_channel"]).strip().lower()
        if normalized_pay_channel not in enabled_channels or not enabled_channels[normalized_pay_channel]:
            raise BusinessException(message="当前充值支付方式不可用", code=4564, status_code=400)

        now = _utc_now_naive()
        order_no = _generate_recharge_order_no()

        if normalized_pay_channel == PAY_CHANNEL_MOCK:
            order = WalletRechargeOrder(
                order_no=order_no,
                user_pk=user_pk,
                amount=recharge_amount,
                pay_channel=PAY_CHANNEL_MOCK,
                status=ORDER_STATUS_PENDING,
                remark="wallet recharge by mock",
            )
            db.add(order)
            db.flush()
            confirm_result = _confirm_paid_recharge_order(
                db=db,
                order=order,
                transaction_id=f"mock_{order_no}",
                ext_payload={"source": "mock"},
            )
            return {
                "action": "mock_paid",
                "order_no": str(order_no),
                "paid_amount": float(recharge_amount),
                "pay_channel": PAY_CHANNEL_MOCK,
                "wallet_balance": confirm_result["wallet_balance"],
            }

        if normalized_pay_channel != PAY_CHANNEL_WXPAY:
            raise BusinessException(message="当前充值支付方式不支持", code=4565, status_code=400)

        openid = str(user.wechat_openid or "").strip()
        if not openid:
            raise BusinessException(message="请先绑定微信账号后再发起充值", code=4566, status_code=400)

        if request_base_url:
            fallback_notify_url = f"{str(request_base_url).rstrip('/')}/api/v1/payment/wechat/notify"
        else:
            fallback_notify_url = ""
        notify_url = str(settings.WECHAT_PAY_NOTIFY_URL or "").strip() or fallback_notify_url
        if not notify_url:
            raise BusinessException(message="微信支付回调地址未配置", code=4567, status_code=500)

        wxpay_params = _prepare_wxpay_params(
            user_openid=openid,
            order_no=order_no,
            amount_yuan=recharge_amount,
            plan_name=f"钱包充值{recharge_amount}",
            client_ip=request_client_ip,
            notify_url=notify_url,
        )
        order = WalletRechargeOrder(
            order_no=order_no,
            user_pk=user_pk,
            amount=recharge_amount,
            pay_channel=PAY_CHANNEL_WXPAY,
            status=ORDER_STATUS_PENDING,
            remark=f"wallet recharge by wxpay at {now.isoformat()}",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return {
            "action": "wxpay_required",
            "order_no": str(order.order_no),
            "paid_amount": float(recharge_amount),
            "pay_channel": str(order.pay_channel),
            "need_confirm": True,
            "wxpay": wxpay_params,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        if _is_wallet_recharge_schema_missing(exc):
            raise BusinessException(
                message="充值模块未初始化，请先执行数据库迁移",
                code=5565,
                status_code=500,
            ) from exc
        raise BusinessException(message="充值下单失败，请稍后重试", code=5561, status_code=500) from exc


def confirm_wallet_recharge_payment(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
    transaction_id: str | None = None,
    ext_payload: dict | None = None,
) -> dict:
    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        raise BusinessException(message="订单号不能为空", code=4571, status_code=400)

    try:
        order = _get_recharge_order_by_order_no(db=db, order_no=normalized_order_no)
        if order is None or int(order.user_pk) != int(user_pk):
            raise BusinessException(message="充值订单不存在", code=4572, status_code=404)
        return _confirm_paid_recharge_order(
            db=db,
            order=order,
            transaction_id=transaction_id,
            ext_payload=ext_payload,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        if _is_wallet_recharge_schema_missing(exc):
            raise BusinessException(
                message="充值模块未初始化，请先执行数据库迁移",
                code=5565,
                status_code=500,
            ) from exc
        raise BusinessException(message="充值确认失败，请稍后重试", code=5562, status_code=500) from exc


def get_wallet_recharge_status(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
) -> dict:
    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        raise BusinessException(message="订单号不能为空", code=4581, status_code=400)
    try:
        order = _get_recharge_order_by_order_no(db=db, order_no=normalized_order_no)
        if order is None or int(order.user_pk) != int(user_pk):
            raise BusinessException(message="充值订单不存在", code=4572, status_code=404)
        payload = _serialize_recharge_order(order)
        payload["paid"] = str(order.status or "").strip().lower() == ORDER_STATUS_PAID
        return payload
    except SQLAlchemyError as exc:
        if _is_wallet_recharge_schema_missing(exc):
            raise BusinessException(
                message="充值模块未初始化，请先执行数据库迁移",
                code=5565,
                status_code=500,
            ) from exc
        raise BusinessException(message="充值订单查询失败", code=5563, status_code=500) from exc


def list_wallet_recharge_orders(
    db: Session,
    *,
    user_pk: int,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    safe_limit = min(max(int(limit), 1), 50)
    stmt = select(WalletRechargeOrder).where(WalletRechargeOrder.user_pk == user_pk)

    normalized_cursor = str(cursor or "").strip()
    if normalized_cursor.isdigit():
        stmt = stmt.where(WalletRechargeOrder.id < int(normalized_cursor))

    stmt = stmt.order_by(WalletRechargeOrder.id.desc()).limit(safe_limit + 1)
    try:
        rows = db.execute(stmt).scalars().all()
    except SQLAlchemyError as exc:
        if _is_wallet_recharge_schema_missing(exc):
            return {
                "items": [],
                "cursor": normalized_cursor,
                "next_cursor": "",
                "has_more": False,
                "limit": safe_limit,
            }
        raise BusinessException(message="充值订单列表查询失败", code=5564, status_code=500) from exc

    has_more = len(rows) > safe_limit
    records = rows[:safe_limit]
    next_cursor = str(records[-1].id) if has_more and records else ""
    items = [_serialize_recharge_order(item) for item in records]
    return {
        "items": items,
        "cursor": normalized_cursor,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": safe_limit,
    }


def _handle_wallet_wechat_notify(
    db: Session,
    *,
    payload: dict[str, str],
) -> tuple[bool, str]:
    api_key = str(settings.WECHAT_PAY_API_V2_KEY or "").strip()
    if not _verify_wechat_v2_sign(payload, api_key=api_key):
        return False, "INVALID_SIGN"

    if str(payload.get("return_code") or "").strip().upper() != "SUCCESS":
        return False, str(payload.get("return_msg") or "RETURN_CODE_FAIL")

    out_trade_no = str(payload.get("out_trade_no") or "").strip()
    if not out_trade_no:
        return False, "MISSING_ORDER_NO"

    order = _get_recharge_order_by_order_no(db=db, order_no=out_trade_no)
    if order is None:
        return False, "ORDER_NOT_FOUND"

    if str(payload.get("result_code") or "").strip().upper() != "SUCCESS":
        if str(order.status or "").strip().lower() == ORDER_STATUS_PENDING:
            order.status = ORDER_STATUS_FAILED
            order.remark = json.dumps(
                {
                    "notify": payload,
                    "failed": True,
                    "err_code": payload.get("err_code"),
                    "err_code_des": payload.get("err_code_des"),
                },
                ensure_ascii=False,
            )[:4000]
            db.add(order)
            db.commit()
        return True, "OK"

    total_fee_text = str(payload.get("total_fee") or "").strip()
    if total_fee_text.isdigit():
        notify_total_fee = int(total_fee_text)
        order_total_fee = int((Decimal(str(order.amount or 0)) * Decimal("100")).quantize(Decimal("1")))
        if notify_total_fee != order_total_fee:
            return False, "TOTAL_FEE_MISMATCH"

    if str(order.pay_channel or "").strip().lower() != PAY_CHANNEL_WXPAY:
        return False, "PAY_CHANNEL_MISMATCH"

    try:
        _confirm_paid_recharge_order(
            db=db,
            order=order,
            transaction_id=str(payload.get("transaction_id") or "").strip(),
            ext_payload={"notify": payload, "source": "wechat_notify"},
        )
        return True, "OK"
    except BusinessException as exc:
        if exc.code == 4570:
            return True, "OK"
        return False, str(exc.message or "BIZ_FAIL")


def handle_wechat_pay_notify_xml(
    db: Session,
    *,
    raw_xml: str,
) -> tuple[bool, str]:
    xml_text = str(raw_xml or "").strip()
    if not xml_text:
        return False, "EMPTY_BODY"

    try:
        payload = _xml_to_dict(xml_text)
    except Exception:  # noqa: BLE001
        return False, "INVALID_XML"

    out_trade_no = str(payload.get("out_trade_no") or "").strip().upper()
    if out_trade_no.startswith("R"):
        try:
            return _handle_wallet_wechat_notify(db=db, payload=payload)
        except SQLAlchemyError:
            db.rollback()
            return False, "DB_ERROR"

    return _handle_member_wechat_pay_notify_xml(db=db, raw_xml=xml_text)
