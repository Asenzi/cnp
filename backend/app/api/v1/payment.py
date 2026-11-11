from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.response import success_response
from app.payment import (
    CIRCLE_OWNER_PLAN_ID,
    confirm_member_order_payment,
    get_circle_owner_overview,
    get_member_center_overview,
    get_member_order_status,
    handle_wechat_pay_notify_xml,
    list_member_orders,
    subscribe_member_plan,
)
from app.payment.service import PARTNER_PLANS, get_partner_overview
from app.payment.statistics import get_payment_statistics, get_user_payment_summary
from app.schemas.payment import (
    CircleOwnerPurchaseRequest,
    MemberPaymentClientErrorRequest,
    MemberOrderConfirmRequest,
    MemberSubscribeRequest,
    PartnerPurchaseRequest,
)

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.get("/partner/{partner_type}/overview", summary="Get partner identity and commission overview")
def get_partner_product(
    partner_type: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(data=get_partner_overview(db=db, user_pk=user_id, partner_type=partner_type))


@router.post("/partner/{partner_type}/purchase", summary="Purchase partner identity")
def post_partner_purchase(
    partner_type: str,
    request: Request,
    payload: PartnerPurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    if partner_type not in PARTNER_PLANS:
        raise BusinessException(message="合作身份类型无效", code=4538, status_code=400)
    data = subscribe_member_plan(
        db=db,
        user_pk=user_id,
        plan_id=partner_type,
        pay_channel=payload.pay_channel,
        use_points_discount=False,
        client_platform=payload.client_platform,
        request_client_ip=request.client.host if request.client else None,
        request_base_url=str(request.base_url).rstrip("/"),
    )
    if str(data.get("action") or "").strip() == "virtualpay_required":
        return success_response(data=data, message="请完成小程序虚拟支付")
    return success_response(data=data, message="合作身份已开通")


@router.get("/ping", summary="Payment health check")
def payment_ping():
    return success_response(message="payment module ready")


@router.get("/member/center", summary="Get member center overview")
def get_member_center(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_member_center_overview(db=db, user_pk=user_id)
    return success_response(data=payload)


@router.get("/circle-owner/overview", summary="Get lifetime circle owner product")
def get_circle_owner_product(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(data=get_circle_owner_overview(db=db, user_pk=user_id))


@router.post("/circle-owner/purchase", summary="Purchase lifetime circle owner identity")
def post_circle_owner_purchase(
    request: Request,
    payload: CircleOwnerPurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = subscribe_member_plan(
        db=db,
        user_pk=user_id,
        plan_id=CIRCLE_OWNER_PLAN_ID,
        pay_channel=payload.pay_channel,
        use_points_discount=False,
        client_platform=payload.client_platform,
        request_client_ip=request.client.host if request.client else None,
        request_base_url=str(request.base_url).rstrip("/"),
    )
    if str(data.get("action") or "").strip() == "virtualpay_required":
        return success_response(data=data, message="请完成小程序虚拟支付")
    return success_response(data=data, message="永久圈主已开通")


@router.post("/member/subscribe", summary="Subscribe or renew member plan")
def post_member_subscribe(
    request: Request,
    payload: MemberSubscribeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = subscribe_member_plan(
        db=db,
        user_pk=user_id,
        plan_id=payload.plan_id,
        pay_channel=payload.pay_channel,
        use_points_discount=payload.use_points_discount,
        client_platform=payload.client_platform,
        request_client_ip=request.client.host if request.client else None,
        request_base_url=str(request.base_url).rstrip("/"),
        referral_invite_code=payload.referral_invite_code,
    )
    action = str(data.get("action") or "").strip()
    if action == "virtualpay_required":
        return success_response(data=data, message="请完成小程序虚拟支付")
    return success_response(data=data, message="会员开通成功")


@router.post("/member/orders/{order_no}/confirm", summary="Confirm member order payment")
def post_member_order_confirm(
    order_no: str,
    payload: MemberOrderConfirmRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = confirm_member_order_payment(
        db=db,
        user_pk=user_id,
        order_no=order_no,
        transaction_id=payload.transaction_id,
        ext_payload=payload.ext,
    )
    return success_response(data=data, message="支付确认成功")


@router.post("/member/payment-client-error", summary="Report member payment client error")
def report_member_payment_client_error(
    payload: MemberPaymentClientErrorRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    ext = payload.ext if isinstance(payload.ext, dict) else {}
    sign_data = ext.get("signData") if isinstance(ext.get("signData"), dict) else {}
    safe_ext = {
        "platform": ext.get("platform"),
        "system": ext.get("system"),
        "brand": ext.get("brand"),
        "model": ext.get("model"),
        "wechat_version": ext.get("wechatVersion") or ext.get("version"),
        "sdk_version": ext.get("SDKVersion"),
        "env_version": ext.get("envVersion"),
        "payment_mode": ext.get("mode"),
        "sign_data": {
            "offerId": sign_data.get("offerId"),
            "productId": sign_data.get("productId"),
            "goodsPrice": sign_data.get("goodsPrice"),
            "outTradeNo": sign_data.get("outTradeNo"),
            "env": sign_data.get("env"),
            "currencyType": sign_data.get("currencyType"),
        },
    }
    logger.warning(
        "Member payment client error. user_pk={}, order_no={}, scene={}, err_code={}, err_msg={}, ip={}, ext={}",
        user_id,
        payload.order_no,
        payload.scene,
        payload.err_code,
        payload.err_msg,
        request.client.host if request.client else None,
        safe_ext,
    )
    return success_response(data={"reported": True}, message="支付失败原因已记录")


@router.get("/member/orders/{order_no}", summary="Get member order status")
def get_member_order(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_member_order_status(
        db=db,
        user_pk=user_id,
        order_no=order_no,
    )
    return success_response(data=payload)


@router.get("/member/orders", summary="List member orders")
def get_member_orders(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_member_orders(
        db=db,
        user_pk=user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.post("/wallet/recharge", summary="Wallet recharge is disabled")
def post_wallet_recharge():
    raise BusinessException(message="储值充值功能已下线", code=4599, status_code=410)


@router.post("/wallet/recharge/{order_no}/confirm", summary="Wallet recharge is disabled")
def post_wallet_recharge_confirm(order_no: str):
    raise BusinessException(message="储值充值功能已下线", code=4599, status_code=410)


@router.get("/wallet/recharge/orders", summary="Wallet recharge is disabled")
def get_wallet_recharge_orders():
    raise BusinessException(message="储值充值功能已下线", code=4599, status_code=410)


@router.get("/wallet/recharge/{order_no}", summary="Wallet recharge is disabled")
def get_wallet_recharge_order(order_no: str):
    raise BusinessException(message="储值充值功能已下线", code=4599, status_code=410)


def _wechat_notify_xml(success: bool, message: str = "OK") -> str:
    code = "SUCCESS" if success else "FAIL"
    msg = str(message or "OK")
    return (
        "<xml>"
        f"<return_code><![CDATA[{code}]]></return_code>"
        f"<return_msg><![CDATA[{msg}]]></return_msg>"
        "</xml>"
    )


@router.post("/wechat/notify", summary="WeChat Pay notify callback", include_in_schema=False)
async def post_wechat_notify(
    request: Request,
    db: Session = Depends(db_session),
):
    raw_body = (await request.body()).decode("utf-8", errors="ignore")
    success, message = handle_wechat_pay_notify_xml(
        db=db,
        raw_xml=raw_body,
    )
    xml = _wechat_notify_xml(success=success, message=message)
    return Response(content=xml, media_type="application/xml")


@router.get("/statistics/summary", summary="Get payment statistics summary")
def get_payment_stats_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """获取当前用户的支付统计汇总"""
    payload = get_user_payment_summary(db=db, user_pk=user_id)
    return success_response(data=payload)


@router.get("/statistics/overview", summary="Get payment overview statistics (Admin)", include_in_schema=True)
def get_payment_stats_overview(
    start_date: str | None = Query(default=None, description="开始日期 ISO格式"),
    end_date: str | None = Query(default=None, description="结束日期 ISO格式"),
    db: Session = Depends(db_session),
):
    """获取支付概览统计（管理员接口）"""
    from datetime import datetime

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            pass

    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            pass

    payload = get_payment_statistics(
        db=db,
        start_date=parsed_start,
        end_date=parsed_end,
    )
    return success_response(data=payload)
