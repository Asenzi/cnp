from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.auth.service import (
    bind_phone_for_user,
    bind_wechat_for_user,
    change_password_with_sms_code,
    get_wechat_bind_status,
    login_with_password,
    login_with_sms_code,
    login_with_wechat_code,
    send_login_sms_code,
    send_password_change_sms_code,
    send_phone_bind_sms_code,
)
from app.core.response import success_response
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordLoginRequest,
    PhoneBindCodeRequest,
    PhoneBindRequest,
    SendCodeRequest,
    WechatBindRequest,
    WechatMiniLoginRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sms-code", summary="Send SMS code for login")
async def send_sms_code(payload: SendCodeRequest):
    result = await send_login_sms_code(payload.phone)
    return success_response(data=result.model_dump())


@router.post("/login", summary="Login with phone and SMS code")
async def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(db_session),
):
    client_ip = request.client.host if request.client else None
    result = await login_with_sms_code(
        phone=payload.phone,
        code=payload.code,
        invite_code=payload.invite_code,
        db=db,
        client_ip=client_ip,
    )
    return success_response(data=result.model_dump())


@router.post("/password-login", summary="Login with phone and password")
async def password_login(
    payload: PasswordLoginRequest,
    request: Request,
    db: Session = Depends(db_session),
):
    client_ip = request.client.host if request.client else None
    result = await login_with_password(
        phone=payload.phone,
        password=payload.password,
        invite_code=payload.invite_code,
        db=db,
        client_ip=client_ip,
    )
    return success_response(data=result.model_dump())


@router.post("/wechat-miniapp-login", summary="One-click login for WeChat miniapp")
async def wechat_miniapp_login(
    payload: WechatMiniLoginRequest,
    request: Request,
    db: Session = Depends(db_session),
):
    client_ip = request.client.host if request.client else None
    result = await login_with_wechat_code(
        code=payload.code,
        db=db,
        client_ip=client_ip,
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
        device_id=payload.device_id,
        invite_code=payload.invite_code,
    )
    return success_response(data=result.model_dump())


@router.get("/wechat-bind-status", summary="Get current user's WeChat bind status")
def wechat_bind_status(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = get_wechat_bind_status(db=db, current_user_pk=user_id)
    return success_response(data=result.model_dump())


@router.post("/wechat-bind", summary="Bind WeChat miniapp account to current user")
async def wechat_bind(
    payload: WechatBindRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    client_ip = request.client.host if request.client else None
    result = await bind_wechat_for_user(
        db=db,
        current_user_pk=user_id,
        code=payload.code,
        client_ip=client_ip,
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
        device_id=payload.device_id,
    )
    return success_response(data=result.model_dump(), message="微信绑定成功")


@router.post("/phone-bind-code", summary="Send SMS code for current user phone bind")
async def phone_bind_code(
    payload: PhoneBindCodeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = await send_phone_bind_sms_code(
        phone=payload.phone,
        db=db,
        current_user_pk=user_id,
    )
    return success_response(data=result.model_dump())


@router.post("/phone-bind", summary="Bind or change current user phone by SMS code")
async def phone_bind(
    payload: PhoneBindRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = await bind_phone_for_user(
        db=db,
        current_user_pk=user_id,
        phone=payload.phone,
        code=payload.code,
    )
    return success_response(data=result.model_dump(), message="手机号绑定成功")


@router.post("/password-change-code", summary="Send SMS code for password change")
async def password_change_code(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = await send_password_change_sms_code(
        db=db,
        current_user_pk=user_id,
    )
    return success_response(data=result.model_dump())


@router.post("/password-change", summary="Change password by SMS code")
async def password_change(
    payload: PasswordChangeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = await change_password_with_sms_code(
        db=db,
        current_user_pk=user_id,
        code=payload.code,
        new_password=payload.new_password,
    )
    return success_response(data=result.model_dump(), message="密码修改成功")
