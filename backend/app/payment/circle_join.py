from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.crud import create_wallet_transaction, ensure_user_wallet, get_user_by_id
from app.models.circle import Circle
from app.models.circle_join_request import CircleJoinRequest
from app.models.notification import Notification
from app.models.user_circle_membership import UserCircleMembership
from app.payment.service import (
    PAY_CHANNEL_MOCK,
    PAY_CHANNEL_WALLET,
    PAY_CHANNEL_WXPAY,
    _dict_to_xml,
    _prepare_wxpay_params,
    _resolve_payment_options,
    _sign_wechat_v2,
    _verify_wechat_v2_sign,
    _xml_to_dict,
)

PAYMENT_UNPAID = "unpaid"
PAYMENT_PENDING = "pending"
PAYMENT_PAID = "paid"
PAYMENT_REFUNDED = "refunded"
REFUND_NONE = "none"
REFUND_SUCCESS = "success"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _next_business_deadline(start: datetime) -> datetime:
    deadline = start + timedelta(days=1)
    while deadline.weekday() >= 5:
        deadline += timedelta(days=1)
    return deadline


def _generate_order_no() -> str:
    return f"J{_now().strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


def _get_request_by_order(db: Session, order_no: str) -> CircleJoinRequest | None:
    return db.scalar(
        select(CircleJoinRequest).where(CircleJoinRequest.order_no == str(order_no or "").strip())
    )


def _serialize(join_request: CircleJoinRequest) -> dict:
    return {
        "request_id": int(join_request.id),
        "circle_code": str(join_request.circle_code),
        "status": str(join_request.status),
        "order_no": str(join_request.order_no or ""),
        "amount": float(Decimal(str(join_request.amount or 0)).quantize(Decimal("0.01"))),
        "pay_channel": str(join_request.pay_channel or ""),
        "payment_status": str(join_request.payment_status or PAYMENT_UNPAID),
        "refund_status": str(join_request.refund_status or REFUND_NONE),
        "paid": str(join_request.payment_status or "") == PAYMENT_PAID,
        "paid_at": join_request.paid_at.isoformat() if join_request.paid_at else None,
        "auto_approve_at": join_request.auto_approve_at.isoformat() if join_request.auto_approve_at else None,
    }


def _notify_owner(db: Session, *, circle: Circle, join_request: CircleJoinRequest, nickname: str) -> None:
    db.add(
        Notification(
            user_pk=int(circle.owner_user_pk),
            type="circle",
            title="新的入圈申请",
            content=f"{nickname or '一位用户'}已支付入圈费用，申请加入“{circle.name}”",
            link_type="circle_join_request",
            link_id=str(join_request.id or ""),
            is_read=False,
        )
    )


def _add_membership(db: Session, join_request: CircleJoinRequest, circle: Circle) -> None:
    membership = db.scalar(
        select(UserCircleMembership).where(
            UserCircleMembership.user_pk == join_request.user_pk,
            UserCircleMembership.circle_code == join_request.circle_code,
        )
    )
    if membership is None:
        db.add(
            UserCircleMembership(
                user_pk=join_request.user_pk,
                circle_code=join_request.circle_code,
                is_active=True,
            )
        )
        circle.member_count = int(circle.member_count or 0) + 1
    elif not membership.is_active:
        membership.is_active = True
        circle.member_count = int(circle.member_count or 0) + 1


def approve_join_request(
    db: Session,
    *,
    join_request: CircleJoinRequest,
    circle: Circle,
    automatic: bool = False,
) -> None:
    if str(join_request.status) != "pending":
        return
    if Decimal(str(join_request.amount or 0)) > 0 and str(join_request.payment_status) != PAYMENT_PAID:
        raise BusinessException(message="入圈费用尚未支付", code=4385, status_code=409)
    _add_membership(db, join_request, circle)
    join_request.status = "approved"
    join_request.reviewed_at = _now()
    if automatic:
        join_request.message = str(join_request.message or "").strip() or "圈主未在1个工作日内处理，系统已自动通过"


def create_circle_join_payment(
    db: Session,
    *,
    user_pk: int,
    circle_code: str,
    message: str = "",
    pay_channel: str | None = None,
    client_ip: str | None = None,
    base_url: str | None = None,
) -> dict:
    circle = db.scalar(select(Circle).where(Circle.circle_code == circle_code))
    if circle is None:
        raise BusinessException(message="圈子不存在", code=4043, status_code=404)
    if int(circle.owner_user_pk) == int(user_pk):
        raise BusinessException(message="圈主无需申请加入自己的圈子", code=4380, status_code=409)

    membership = db.scalar(
        select(UserCircleMembership).where(
            UserCircleMembership.user_pk == user_pk,
            UserCircleMembership.circle_code == circle_code,
            UserCircleMembership.is_active.is_(True),
        )
    )
    if membership is not None:
        raise BusinessException(message="您已经是圈子成员", code=4381, status_code=409)

    user = get_user_by_id(db=db, user_id=user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    join_request = db.scalar(
        select(CircleJoinRequest).where(
            CircleJoinRequest.user_pk == user_pk,
            CircleJoinRequest.circle_code == circle_code,
        )
    )
    if join_request is not None and join_request.status == "pending":
        if join_request.payment_status == PAYMENT_PAID:
            return {"action": "already_paid", **_serialize(join_request)}

    amount = Decimal(str(circle.join_price or 0)).quantize(Decimal("0.01"))
    now = _now()
    order_no = _generate_order_no()
    payment_options = _resolve_payment_options(db=db)
    enabled = {str(item["key"]): bool(item["enabled"]) for item in payment_options["channels"]}
    channel = str(pay_channel or payment_options["default_channel"]).strip().lower()
    if channel not in enabled or not enabled[channel]:
        raise BusinessException(message="当前支付方式不可用", code=4383, status_code=400)

    if join_request is None:
        join_request = CircleJoinRequest(user_pk=user_pk, circle_code=circle_code)
        db.add(join_request)

    join_request.status = "pending"
    join_request.message = str(message or "").strip() or None
    join_request.reject_reason = None
    join_request.reviewed_at = None
    join_request.order_no = order_no
    join_request.amount = amount
    join_request.pay_channel = channel if amount > 0 else "free"
    join_request.payment_status = PAYMENT_UNPAID
    join_request.transaction_id = None
    join_request.refund_status = REFUND_NONE
    join_request.refunded_at = None
    join_request.paid_at = None
    join_request.auto_approve_at = None

    if amount <= 0:
        join_request.payment_status = PAYMENT_PAID
        join_request.paid_at = now
        join_request.auto_approve_at = _next_business_deadline(now)
        db.commit()
        db.refresh(join_request)
        _notify_owner(db, circle=circle, join_request=join_request, nickname=str(user.nickname or ""))
        db.commit()
        return {"action": "free_submitted", **_serialize(join_request)}

    wallet = ensure_user_wallet(db=db, user_pk=user_pk, default_balance=user.balance or 0)
    wallet_balance = Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))
    if channel == PAY_CHANNEL_WALLET and wallet_balance < amount:
        if enabled.get(PAY_CHANNEL_WXPAY):
            channel = PAY_CHANNEL_WXPAY
            join_request.pay_channel = channel
        else:
            raise BusinessException(message="钱包余额不足", code=4384, status_code=400)

    if channel == PAY_CHANNEL_WALLET:
        wallet.balance = (wallet_balance - amount).quantize(Decimal("0.01"))
        join_request.payment_status = PAYMENT_PAID
        join_request.paid_at = now
        join_request.auto_approve_at = _next_business_deadline(now)
        create_wallet_transaction(
            db=db,
            user_pk=user_pk,
            change_amount=-amount,
            balance_after=wallet.balance,
            biz_type="circle_join",
            biz_key=order_no,
            title=f"加入圈子-{circle.name}",
            remark=f"圈子编号: {circle_code}",
        )
        db.flush()
        _notify_owner(db, circle=circle, join_request=join_request, nickname=str(user.nickname or ""))
        db.commit()
        db.refresh(join_request)
        return {
            "action": "wallet_paid",
            "wallet_balance": float(wallet.balance),
            **_serialize(join_request),
        }

    if channel == PAY_CHANNEL_MOCK:
        join_request.payment_status = PAYMENT_PAID
        join_request.paid_at = now
        join_request.auto_approve_at = _next_business_deadline(now)
        db.flush()
        _notify_owner(db, circle=circle, join_request=join_request, nickname=str(user.nickname or ""))
        db.commit()
        db.refresh(join_request)
        return {"action": "mock_paid", **_serialize(join_request)}

    if channel != PAY_CHANNEL_WXPAY:
        raise BusinessException(message="当前支付方式不支持", code=4386, status_code=400)
    if not user.wechat_openid:
        raise BusinessException(message="请先绑定微信账号", code=4387, status_code=400)

    notify_url = str(settings.WECHAT_PAY_NOTIFY_URL or "").strip()
    if not notify_url and base_url:
        notify_url = f"{str(base_url).rstrip('/')}/api/v1/payment/wechat/notify"
    wxpay = _prepare_wxpay_params(
        user_openid=str(user.wechat_openid),
        order_no=order_no,
        amount_yuan=amount,
        plan_name=f"加入圈子-{circle.name}",
        client_ip=client_ip or "127.0.0.1",
        notify_url=notify_url,
    )
    join_request.payment_status = PAYMENT_PENDING
    db.commit()
    db.refresh(join_request)
    return {"action": "wxpay_required", "wxpay": wxpay, **_serialize(join_request)}


def confirm_circle_join_payment(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
    transaction_id: str | None = None,
) -> dict:
    join_request = _get_request_by_order(db, order_no)
    if join_request is None or int(join_request.user_pk) != int(user_pk):
        raise BusinessException(message="入圈订单不存在", code=4388, status_code=404)
    if join_request.payment_status == PAYMENT_PAID:
        return _serialize(join_request)
    if join_request.payment_status != PAYMENT_PENDING:
        raise BusinessException(message="入圈订单状态异常", code=4389, status_code=409)
    now = _now()
    join_request.payment_status = PAYMENT_PAID
    join_request.transaction_id = str(transaction_id or "").strip() or None
    join_request.paid_at = now
    join_request.auto_approve_at = _next_business_deadline(now)
    circle = db.scalar(select(Circle).where(Circle.circle_code == join_request.circle_code))
    user = get_user_by_id(db=db, user_id=user_pk)
    if circle is not None:
        _notify_owner(
            db,
            circle=circle,
            join_request=join_request,
            nickname=str(user.nickname or "") if user else "",
        )
    db.commit()
    db.refresh(join_request)
    return _serialize(join_request)


def get_circle_join_order(db: Session, *, user_pk: int, order_no: str) -> dict:
    join_request = _get_request_by_order(db, order_no)
    if join_request is None or int(join_request.user_pk) != int(user_pk):
        raise BusinessException(message="入圈订单不存在", code=4388, status_code=404)
    return _serialize(join_request)


def _wechat_refund(join_request: CircleJoinRequest) -> None:
    cert_path = str(settings.WECHAT_PAY_CERT_PATH or "").strip()
    key_path = str(settings.WECHAT_PAY_KEY_PATH or "").strip()
    if not cert_path or not key_path:
        raise BusinessException(message="微信退款证书未配置，暂不能拒绝该申请", code=4390, status_code=503)
    amount_fen = int((Decimal(str(join_request.amount or 0)) * 100).quantize(Decimal("1")))
    params = {
        "appid": str(settings.WECHAT_PAY_APP_ID or settings.WECHAT_MINI_APP_ID).strip(),
        "mch_id": str(settings.WECHAT_PAY_MCH_ID or "").strip(),
        "nonce_str": token_hex(12),
        "out_trade_no": str(join_request.order_no),
        "out_refund_no": f"RF{str(join_request.order_no)}",
        "total_fee": str(amount_fen),
        "refund_fee": str(amount_fen),
    }
    params["sign"] = _sign_wechat_v2(params, str(settings.WECHAT_PAY_API_V2_KEY or "").strip())
    context = ssl.create_default_context()
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    request = urllib.request.Request(
        str(settings.WECHAT_PAY_REFUND_URL),
        data=_dict_to_xml(params).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/xml; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15, context=context) as response:  # noqa: S310
            result = _xml_to_dict(response.read().decode("utf-8", errors="ignore"))
    except (OSError, urllib.error.URLError) as exc:
        raise BusinessException(message="微信退款请求失败，请稍后重试", code=4391, status_code=502) from exc
    if result.get("return_code") != "SUCCESS" or result.get("result_code") != "SUCCESS":
        raise BusinessException(
            message=f"微信退款失败：{result.get('err_code_des') or result.get('return_msg') or 'unknown'}",
            code=4392,
            status_code=502,
        )


def refund_circle_join_payment(
    db: Session,
    *,
    join_request: CircleJoinRequest,
    circle: Circle,
    reason: str = "圈主拒绝申请",
) -> None:
    if join_request.payment_status != PAYMENT_PAID:
        return
    amount = Decimal(str(join_request.amount or 0)).quantize(Decimal("0.01"))
    channel = str(join_request.pay_channel or "")
    if amount > 0 and channel == PAY_CHANNEL_WALLET:
        wallet = ensure_user_wallet(db=db, user_pk=join_request.user_pk, default_balance=0)
        wallet.balance = (Decimal(str(wallet.balance or 0)) + amount).quantize(Decimal("0.01"))
        create_wallet_transaction(
            db=db,
            user_pk=join_request.user_pk,
            change_amount=amount,
            balance_after=wallet.balance,
            biz_type="circle_join_refund",
            biz_key=str(join_request.order_no),
            title=f"入圈费用退款-{circle.name}",
            remark=f"{reason}，圈子编号: {circle.circle_code}",
        )
    elif amount > 0 and channel == PAY_CHANNEL_WXPAY:
        _wechat_refund(join_request)
    join_request.payment_status = PAYMENT_REFUNDED
    join_request.refund_status = REFUND_SUCCESS
    join_request.refunded_at = _now()


def handle_circle_join_wechat_notify(db: Session, *, payload: dict[str, str]) -> tuple[bool, str]:
    if not _verify_wechat_v2_sign(payload, str(settings.WECHAT_PAY_API_V2_KEY or "").strip()):
        return False, "INVALID_SIGN"
    order_no = str(payload.get("out_trade_no") or "").strip()
    join_request = _get_request_by_order(db, order_no)
    if join_request is None:
        return False, "ORDER_NOT_FOUND"
    if payload.get("return_code") != "SUCCESS" or payload.get("result_code") != "SUCCESS":
        return True, "OK"
    expected = int((Decimal(str(join_request.amount or 0)) * 100).quantize(Decimal("1")))
    if str(payload.get("total_fee") or "") != str(expected):
        return False, "TOTAL_FEE_MISMATCH"
    if join_request.payment_status != PAYMENT_PAID:
        now = _now()
        join_request.payment_status = PAYMENT_PAID
        join_request.transaction_id = str(payload.get("transaction_id") or "").strip() or None
        join_request.paid_at = now
        join_request.auto_approve_at = _next_business_deadline(now)
        circle = db.scalar(select(Circle).where(Circle.circle_code == join_request.circle_code))
        user = get_user_by_id(db=db, user_id=join_request.user_pk)
        if circle is not None:
            _notify_owner(
                db,
                circle=circle,
                join_request=join_request,
                nickname=str(user.nickname or "") if user else "",
            )
        db.commit()
    return True, "OK"


def auto_approve_due_circle_joins(db: Session) -> int:
    now = _now()
    rows = db.scalars(
        select(CircleJoinRequest).where(
            CircleJoinRequest.status == "pending",
            CircleJoinRequest.payment_status == PAYMENT_PAID,
            CircleJoinRequest.auto_approve_at.is_not(None),
            CircleJoinRequest.auto_approve_at <= now,
        )
    ).all()
    count = 0
    for join_request in rows:
        circle = db.scalar(select(Circle).where(Circle.circle_code == join_request.circle_code))
        if circle is None:
            continue
        approve_join_request(db, join_request=join_request, circle=circle, automatic=True)
        db.add(
            Notification(
                user_pk=int(join_request.user_pk),
                type="circle",
                title="已自动加入圈子",
                content=f"圈主在1个工作日内未处理，系统已自动通过您加入“{circle.name}”的申请",
                link_type="circle",
                link_id=str(circle.circle_code),
                is_read=False,
            )
        )
        count += 1
    if count:
        db.commit()
    return count
