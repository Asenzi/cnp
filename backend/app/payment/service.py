from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.crud import ensure_user_points_account, ensure_user_wallet, get_sys_config_values, get_user_by_id
from app.models.member_order import MemberOrder
from app.models.user_membership import UserMembership
from app.points import (
    POINTS_STATUS_NONE,
    POINTS_STATUS_RELEASED,
    POINTS_STATUS_RESERVED,
    POINTS_STATUS_SPENT,
    cleanup_expired_member_points_orders,
    consume_points_for_member_order,
    release_reserved_points_for_member_order,
    reserve_points_for_member_order,
    resolve_member_points_offer,
)

MEMBER_STATUS_ACTIVE = "active"
MEMBER_STATUS_INACTIVE = "inactive"

ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_FAILED = "failed"

PAY_CHANNEL_WALLET = "wallet"
PAY_CHANNEL_MOCK = "mock"
PAY_CHANNEL_WXPAY = "wxpay"

DEFAULT_MEMBER_BENEFITS = [
    {
        "key": "badge",
        "title": "专属身份标识",
        "desc": "彰显商务独特身份",
        "icon_path": "/static/me-icons/badge-blue.png",
        "icon_text": "",
        "wide": False,
    },
    {
        "key": "contact",
        "title": "解锁联系方式",
        "desc": "直接获取核心资源",
        "icon_path": "/static/me-icons/contact-page-primary.png",
        "icon_text": "",
        "wide": False,
    },
    {
        "key": "circle_discount",
        "title": "社群加入优惠",
        "desc": "低成本高效入圈",
        "icon_path": "/static/me-icons/corporate-primary.png",
        "icon_text": "",
        "wide": False,
    },
    {
        "key": "boost",
        "title": "展示权重提升",
        "desc": "曝光率大幅翻倍",
        "icon_path": "/static/me-icons/payments-green.png",
        "icon_text": "",
        "wide": False,
    },
    {
        "key": "support",
        "title": "优先技术支持",
        "desc": "专属客服，极速响应您的需求",
        "icon_path": "/static/me-icons/shield-person-primary.png",
        "icon_text": "",
        "wide": True,
    },
]

DEFAULT_MEMBER_PLANS = [
    {
        "id": "yearly",
        "name": "年度会员",
        "subtitle": "平均每天仅需 ¥0.54",
        "price": Decimal("198"),
        "original_price": Decimal("348"),
        "duration_days": 365,
        "recommended": True,
        "badge_text": "超值推荐 BEST VALUE",
        "sort": 1,
    },
    {
        "id": "quarterly",
        "name": "季度会员",
        "subtitle": "更灵活的商务选择",
        "price": Decimal("79"),
        "original_price": Decimal("87"),
        "duration_days": 90,
        "recommended": False,
        "badge_text": "热门方案",
        "sort": 2,
    },
    {
        "id": "monthly",
        "name": "月度会员",
        "subtitle": "抢先体验会员权益",
        "price": Decimal("29"),
        "original_price": Decimal("0"),
        "duration_days": 30,
        "recommended": False,
        "badge_text": "轻量体验",
        "sort": 3,
    },
]


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _to_decimal(value: object, default: Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed < 0:
        return default
    return parsed.quantize(Decimal("0.01"))


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


def _to_int(value: object, default: int, min_value: int = 1, max_value: int = 3650) -> int:
    try:
        parsed = int(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed < min_value:
        return min_value
    if parsed > max_value:
        return max_value
    return parsed


def _format_date(date_value: datetime | None) -> str:
    if date_value is None:
        return "--"
    return date_value.strftime("%Y-%m-%d")


def _generate_order_no() -> str:
    return f"M{_utc_now_naive().strftime('%Y%m%d%H%M%S')}{token_hex(3).upper()}"


def _generate_nonce(length: int = 24) -> str:
    return token_hex(max(8, length // 2))[:length]


def _xml_to_dict(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    result: dict[str, str] = {}
    for child in root:
        result[child.tag] = (child.text or "").strip()
    return result


def _dict_to_xml(data: dict[str, str]) -> str:
    root = ET.Element("xml")
    for key, value in data.items():
        node = ET.SubElement(root, key)
        node.text = str(value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _sign_wechat_v2(params: dict[str, str], api_key: str) -> str:
    pairs = []
    for key in sorted(params.keys()):
        value = str(params.get(key, "")).strip()
        if not value or key == "sign":
            continue
        pairs.append(f"{key}={value}")
    pairs.append(f"key={api_key}")
    sign_text = "&".join(pairs)
    return hashlib.md5(sign_text.encode("utf-8")).hexdigest().upper()


def _verify_wechat_v2_sign(params: dict[str, str], api_key: str) -> bool:
    if not api_key:
        return False
    sign = str(params.get("sign") or "").strip().upper()
    if not sign:
        return False
    calc = _sign_wechat_v2(params, api_key=api_key)
    return sign == calc


def _safe_client_ip(raw_ip: str | None) -> str:
    text = str(raw_ip or "").strip()
    if not text:
        return "127.0.0.1"
    if len(text) > 45:
        return "127.0.0.1"
    return text


def _resolve_pay_app_id() -> str:
    pay_app_id = str(settings.WECHAT_PAY_APP_ID or "").strip()
    if pay_app_id:
        return pay_app_id
    return str(settings.WECHAT_MINI_APP_ID or "").strip()


def _load_member_config_values(db: Session) -> dict[str, str]:
    config_keys: set[str] = {
        "member.payment.default_channel",
        "member.payment.wallet_enabled",
        "member.payment.mock_enabled",
        "member.payment.wxpay_enabled",
    }
    for plan in DEFAULT_MEMBER_PLANS:
        plan_id = str(plan["id"])
        prefix = f"member.plan.{plan_id}."
        config_keys.update(
            {
                f"{prefix}enabled",
                f"{prefix}name",
                f"{prefix}subtitle",
                f"{prefix}price",
                f"{prefix}original_price",
                f"{prefix}duration_days",
                f"{prefix}recommended",
                f"{prefix}badge_text",
                f"{prefix}sort",
            }
        )

    return get_sys_config_values(db=db, config_keys=config_keys)


def _serialize_plan(plan: dict, *, points_offer: dict | None = None) -> dict:
    payload = {
        "id": str(plan["id"]),
        "name": str(plan["name"]),
        "subtitle": str(plan["subtitle"]),
        "price": float(plan["price"]),
        "original_price": float(plan["original_price"]),
        "duration_days": int(plan["duration_days"]),
        "recommended": bool(plan["recommended"]),
        "badge_text": str(plan["badge_text"]),
    }
    if points_offer is not None:
        payload["points_offer"] = points_offer
    return payload


def _resolve_member_plans(db: Session) -> list[dict]:
    config_values = _load_member_config_values(db=db)
    plans: list[dict] = []

    for default in DEFAULT_MEMBER_PLANS:
        plan_id = str(default["id"])
        prefix = f"member.plan.{plan_id}."
        enabled = _to_bool(config_values.get(f"{prefix}enabled"), True)
        if not enabled:
            continue

        plan = {
            "id": plan_id,
            "name": str(config_values.get(f"{prefix}name") or default["name"]).strip() or str(default["name"]),
            "subtitle": str(config_values.get(f"{prefix}subtitle") or default["subtitle"]).strip(),
            "price": _to_decimal(config_values.get(f"{prefix}price"), default["price"]),
            "original_price": _to_decimal(config_values.get(f"{prefix}original_price"), default["original_price"]),
            "duration_days": _to_int(config_values.get(f"{prefix}duration_days"), int(default["duration_days"])),
            "recommended": _to_bool(config_values.get(f"{prefix}recommended"), bool(default["recommended"])),
            "badge_text": str(config_values.get(f"{prefix}badge_text") or default["badge_text"]).strip()
            or str(default["badge_text"]),
            "sort": _to_int(config_values.get(f"{prefix}sort"), int(default["sort"]), min_value=1, max_value=9999),
        }
        plans.append(plan)

    if not plans:
        plans = [dict(item) for item in DEFAULT_MEMBER_PLANS]

    plans.sort(key=lambda item: int(item["sort"]))
    if not any(bool(item["recommended"]) for item in plans):
        plans[0]["recommended"] = True
    return plans


def _resolve_payment_options(db: Session) -> dict:
    config_values = _load_member_config_values(db=db)
    wallet_enabled = _to_bool(config_values.get("member.payment.wallet_enabled"), True)
    mock_enabled = _to_bool(config_values.get("member.payment.mock_enabled"), True)
    wxpay_enabled_by_config = _to_bool(config_values.get("member.payment.wxpay_enabled"), settings.WECHAT_PAY_ENABLED)
    app_id_ready = bool(_resolve_pay_app_id())
    merchant_ready = bool(str(settings.WECHAT_PAY_MCH_ID or "").strip() and str(settings.WECHAT_PAY_API_V2_KEY or "").strip())
    wxpay_enabled = bool(wxpay_enabled_by_config and app_id_ready and merchant_ready)
    default_channel = str(config_values.get("member.payment.default_channel") or PAY_CHANNEL_WALLET).strip().lower()

    channels = [
        {
            "key": PAY_CHANNEL_WALLET,
            "label": "钱包余额支付",
            "enabled": wallet_enabled,
        },
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
    enabled_channels = [item["key"] for item in channels if item["enabled"]]
    if not enabled_channels:
        channels[0]["enabled"] = True
        enabled_channels = [PAY_CHANNEL_WALLET]

    if default_channel not in enabled_channels:
        default_channel = enabled_channels[0]

    return {
        "default_channel": default_channel,
        "channels": channels,
    }


def _get_membership(db: Session, *, user_pk: int) -> UserMembership | None:
    try:
        stmt = select(UserMembership).where(UserMembership.user_pk == user_pk)
        return db.execute(stmt).scalar_one_or_none()
    except SQLAlchemyError:
        return None


def _get_order_by_order_no(db: Session, *, order_no: str) -> MemberOrder | None:
    stmt = select(MemberOrder).where(MemberOrder.order_no == order_no)
    return db.execute(stmt).scalar_one_or_none()


def _upsert_membership_paid_order(
    db: Session,
    *,
    user_pk: int,
    plan_id: str,
    plan_name: str,
    duration_days: int,
    order_no: str,
    now: datetime,
) -> UserMembership:
    membership = _get_membership(db=db, user_pk=user_pk)
    start_from = now
    if (
        membership is not None
        and membership.status == MEMBER_STATUS_ACTIVE
        and membership.expire_at is not None
        and membership.expire_at > now
    ):
        start_from = membership.expire_at
    new_expire_at = start_from + timedelta(days=duration_days)

    if membership is None:
        membership = UserMembership(
            user_pk=user_pk,
            plan_id=plan_id,
            plan_name=plan_name,
            status=MEMBER_STATUS_ACTIVE,
            started_at=now,
            expire_at=new_expire_at,
            last_order_no=order_no,
        )
        db.add(membership)
    else:
        if not (
            membership.status == MEMBER_STATUS_ACTIVE
            and membership.expire_at is not None
            and membership.expire_at > now
        ):
            membership.started_at = now
        membership.plan_id = plan_id
        membership.plan_name = plan_name
        membership.status = MEMBER_STATUS_ACTIVE
        membership.expire_at = new_expire_at
        membership.last_order_no = order_no
        db.add(membership)
    return membership


def _prepare_wxpay_params(
    *,
    user_openid: str,
    order_no: str,
    amount_yuan: Decimal,
    plan_name: str,
    client_ip: str,
    notify_url: str,
) -> dict:
    app_id = _resolve_pay_app_id()
    mch_id = str(settings.WECHAT_PAY_MCH_ID or "").strip()
    api_key = str(settings.WECHAT_PAY_API_V2_KEY or "").strip()
    unifiedorder_url = str(settings.WECHAT_PAY_UNIFIEDORDER_URL or "").strip()
    if not app_id or not mch_id or not api_key:
        raise BusinessException(message="微信支付配置不完整", code=4520, status_code=500)
    if not unifiedorder_url:
        raise BusinessException(message="微信支付下单地址未配置", code=4521, status_code=500)

    total_fee_fen = int((amount_yuan * Decimal("100")).quantize(Decimal("1")))
    if total_fee_fen <= 0:
        raise BusinessException(message="支付金额无效", code=4522, status_code=400)

    nonce_str = _generate_nonce(24)
    req_params = {
        "appid": app_id,
        "mch_id": mch_id,
        "nonce_str": nonce_str,
        "body": f"圈脉链会员-{plan_name}"[:127],
        "out_trade_no": order_no,
        "total_fee": str(total_fee_fen),
        "spbill_create_ip": _safe_client_ip(client_ip),
        "notify_url": notify_url,
        "trade_type": "JSAPI",
        "openid": str(user_openid).strip(),
    }
    req_params["sign"] = _sign_wechat_v2(req_params, api_key=api_key)
    req_xml = _dict_to_xml(req_params).encode("utf-8")

    try:
        req = urllib.request.Request(
            url=unifiedorder_url,
            data=req_xml,
            method="POST",
            headers={"Content-Type": "application/xml; charset=utf-8"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:  # noqa: S310
            resp_xml = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        raise BusinessException(message="微信支付下单失败，请稍后重试", code=4523, status_code=502) from exc

    try:
        resp_data = _xml_to_dict(resp_xml)
    except Exception as exc:  # noqa: BLE001
        raise BusinessException(message="微信支付响应解析失败", code=4524, status_code=502) from exc

    if str(resp_data.get("return_code") or "").upper() != "SUCCESS":
        raise BusinessException(
            message=f"微信支付下单失败：{resp_data.get('return_msg') or 'unknown'}",
            code=4525,
            status_code=502,
        )
    if str(resp_data.get("result_code") or "").upper() != "SUCCESS":
        raise BusinessException(
            message=f"微信支付下单失败：{resp_data.get('err_code_des') or resp_data.get('err_code') or 'unknown'}",
            code=4526,
            status_code=502,
        )

    prepay_id = str(resp_data.get("prepay_id") or "").strip()
    if not prepay_id:
        raise BusinessException(message="微信支付预下单失败（缺少 prepay_id）", code=4527, status_code=502)

    pay_nonce_str = _generate_nonce(24)
    time_stamp = str(int(datetime.now(UTC).timestamp()))
    client_pay_params = {
        "appId": app_id,
        "timeStamp": time_stamp,
        "nonceStr": pay_nonce_str,
        "package": f"prepay_id={prepay_id}",
        "signType": "MD5",
    }
    client_pay_params["paySign"] = _sign_wechat_v2(client_pay_params, api_key=api_key)

    return {
        "timeStamp": client_pay_params["timeStamp"],
        "nonceStr": client_pay_params["nonceStr"],
        "package": client_pay_params["package"],
        "signType": client_pay_params["signType"],
        "paySign": client_pay_params["paySign"],
        "prepayId": prepay_id,
    }


def _confirm_paid_member_order(
    db: Session,
    *,
    order: MemberOrder,
    transaction_id: str | None = None,
    ext_payload: dict | None = None,
) -> dict:
    user_pk = int(order.user_pk)
    if str(order.status or "").strip().lower() == ORDER_STATUS_PAID:
        snapshot = resolve_member_snapshot(db=db, user_pk=user_pk)
        return {
            "order_no": str(order.order_no),
            "already_paid": True,
            "member_expire_at": snapshot["member_expire_at"],
            "member_expire_date_text": snapshot["expire_date_text"],
        }

    if str(order.status or "").strip().lower() != ORDER_STATUS_PENDING:
        raise BusinessException(message="订单状态异常，无法确认支付", code=4533, status_code=400)

    now = _utc_now_naive()
    points_cost = int(order.points_cost or 0)
    if bool(order.used_points_discount) and points_cost > 0:
        consume_points_for_member_order(
            db=db,
            user_pk=user_pk,
            order_no=str(order.order_no),
            points_cost=points_cost,
            plan_name=str(order.plan_name or ""),
            use_reserved_balance=str(order.points_status or "").strip().lower() == POINTS_STATUS_RESERVED,
            commit=False,
        )
        order.points_status = POINTS_STATUS_SPENT
    else:
        order.points_status = POINTS_STATUS_NONE

    order.status = ORDER_STATUS_PAID
    order.paid_at = now
    ext = ext_payload if isinstance(ext_payload, dict) else {}
    ext["transaction_id"] = str(transaction_id or "").strip()
    order.remark = json.dumps(ext, ensure_ascii=False)[:4000]
    db.add(order)

    _upsert_membership_paid_order(
        db=db,
        user_pk=user_pk,
        plan_id=str(order.plan_id),
        plan_name=str(order.plan_name),
        duration_days=int(order.duration_days or 0) or 30,
        order_no=str(order.order_no),
        now=now,
    )

    db.commit()
    db.refresh(order)
    snapshot = resolve_member_snapshot(db=db, user_pk=user_pk)
    return {
        "order_no": str(order.order_no),
        "already_paid": False,
        "member_expire_at": snapshot["member_expire_at"],
        "member_expire_date_text": snapshot["expire_date_text"],
    }


def resolve_member_snapshot(db: Session, *, user_pk: int) -> dict:
    now = _utc_now_naive()
    membership = _get_membership(db=db, user_pk=user_pk)

    opened = False
    expire_at: datetime | None = None
    plan_id = ""
    plan_name = ""
    if membership is not None:
        expire_at = membership.expire_at
        plan_id = str(membership.plan_id or "").strip()
        plan_name = str(membership.plan_name or "").strip()
        if membership.status == MEMBER_STATUS_ACTIVE and membership.expire_at and membership.expire_at > now:
            opened = True

    status_text = "已开通" if opened else "未开通"
    status_value = MEMBER_STATUS_ACTIVE if opened else MEMBER_STATUS_INACTIVE
    expire_at_iso = expire_at.isoformat() if expire_at else None
    expire_date_text = _format_date(expire_at if opened else None)

    return {
        "opened": opened,
        "status_text": status_text,
        "status": status_value,
        "expire_at": expire_at_iso,
        "expire_date_text": expire_date_text,
        "plan_id": plan_id,
        "plan_name": plan_name,
        # 兼容前端已有识别逻辑字段
        "is_member": opened,
        "member_opened": opened,
        "is_vip": opened,
        "vip_opened": opened,
        "member_status": status_value,
        "vip_status": status_value,
        "member_expire_at": expire_at_iso if opened else None,
        "vip_expire_at": expire_at_iso if opened else None,
        "member_plan_id": plan_id if opened else "",
        "member_plan_name": plan_name if opened else "",
    }


def get_member_center_overview(db: Session, *, user_pk: int) -> dict:
    user = get_user_by_id(db=db, user_id=user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    try:
        cleanup_expired_member_points_orders(db=db, user_pk=user_pk)
        plans = _resolve_member_plans(db=db)
        payment_options = _resolve_payment_options(db=db)
        wallet = ensure_user_wallet(db=db, user_pk=user_pk, default_balance=user.balance or 0)
        points_account = ensure_user_points_account(db=db, user_pk=user_pk, default_balance=0)
        snapshot = resolve_member_snapshot(db=db, user_pk=user_pk)
        serialized_plans: list[dict] = []
        for plan in plans:
            serialized_plans.append(
                _serialize_plan(
                    plan,
                    points_offer=resolve_member_points_offer(
                        db=db,
                        user_pk=user_pk,
                        plan_id=str(plan["id"]),
                        price_amount=_to_decimal(plan["price"], Decimal("0.00")),
                    ),
                )
            )
    except SQLAlchemyError as exc:
        raise BusinessException(
            message="会员模块尚未初始化，请先执行数据库迁移",
            code=5501,
            status_code=500,
        ) from exc

    return {
        "status": {
            "opened": bool(snapshot["opened"]),
            "status_text": str(snapshot["status_text"]),
            "expire_at": snapshot["expire_at"],
            "expire_date_text": str(snapshot["expire_date_text"]),
            "plan_id": str(snapshot["plan_id"]),
            "plan_name": str(snapshot["plan_name"]),
        },
        "plans": serialized_plans,
        "benefits": [dict(item) for item in DEFAULT_MEMBER_BENEFITS],
        "wallet": {
            "balance": float(Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))),
        },
        "points": {
            "balance": int(points_account.balance or 0),
            "frozen_balance": int(points_account.frozen_balance or 0),
            "available_balance": max(int(points_account.balance or 0) - int(points_account.frozen_balance or 0), 0),
        },
        "payment": payment_options,
    }


def subscribe_member_plan(
    db: Session,
    *,
    user_pk: int,
    plan_id: str,
    pay_channel: str | None = None,
    use_points_discount: bool | None = None,
    request_client_ip: str | None = None,
    request_base_url: str | None = None,
) -> dict:
    user = get_user_by_id(db=db, user_id=user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    normalized_plan_id = str(plan_id or "").strip()
    if not normalized_plan_id:
        raise BusinessException(message="订阅方案不能为空", code=4511, status_code=400)

    try:
        cleanup_expired_member_points_orders(db=db, user_pk=user_pk)
        plans = _resolve_member_plans(db=db)
        selected_plan = {str(item["id"]): item for item in plans}.get(normalized_plan_id)
        if selected_plan is None:
            raise BusinessException(message="订阅方案不存在或已下线", code=4512, status_code=400)

        payment_options = _resolve_payment_options(db=db)
        enabled_channels = {str(item["key"]): bool(item["enabled"]) for item in payment_options["channels"]}
        normalized_pay_channel = str(pay_channel or payment_options["default_channel"]).strip().lower()
        if normalized_pay_channel not in enabled_channels or not enabled_channels[normalized_pay_channel]:
            raise BusinessException(message="当前支付方式不可用", code=4513, status_code=400)

        original_amount = _to_decimal(selected_plan["price"], Decimal("0.00"))
        duration_days = int(selected_plan["duration_days"])
        points_offer = resolve_member_points_offer(
            db=db,
            user_pk=user_pk,
            plan_id=str(selected_plan["id"]),
            price_amount=original_amount,
        )
        wants_points_discount = bool(use_points_discount)
        if wants_points_discount and not bool(points_offer.get("enabled")):
            raise BusinessException(message="当前套餐暂不支持积分抵扣", code=4514, status_code=400)
        if wants_points_discount and not bool(points_offer.get("can_use")):
            raise BusinessException(
                message="积分不足，暂时无法使用会员积分抵扣",
                code=4519,
                status_code=400,
                data={
                    "required_points": int(points_offer.get("required_points") or 0),
                    "available_points": int(points_offer.get("available_points") or 0),
                    "missing_points": int(points_offer.get("missing_points") or 0),
                },
            )

        points_cost = int(points_offer.get("required_points") or 0) if wants_points_discount else 0
        points_discount_rate = (
            Decimal(str(points_offer.get("discount_rate") or 1)).quantize(Decimal("0.0001"))
            if wants_points_discount
            else Decimal("1.0000")
        )
        price_amount = (
            _to_decimal(points_offer.get("discounted_price"), original_amount)
            if wants_points_discount
            else original_amount
        )
        saved_amount = (original_amount - price_amount).quantize(Decimal("0.01"))
        wallet = ensure_user_wallet(db=db, user_pk=user_pk, default_balance=user.balance or 0)
        wallet_balance = Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))

        # 余额支付不足时，自动降级到微信支付
        if normalized_pay_channel == PAY_CHANNEL_WALLET and price_amount > wallet_balance:
            normalized_pay_channel = PAY_CHANNEL_WXPAY

        now = _utc_now_naive()
        order_no = _generate_order_no()

        if normalized_pay_channel == PAY_CHANNEL_WALLET:
            if price_amount > Decimal("0.00"):
                wallet.balance = (wallet_balance - price_amount).quantize(Decimal("0.01"))
            points_status = POINTS_STATUS_NONE
            if wants_points_discount and points_cost > 0:
                consume_points_for_member_order(
                    db=db,
                    user_pk=user_pk,
                    order_no=order_no,
                    points_cost=points_cost,
                    plan_name=str(selected_plan["name"]),
                    use_reserved_balance=False,
                    commit=False,
                )
                points_status = POINTS_STATUS_SPENT
            order = MemberOrder(
                order_no=order_no,
                user_pk=user_pk,
                plan_id=str(selected_plan["id"]),
                plan_name=str(selected_plan["name"]),
                duration_days=duration_days,
                amount=price_amount,
                original_amount=original_amount,
                points_cost=points_cost,
                points_discount_rate=points_discount_rate,
                used_points_discount=wants_points_discount,
                points_status=points_status,
                pay_channel=PAY_CHANNEL_WALLET,
                status=ORDER_STATUS_PAID,
                remark="member subscribe by wallet",
                paid_at=now,
            )
            db.add(order)
            membership = _upsert_membership_paid_order(
                db=db,
                user_pk=user_pk,
                plan_id=str(selected_plan["id"]),
                plan_name=str(selected_plan["name"]),
                duration_days=duration_days,
                order_no=order_no,
                now=now,
            )
            db.commit()
            db.refresh(order)
            db.refresh(membership)
            db.refresh(wallet)
            snapshot = resolve_member_snapshot(db=db, user_pk=user_pk)
            return {
                "action": "wallet_paid",
                "order_no": str(order.order_no),
                "plan_id": str(order.plan_id),
                "plan_name": str(order.plan_name),
                "paid_amount": float(Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))),
                "original_amount": float(Decimal(str(order.original_amount or 0)).quantize(Decimal("0.01"))),
                "saved_amount": float(saved_amount),
                "pay_channel": str(order.pay_channel),
                "points_cost": int(order.points_cost or 0),
                "used_points_discount": bool(order.used_points_discount),
                "points_status": str(order.points_status or POINTS_STATUS_NONE),
                "wallet_balance": float(Decimal(str(wallet.balance or 0)).quantize(Decimal("0.01"))),
                "member_expire_at": snapshot["member_expire_at"],
                "member_expire_date_text": snapshot["expire_date_text"],
            }

        if normalized_pay_channel == PAY_CHANNEL_MOCK:
            points_status = POINTS_STATUS_NONE
            if wants_points_discount and points_cost > 0:
                consume_points_for_member_order(
                    db=db,
                    user_pk=user_pk,
                    order_no=order_no,
                    points_cost=points_cost,
                    plan_name=str(selected_plan["name"]),
                    use_reserved_balance=False,
                    commit=False,
                )
                points_status = POINTS_STATUS_SPENT
            order = MemberOrder(
                order_no=order_no,
                user_pk=user_pk,
                plan_id=str(selected_plan["id"]),
                plan_name=str(selected_plan["name"]),
                duration_days=duration_days,
                amount=price_amount,
                original_amount=original_amount,
                points_cost=points_cost,
                points_discount_rate=points_discount_rate,
                used_points_discount=wants_points_discount,
                points_status=points_status,
                pay_channel=PAY_CHANNEL_MOCK,
                status=ORDER_STATUS_PAID,
                remark="member subscribe by mock",
                paid_at=now,
            )
            db.add(order)
            membership = _upsert_membership_paid_order(
                db=db,
                user_pk=user_pk,
                plan_id=str(selected_plan["id"]),
                plan_name=str(selected_plan["name"]),
                duration_days=duration_days,
                order_no=order_no,
                now=now,
            )
            db.commit()
            db.refresh(order)
            db.refresh(membership)
            snapshot = resolve_member_snapshot(db=db, user_pk=user_pk)
            return {
                "action": "mock_paid",
                "order_no": str(order.order_no),
                "plan_id": str(order.plan_id),
                "plan_name": str(order.plan_name),
                "paid_amount": float(Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))),
                "original_amount": float(Decimal(str(order.original_amount or 0)).quantize(Decimal("0.01"))),
                "saved_amount": float(saved_amount),
                "pay_channel": str(order.pay_channel),
                "points_cost": int(order.points_cost or 0),
                "used_points_discount": bool(order.used_points_discount),
                "points_status": str(order.points_status or POINTS_STATUS_NONE),
                "member_expire_at": snapshot["member_expire_at"],
                "member_expire_date_text": snapshot["expire_date_text"],
            }

        if normalized_pay_channel == PAY_CHANNEL_WXPAY:
            if not enabled_channels.get(PAY_CHANNEL_WXPAY):
                raise BusinessException(message="微信支付未开启，请联系管理员配置", code=4518, status_code=400)
            openid = str(user.wechat_openid or "").strip()
            if not openid:
                raise BusinessException(message="请先绑定微信账号后再发起微信支付", code=4515, status_code=400)

            if request_base_url:
                base = str(request_base_url).rstrip("/")
                fallback_notify_url = f"{base}/api/v1/payment/wechat/notify"
            else:
                fallback_notify_url = ""
            notify_url = str(settings.WECHAT_PAY_NOTIFY_URL or "").strip() or fallback_notify_url
            if not notify_url:
                raise BusinessException(message="微信支付回调地址未配置", code=4516, status_code=500)

            points_status = POINTS_STATUS_NONE
            if wants_points_discount and points_cost > 0:
                reserve_points_for_member_order(
                    db=db,
                    user_pk=user_pk,
                    points_cost=points_cost,
                    order_no=order_no,
                    commit=False,
                )
                points_status = POINTS_STATUS_RESERVED

            wxpay_params = _prepare_wxpay_params(
                user_openid=openid,
                order_no=order_no,
                amount_yuan=price_amount,
                plan_name=str(selected_plan["name"]),
                client_ip=request_client_ip,
                notify_url=notify_url,
            )
            order = MemberOrder(
                order_no=order_no,
                user_pk=user_pk,
                plan_id=str(selected_plan["id"]),
                plan_name=str(selected_plan["name"]),
                duration_days=duration_days,
                amount=price_amount,
                original_amount=original_amount,
                points_cost=points_cost,
                points_discount_rate=points_discount_rate,
                used_points_discount=wants_points_discount,
                points_status=points_status,
                pay_channel=PAY_CHANNEL_WXPAY,
                status=ORDER_STATUS_PENDING,
                remark="member subscribe by wxpay pending",
                paid_at=None,
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            return {
                "action": "wxpay_required",
                "order_no": str(order.order_no),
                "plan_id": str(order.plan_id),
                "plan_name": str(order.plan_name),
                "paid_amount": float(Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))),
                "original_amount": float(Decimal(str(order.original_amount or 0)).quantize(Decimal("0.01"))),
                "saved_amount": float(saved_amount),
                "pay_channel": str(order.pay_channel),
                "points_cost": int(order.points_cost or 0),
                "used_points_discount": bool(order.used_points_discount),
                "points_status": str(order.points_status or POINTS_STATUS_NONE),
                "need_confirm": True,
                "wxpay": wxpay_params,
            }

        raise BusinessException(message="当前支付方式不支持", code=4517, status_code=400)
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(
            message="会员开通失败，请确认数据库迁移已完成",
            code=5502,
            status_code=500,
        ) from exc


def confirm_member_order_payment(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
    transaction_id: str | None = None,
    ext_payload: dict | None = None,
) -> dict:
    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        raise BusinessException(message="订单号不能为空", code=4531, status_code=400)

    try:
        cleanup_expired_member_points_orders(db=db, user_pk=user_pk)
        order = _get_order_by_order_no(db=db, order_no=normalized_order_no)
        if order is None or int(order.user_pk) != int(user_pk):
            raise BusinessException(message="订单不存在", code=4532, status_code=404)
        return _confirm_paid_member_order(
            db=db,
            order=order,
            transaction_id=transaction_id,
            ext_payload=ext_payload,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="确认支付失败，请稍后重试", code=5504, status_code=500) from exc


def get_member_order_status(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
) -> dict:
    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        raise BusinessException(message="订单号不能为空", code=4541, status_code=400)

    try:
        order = _get_order_by_order_no(db=db, order_no=normalized_order_no)
        if order is None or int(order.user_pk) != int(user_pk):
            raise BusinessException(message="订单不存在", code=4532, status_code=404)
    except SQLAlchemyError as exc:
        raise BusinessException(message="查询订单失败，请稍后重试", code=5505, status_code=500) from exc

    status_text = str(order.status or "").strip().lower()
    paid = status_text == ORDER_STATUS_PAID
    return {
        "order_no": str(order.order_no),
        "status": status_text or ORDER_STATUS_PENDING,
        "pay_channel": str(order.pay_channel or ""),
        "paid": paid,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "plan_id": str(order.plan_id or ""),
        "plan_name": str(order.plan_name or ""),
        "paid_amount": float(Decimal(str(order.amount or 0)).quantize(Decimal("0.01"))),
        "original_amount": float(Decimal(str(order.original_amount or 0)).quantize(Decimal("0.01"))),
        "points_cost": int(order.points_cost or 0),
        "points_discount_rate": float(Decimal(str(order.points_discount_rate or 1)).quantize(Decimal("0.0001"))),
        "used_points_discount": bool(order.used_points_discount),
        "points_status": str(order.points_status or POINTS_STATUS_NONE),
    }


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

    api_key = str(settings.WECHAT_PAY_API_V2_KEY or "").strip()
    if not _verify_wechat_v2_sign(payload, api_key=api_key):
        return False, "INVALID_SIGN"

    if str(payload.get("return_code") or "").strip().upper() != "SUCCESS":
        return False, str(payload.get("return_msg") or "RETURN_CODE_FAIL")
    if str(payload.get("result_code") or "").strip().upper() != "SUCCESS":
        out_trade_no = str(payload.get("out_trade_no") or "").strip()
        if out_trade_no:
            try:
                order = _get_order_by_order_no(db=db, order_no=out_trade_no)
                if order is not None and str(order.status or "").strip().lower() == ORDER_STATUS_PENDING:
                    if bool(order.used_points_discount) and int(order.points_cost or 0) > 0 and str(order.points_status or "").strip().lower() == POINTS_STATUS_RESERVED:
                        release_reserved_points_for_member_order(
                            db=db,
                            user_pk=int(order.user_pk),
                            points_cost=int(order.points_cost or 0),
                            commit=False,
                        )
                        order.points_status = POINTS_STATUS_RELEASED
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
            except SQLAlchemyError:
                db.rollback()
        return True, "OK"

    out_trade_no = str(payload.get("out_trade_no") or "").strip()
    if not out_trade_no:
        return False, "MISSING_ORDER_NO"

    try:
        order = _get_order_by_order_no(db=db, order_no=out_trade_no)
        if order is None:
            return False, "ORDER_NOT_FOUND"

        total_fee_text = str(payload.get("total_fee") or "").strip()
        if total_fee_text.isdigit():
            notify_total_fee = int(total_fee_text)
            order_total_fee = int((Decimal(str(order.amount or 0)) * Decimal("100")).quantize(Decimal("1")))
            if notify_total_fee != order_total_fee:
                return False, "TOTAL_FEE_MISMATCH"

        if str(order.pay_channel or "").strip().lower() != PAY_CHANNEL_WXPAY:
            return False, "PAY_CHANNEL_MISMATCH"

        _confirm_paid_member_order(
            db=db,
            order=order,
            transaction_id=str(payload.get("transaction_id") or "").strip(),
            ext_payload={
                "notify": payload,
                "source": "wechat_notify",
            },
        )
        return True, "OK"
    except BusinessException as exc:
        if exc.code == 4533:
            # 订单状态不允许更新时，按成功应答避免微信重复回调风暴
            return True, "OK"
        return False, str(exc.message or "BIZ_FAIL")
    except SQLAlchemyError:
        db.rollback()
        return False, "DB_ERROR"


def list_member_orders(
    db: Session,
    *,
    user_pk: int,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    safe_limit = min(max(int(limit), 1), 50)
    cleanup_expired_member_points_orders(db=db, user_pk=user_pk)
    stmt = select(MemberOrder).where(MemberOrder.user_pk == user_pk)

    normalized_cursor = str(cursor or "").strip()
    if normalized_cursor.isdigit():
        stmt = stmt.where(MemberOrder.id < int(normalized_cursor))

    stmt = stmt.order_by(MemberOrder.id.desc()).limit(safe_limit + 1)
    try:
        rows = db.execute(stmt).scalars().all()
    except SQLAlchemyError as exc:
        raise BusinessException(
            message="会员订单模块尚未初始化，请先执行数据库迁移",
            code=5503,
            status_code=500,
        ) from exc
    has_more = len(rows) > safe_limit
    records = rows[:safe_limit]
    next_cursor = str(records[-1].id) if has_more and records else ""

    items = [
        {
            "id": int(item.id),
            "order_no": str(item.order_no),
            "plan_id": str(item.plan_id),
            "plan_name": str(item.plan_name),
            "duration_days": int(item.duration_days or 0),
            "paid_amount": float(Decimal(str(item.amount or 0)).quantize(Decimal("0.01"))),
            "original_amount": float(Decimal(str(item.original_amount or 0)).quantize(Decimal("0.01"))),
            "pay_channel": str(item.pay_channel or ""),
            "status": str(item.status or ""),
            "points_cost": int(item.points_cost or 0),
            "points_discount_rate": float(Decimal(str(item.points_discount_rate or 1)).quantize(Decimal("0.0001"))),
            "used_points_discount": bool(item.used_points_discount),
            "points_status": str(item.points_status or POINTS_STATUS_NONE),
            "remark": str(item.remark or ""),
            "paid_at": item.paid_at.isoformat() if item.paid_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in records
    ]

    return {
        "items": items,
        "cursor": normalized_cursor,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": safe_limit,
    }
