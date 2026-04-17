from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.response import success_response
from app.payment import (
    confirm_member_order_payment,
    confirm_wallet_recharge_payment,
    create_wallet_recharge,
    get_member_center_overview,
    get_member_order_status,
    get_wallet_recharge_status,
    handle_wechat_pay_notify_xml,
    list_member_orders,
    list_wallet_recharge_orders,
    subscribe_member_plan,
)
from app.schemas.payment import (
    MemberOrderConfirmRequest,
    MemberSubscribeRequest,
    WalletRechargeConfirmRequest,
    WalletRechargeRequest,
)

router = APIRouter(prefix="/payment", tags=["Payment"])


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
        request_client_ip=request.client.host if request.client else None,
        request_base_url=str(request.base_url).rstrip("/"),
    )
    action = str(data.get("action") or "").strip()
    if action == "wxpay_required":
        return success_response(data=data, message="请完成微信支付")
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


@router.post("/wallet/recharge", summary="Create wallet recharge order")
def post_wallet_recharge(
    request: Request,
    payload: WalletRechargeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = create_wallet_recharge(
        db=db,
        user_pk=user_id,
        amount=payload.amount,
        pay_channel=payload.pay_channel,
        request_client_ip=request.client.host if request.client else None,
        request_base_url=str(request.base_url).rstrip("/"),
    )
    if str(data.get("action") or "").strip() == "wxpay_required":
        return success_response(data=data, message="请完成微信支付")
    return success_response(data=data, message="充值成功")


@router.post("/wallet/recharge/{order_no}/confirm", summary="Confirm wallet recharge payment")
def post_wallet_recharge_confirm(
    order_no: str,
    payload: WalletRechargeConfirmRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = confirm_wallet_recharge_payment(
        db=db,
        user_pk=user_id,
        order_no=order_no,
        transaction_id=payload.transaction_id,
        ext_payload=payload.ext,
    )
    return success_response(data=data, message="充值确认成功")


@router.get("/wallet/recharge/orders", summary="List wallet recharge orders")
def get_wallet_recharge_orders(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_wallet_recharge_orders(
        db=db,
        user_pk=user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.get("/wallet/recharge/{order_no}", summary="Get wallet recharge order status")
def get_wallet_recharge_order(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_wallet_recharge_status(
        db=db,
        user_pk=user_id,
        order_no=order_no,
    )
    return success_response(data=payload)


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
