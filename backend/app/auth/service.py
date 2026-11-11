import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from random import randint
from uuid import uuid4
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.asset_urls import normalize_persisted_asset_url
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.redis import get_redis
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.wechat_access_token import get_wechat_access_token, invalidate_wechat_access_token
from app.crud import (
    bind_wechat_identity,
    create_user,
    get_user_by_id,
    get_user_by_phone,
    get_user_by_wechat_openid,
    get_user_realtime_stats,
    update_user_login_meta,
)
from app.points import grant_invite_friend_points, resolve_inviter_user_pk
from app.schemas.auth import (
    AccountCloseData,
    LoginData,
    PasswordChangeData,
    PhoneBindData,
    SendCodeData,
    UserBrief,
    WechatBindData,
)

_SMS_CODE_KEY_PREFIX = "auth:sms:"
_SMS_CODE_EXPIRE_SECONDS = 300
_PHONE_BIND_CODE_KEY_PREFIX = "auth:bind_phone_user:"
_PHONE_BIND_CODE_EXPIRE_SECONDS = 300
_PASSWORD_CHANGE_CODE_KEY_PREFIX = "auth:change_password_user:"
_PASSWORD_CHANGE_CODE_EXPIRE_SECONDS = 300

# Redis unavailable fallback: {phone: (code, expire_at)}
_local_code_store: dict[str, tuple[str, datetime]] = {}
# Redis unavailable fallback for phone bind: {user_pk: (code, expire_at)}
_local_phone_bind_code_store: dict[int, tuple[str, datetime]] = {}
_local_password_change_code_store: dict[int, tuple[str, datetime]] = {}


def _sms_key(phone: str) -> str:
    return f"{_SMS_CODE_KEY_PREFIX}{phone}"


def _phone_bind_key(user_pk: int) -> str:
    return f"{_PHONE_BIND_CODE_KEY_PREFIX}{user_pk}"


def _password_change_key(user_pk: int) -> str:
    return f"{_PASSWORD_CHANGE_CODE_KEY_PREFIX}{user_pk}"


def _generate_sms_code() -> str:
    return f"{randint(0, 999999):06d}"


def _normalize_optional_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:max_len]


def _normalize_avatar_input(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value, 255)
    if not normalized:
        return None
    try:
        return normalize_persisted_asset_url(
            normalized,
            field_label="头像",
        )[:255]
    except BusinessException:
        return None


def _parse_card_files(card_files_json: str | None) -> list[dict]:
    if not card_files_json:
        return []
    try:
        parsed = json.loads(card_files_json)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def _resolve_user_stats(db: Session, user) -> dict:
    fallback_stats = {
        "circle_count": int(user.circle_count or 0),
        "network_count": int(user.network_count or 0),
        "balance": user.balance or 0,
        "points": 0,
    }

    try:
        return get_user_realtime_stats(
            db=db,
            user_pk=user.id,
            fallback_circle_count=fallback_stats["circle_count"],
            fallback_network_count=fallback_stats["network_count"],
            fallback_balance=fallback_stats["balance"],
            fallback_points=fallback_stats["points"],
        )
    except SQLAlchemyError as exc:
        logger.warning(
            f"Failed to query realtime user stats, fallback to user fields. "
            f"user_pk={user.id}, error={exc}"
        )
        return fallback_stats


def _build_login_data(user, is_new_user: bool, db: Session) -> LoginData:
    stats = _resolve_user_stats(db=db, user=user)
    avatar_status = str(getattr(user, "avatar_review_status", "approved") or "approved")
    nickname_status = str(getattr(user, "nickname_review_status", "approved") or "approved")
    intro_status = str(getattr(user, "intro_review_status", "approved") or "approved")
    display_nickname = (
        str(user.nickname or "").strip()
        if nickname_status == "approved"
        else f"用户{str(user.user_id or '')[-4:] or '0000'}"
    )
    display_avatar = (
        str(user.avatar_url or "").strip()
        if avatar_status == "approved"
        else settings.DEFAULT_AVATAR_URL
    )

    user_info = UserBrief(
        userId=user.user_id,
        user_id=user.user_id,
        phone=user.phone,
        nickname=display_nickname,
        avatar_url=display_avatar or None,
        wechat_bound=bool(user.wechat_openid),
        is_verified=bool(user.is_verified),
        intro=user.intro if intro_status == "approved" else None,
        industry_code=user.industry_code,
        industry_label=user.industry_label,
        city_name=user.city_name,
        company_name=user.company_name,
        job_title=user.job_title,
        card_files=_parse_card_files(user.card_files_json),
        show_contact=bool(user.show_contact),
        circle_count=int(stats["circle_count"] or 0),
        network_count=int(stats["network_count"] or 0),
        points=int(stats.get("points") or 0),
        balance=float(stats["balance"] or 0),
        invite_code=str(user.user_id or "").strip() or None,
    )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "tv": int(user.token_version or 0),
            "jti": uuid4().hex,
        },
    )

    return LoginData(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        is_new_user=is_new_user,
        user_info=user_info,
    )


def _wechat_api_enabled() -> bool:
    return bool(settings.WECHAT_MINI_APP_ID and settings.WECHAT_MINI_APP_SECRET)


def _is_dev_mode() -> bool:
    app_env = settings.APP_ENV.strip().lower()
    return settings.DEBUG or app_env in {"dev", "local", "test", "testing"}


def _wechat_virtual_phone(openid: str) -> str:
    # A deterministic internal identifier for miniapp users before phone binding.
    digest = sha256(openid.encode("utf-8")).hexdigest()[:16]
    return f"wx_{digest}"


def _is_wechat_virtual_phone(phone: str | None) -> bool:
    if not phone:
        return False
    normalized = str(phone).strip().lower()
    return normalized.startswith("wx_")


def _mask_phone(phone: str) -> str:
    normalized = str(phone or "").strip()
    if len(normalized) != 11 or not normalized.isdigit():
        return normalized
    return f"{normalized[:3]}****{normalized[7:]}"


def _is_mainland_phone(phone: str | None) -> bool:
    if not phone:
        return False
    normalized = str(phone).strip()
    return len(normalized) == 11 and normalized.isdigit() and normalized.startswith("1")


def _resolve_wechat_openid(
    code: str,
    device_id: str | None = None,
    client_ip: str | None = None,
) -> tuple[str, str | None, str | None]:
    if _wechat_api_enabled():
        query = urlencode(
            {
                "appid": settings.WECHAT_MINI_APP_ID,
                "secret": settings.WECHAT_MINI_APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            }
        )
        request_url = f"{settings.WECHAT_CODE2SESSION_URL}?{query}"

        try:
            with urlopen(request_url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Failed to call WeChat code2session: {exc}")
            raise BusinessException(
                message="微信登录服务暂不可用，请稍后重试",
                code=4101,
                status_code=502,
            )

        errcode = payload.get("errcode")
        if errcode:
            errmsg = payload.get("errmsg", "")
            appid = str(settings.WECHAT_MINI_APP_ID or "").strip()
            logger.warning(
                "WeChat code2session failed: "
                f"errcode={errcode}, errmsg={errmsg}, appid_suffix={appid[-4:] if appid else '-'}, "
                f"client_ip={client_ip or '-'}, device_id={_normalize_optional_text(device_id, 128) or '-'}"
            )
            raise BusinessException(
                message="微信登录失败，请重试",
                code=4102,
                status_code=400,
                data=(
                    {
                        "wechat_errcode": errcode,
                        "wechat_errmsg": errmsg or None,
                    }
                    if _is_dev_mode()
                    else None
                ),
            )

        openid = payload.get("openid")
        if not openid:
            logger.warning(
                "WeChat code2session missing openid: "
                f"payload_keys={sorted(payload.keys())}, client_ip={client_ip or '-'}, "
                f"device_id={_normalize_optional_text(device_id, 128) or '-'}"
            )
            raise BusinessException(
                message="微信登录失败，请重试",
                code=4103,
                status_code=400,
                data=(
                    {
                        "wechat_payload_keys": sorted(payload.keys()),
                    }
                    if _is_dev_mode()
                    else None
                ),
            )

        unionid = payload.get("unionid")
        normalized_unionid = str(unionid) if unionid else None
        session_key = payload.get("session_key")
        normalized_session_key = str(session_key) if session_key else None

        return str(openid), normalized_unionid, normalized_session_key

    if not _is_dev_mode():
        raise BusinessException(
            message="微信登录配置缺失，请联系管理员",
            code=4104,
            status_code=500,
        )

    # Dev fallback for local integration without real WeChat credentials.
    # Priority: stable device_id -> client_ip -> code
    # This avoids creating a new account for each temporary login code.
    fallback_seed = (
        _normalize_optional_text(device_id, 128)
        or _normalize_optional_text(client_ip, 64)
        or code
    )
    openid = f"debug_{sha256(fallback_seed.encode('utf-8')).hexdigest()[:24]}"
    return openid, None, None


def _resolve_wechat_phone(phone_code: str | None) -> str | None:
    normalized_code = _normalize_optional_text(phone_code, 128)
    if not normalized_code:
        if _is_dev_mode():
            return None
        raise BusinessException(message="请先授权手机号后再注册", code=4109, status_code=400)

    body = json.dumps({"code": normalized_code}).encode("utf-8")
    payload: dict = {}
    try:
        for attempt in range(2):
            token = get_wechat_access_token(force_refresh=attempt > 0)
            if not token:
                raise RuntimeError("WeChat access token is unavailable")
            request = UrlRequest(
                f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={token}",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            errcode = int(payload.get("errcode") or 0)
            if errcode not in {40001, 40014, 42001}:
                break
            invalidate_wechat_access_token()
            logger.warning(f"WeChat phone token expired, errcode={errcode}; refreshing once")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Failed to get WeChat phone number: {exc}")
        raise BusinessException(message="微信手机号授权失败，请稍后重试", code=4110, status_code=502)

    if int(payload.get("errcode") or 0) != 0:
        logger.warning(f"WeChat phone failed, errcode={payload.get('errcode')}, errmsg={payload.get('errmsg')}")
        raise BusinessException(message="微信手机号授权失败，请重新授权", code=4111, status_code=400)

    phone = str((payload.get("phone_info") or {}).get("phoneNumber") or "").strip()
    if not _is_mainland_phone(phone):
        raise BusinessException(message="请授权中国大陆手机号后再注册", code=4112, status_code=400)
    return phone


def _sync_authorized_phone_to_wechat_user(
    db: Session,
    *,
    user,
    authorized_phone: str | None,
):
    phone = str(authorized_phone or "").strip()
    if not _is_mainland_phone(phone):
        return user

    current_phone = str(user.phone or "").strip()
    if current_phone == phone:
        return user

    # Existing accounts may have changed their bound phone in account management.
    # A later WeChat login should not overwrite that user-managed phone with the
    # phone returned by WeChat authorization. Only legacy virtual phones are
    # backfilled from WeChat authorization.
    if _is_mainland_phone(current_phone):
        return user

    existing_user = get_user_by_phone(db=db, phone=phone)
    if existing_user is not None and int(existing_user.id) != int(user.id):
        raise BusinessException(message="该手机号已绑定其他账号", code=4113, status_code=409)

    user.phone = phone
    db.add(user)
    return user


async def send_login_sms_code(phone: str) -> SendCodeData:
    code = _generate_sms_code()

    stored_in_redis = False
    try:
        redis_client = get_redis()
        await redis_client.set(_sms_key(phone), code, ex=_SMS_CODE_EXPIRE_SECONDS)
        stored_in_redis = True
    except (RuntimeError, RedisError):
        stored_in_redis = False

    if not stored_in_redis:
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=_SMS_CODE_EXPIRE_SECONDS)
        _local_code_store[phone] = (code, expire_at)

    return SendCodeData(
        phone=phone,
        expires_in=_SMS_CODE_EXPIRE_SECONDS,
        # TODO: hide debug_code after integrating real SMS provider.
        debug_code=code,
    )


async def send_phone_bind_sms_code(
    phone: str,
    db: Session,
    current_user_pk: int,
) -> SendCodeData:
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    new_phone = phone
    existing_user = get_user_by_phone(db=db, phone=new_phone)
    if existing_user is not None and existing_user.id != user.id:
        raise BusinessException(message="该手机号已被其他账号绑定", code=4201, status_code=409)

    # Change-flow security rule:
    # if current phone is a real mainland mobile number, send verification SMS to current phone.
    # otherwise (legacy virtual phone), fallback to sending code to the target new phone.
    send_to_phone = user.phone if _is_mainland_phone(user.phone) else new_phone
    if not _is_mainland_phone(send_to_phone):
        raise BusinessException(message="当前账号手机号异常，请重新登录后再试", code=4204, status_code=400)

    code = _generate_sms_code()
    redis_key = _phone_bind_key(current_user_pk)

    stored_in_redis = False
    try:
        redis_client = get_redis()
        await redis_client.set(redis_key, code, ex=_PHONE_BIND_CODE_EXPIRE_SECONDS)
        stored_in_redis = True
    except (RuntimeError, RedisError):
        stored_in_redis = False

    if not stored_in_redis:
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=_PHONE_BIND_CODE_EXPIRE_SECONDS)
        _local_phone_bind_code_store[current_user_pk] = (code, expire_at)

    return SendCodeData(
        phone=send_to_phone,
        expires_in=_PHONE_BIND_CODE_EXPIRE_SECONDS,
        debug_code=code,
    )


async def login_with_sms_code(
    phone: str,
    code: str,
    db: Session,
    client_ip: str | None = None,
    invite_code: str | None = None,
    city_name: str | None = None,
) -> LoginData:
    cached_code: str | None = None
    loaded_from_redis = False

    try:
        redis_client = get_redis()
        cached_code = await redis_client.get(_sms_key(phone))
        loaded_from_redis = True
    except (RuntimeError, RedisError):
        loaded_from_redis = False

    if not loaded_from_redis:
        local_data = _local_code_store.get(phone)
        if local_data:
            local_code, expire_at = local_data
            if expire_at > datetime.now(timezone.utc):
                cached_code = local_code
            else:
                _local_code_store.pop(phone, None)

    if not cached_code:
        raise BusinessException(message="验证码已过期，请重新获取", code=4001, status_code=400)

    if cached_code != code:
        raise BusinessException(message="验证码错误", code=4002, status_code=400)

    # One-time code: clear it once validated.
    if loaded_from_redis:
        try:
            redis_client = get_redis()
            await redis_client.delete(_sms_key(phone))
        except (RuntimeError, RedisError):
            pass
    _local_code_store.pop(phone, None)

    is_new_user = False
    normalized_city_name = _normalize_optional_text(city_name, 32)
    try:
        user = get_user_by_phone(db, phone)
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to query user by phone={phone}: {exc}")
        raise BusinessException(message="数据库连接异常，请稍后重试", code=5002, status_code=500)

    if user is None:
        is_new_user = True
        inviter_user_pk = resolve_inviter_user_pk(db=db, invite_code=invite_code)
        try:
            user = create_user(
                db=db,
                phone=phone,
                city_name=normalized_city_name,
                inviter_user_pk=inviter_user_pk,
            )
        except IntegrityError:
            db.rollback()
            user = get_user_by_phone(db, phone)
            if user is None:
                raise BusinessException(message="用户创建失败，请稍后重试", code=5001, status_code=500)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(f"Failed to create user by phone={phone}: {exc}")
            raise BusinessException(message="用户创建失败，请稍后重试", code=5001, status_code=500)

        logger.info(f"Auto-created user for phone login, user_id={user.id}, phone={phone}")
        try:
            grant_invite_friend_points(db=db, invitee_user=user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning(f"Failed to grant invite points for new phone user user_pk={user.id}: {exc}")
    if user is not None and normalized_city_name and not _normalize_optional_text(user.city_name, 32):
        user.city_name = normalized_city_name

    try:
        user = update_user_login_meta(db=db, user=user, client_ip=client_ip)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to update user login meta user_id={user.id}: {exc}")
        raise BusinessException(message="更新登录信息失败，请稍后重试", code=5003, status_code=500)

    return _build_login_data(user=user, is_new_user=is_new_user, db=db)


async def login_with_password(
    phone: str,
    password: str,
    db: Session,
    client_ip: str | None = None,
    invite_code: str | None = None,
) -> LoginData:
    try:
        user = get_user_by_phone(db, phone)
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to query user by phone={phone}: {exc}")
        raise BusinessException(message="数据库连接异常，请稍后重试", code=5002, status_code=500)

    if user is None:
        raise BusinessException(message="账号或密码错误", code=4004, status_code=400)

    stored_password_hash = (user.password_hash or "").strip()
    if not stored_password_hash:
        raise BusinessException(message="请先使用验证码登录并设置密码", code=4005, status_code=400)

    if not verify_password(password, stored_password_hash):
        raise BusinessException(message="账号或密码错误", code=4004, status_code=400)

    try:
        user = update_user_login_meta(db=db, user=user, client_ip=client_ip)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to update user login meta user_id={user.id}: {exc}")
        raise BusinessException(message="更新登录信息失败，请稍后重试", code=5003, status_code=500)

    return _build_login_data(user=user, is_new_user=False, db=db)


async def bind_phone_for_user(
    db: Session,
    current_user_pk: int,
    phone: str,
    code: str,
) -> PhoneBindData:
    redis_key = _phone_bind_key(current_user_pk)
    cached_code: str | None = None
    loaded_from_redis = False

    try:
        redis_client = get_redis()
        cached_code = await redis_client.get(redis_key)
        loaded_from_redis = True
    except (RuntimeError, RedisError):
        loaded_from_redis = False

    if not loaded_from_redis:
        local_data = _local_phone_bind_code_store.get(current_user_pk)
        if local_data:
            local_code, expire_at = local_data
            if expire_at > datetime.now(timezone.utc):
                cached_code = local_code
            else:
                _local_phone_bind_code_store.pop(current_user_pk, None)

    if not cached_code:
        raise BusinessException(message="验证码已过期，请重新获取", code=4202, status_code=400)

    if cached_code != code:
        raise BusinessException(message="验证码错误", code=4203, status_code=400)

    if loaded_from_redis:
        try:
            redis_client = get_redis()
            await redis_client.delete(redis_key)
        except (RuntimeError, RedisError):
            pass
    _local_phone_bind_code_store.pop(current_user_pk, None)

    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    new_phone = phone

    existing_user = get_user_by_phone(db=db, phone=new_phone)
    if existing_user is not None and existing_user.id != user.id:
        raise BusinessException(message="该手机号已被其他账号绑定", code=4201, status_code=409)

    if user.phone == new_phone:
        return PhoneBindData(
            phone=new_phone,
            masked_phone=_mask_phone(new_phone),
            is_bound_to_current_user=True,
            updated=False,
        )

    user.phone = new_phone
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise BusinessException(message="该手机号已被其他账号绑定", code=4201, status_code=409)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to bind phone for user_pk={user.id}: {exc}")
        raise BusinessException(message="手机号绑定失败，请稍后重试", code=5007, status_code=500)

    return PhoneBindData(
        phone=user.phone,
        masked_phone=_mask_phone(user.phone),
        is_bound_to_current_user=True,
        updated=True,
    )


async def send_password_change_sms_code(
    db: Session,
    current_user_pk: int,
) -> SendCodeData:
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    if not _is_mainland_phone(user.phone):
        raise BusinessException(message="手机号未绑定，暂不支持修改密码", code=4301, status_code=400)

    code = _generate_sms_code()
    redis_key = _password_change_key(current_user_pk)

    stored_in_redis = False
    try:
        redis_client = get_redis()
        await redis_client.set(redis_key, code, ex=_PASSWORD_CHANGE_CODE_EXPIRE_SECONDS)
        stored_in_redis = True
    except (RuntimeError, RedisError):
        stored_in_redis = False

    if not stored_in_redis:
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=_PASSWORD_CHANGE_CODE_EXPIRE_SECONDS)
        _local_password_change_code_store[current_user_pk] = (code, expire_at)

    return SendCodeData(
        phone=user.phone,
        expires_in=_PASSWORD_CHANGE_CODE_EXPIRE_SECONDS,
        debug_code=code,
    )


async def change_password_with_sms_code(
    db: Session,
    current_user_pk: int,
    code: str,
    new_password: str,
) -> PasswordChangeData:
    redis_key = _password_change_key(current_user_pk)
    cached_code: str | None = None
    loaded_from_redis = False

    try:
        redis_client = get_redis()
        cached_code = await redis_client.get(redis_key)
        loaded_from_redis = True
    except (RuntimeError, RedisError):
        loaded_from_redis = False

    if not loaded_from_redis:
        local_data = _local_password_change_code_store.get(current_user_pk)
        if local_data:
            local_code, expire_at = local_data
            if expire_at > datetime.now(timezone.utc):
                cached_code = local_code
            else:
                _local_password_change_code_store.pop(current_user_pk, None)

    if not cached_code:
        raise BusinessException(message="验证码已过期，请重新获取", code=4302, status_code=400)

    if cached_code != code:
        raise BusinessException(message="验证码错误", code=4303, status_code=400)

    if loaded_from_redis:
        try:
            redis_client = get_redis()
            await redis_client.delete(redis_key)
        except (RuntimeError, RedisError):
            pass
    _local_password_change_code_store.pop(current_user_pk, None)

    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    if not _is_mainland_phone(user.phone):
        raise BusinessException(message="手机号未绑定，暂不支持修改密码", code=4301, status_code=400)

    resolved_password = str(new_password or "").strip()
    if len(resolved_password) < 6 or len(resolved_password) > 32:
        raise BusinessException(message="新密码长度需为6-32位", code=4304, status_code=400)

    user.password_hash = get_password_hash(resolved_password)
    user.token_version = int(user.token_version or 0) + 1
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to change password for user_pk={user.id}: {exc}")
        raise BusinessException(message="修改密码失败，请稍后重试", code=5008, status_code=500)

    return PasswordChangeData(updated=True, force_relogin=True)


def close_account_for_user(
    db: Session,
    current_user_pk: int,
    confirm_text: str,
) -> AccountCloseData:
    normalized_confirm = str(confirm_text or "").strip()
    if normalized_confirm != "注销账号":
        raise BusinessException(message="请确认注销账号", code=4401, status_code=400)

    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    if not bool(user.is_active):
        return AccountCloseData(closed=True, force_relogin=True)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    release_suffix = f"closed_{user.id}_{int(now.timestamp())}"

    user.is_active = False
    user.token_version = int(user.token_version or 0) + 1
    user.phone = release_suffix[:20]
    user.password_hash = None
    user.wechat_openid = None
    user.wechat_unionid = None
    user.wechat_session_key = None
    user.wechat_bound_at = None
    user.display_phone = None
    user.display_wechat = None
    user.email = None
    user.show_contact = False
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        user.phone = f"closed_{uuid4().hex[:12]}"[:20]
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(f"Failed to close account after phone conflict user_pk={user.id}: {exc}")
            raise BusinessException(message="注销账号失败，请稍后重试", code=5009, status_code=500)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to close account user_pk={user.id}: {exc}")
        raise BusinessException(message="注销账号失败，请稍后重试", code=5009, status_code=500)

    return AccountCloseData(closed=True, force_relogin=True)


async def login_with_wechat_code(
    code: str,
    phone_code: str | None,
    db: Session,
    client_ip: str | None = None,
    nickname: str | None = None,
    avatar_url: str | None = None,
    device_id: str | None = None,
    invite_code: str | None = None,
    city_name: str | None = None,
) -> LoginData:
    if not _normalize_optional_text(phone_code, 128):
        raise BusinessException(message="请先授权手机号后再登录", code=4109, status_code=400)

    authorized_phone = _resolve_wechat_phone(phone_code)

    openid, unionid, session_key = _resolve_wechat_openid(
        code=code,
        device_id=device_id,
        client_ip=client_ip,
    )
    identity_phone = _wechat_virtual_phone(openid)

    normalized_city_name = _normalize_optional_text(city_name, 32)

    is_new_user = False

    try:
        user = get_user_by_wechat_openid(db, openid)
        if user is None:
            legacy_user = get_user_by_phone(db, identity_phone)
            if legacy_user is not None:
                if legacy_user.wechat_openid and legacy_user.wechat_openid != openid:
                    raise BusinessException(message="微信登录状态异常，请联系管理员", code=4105, status_code=409)
                user = bind_wechat_identity(
                    db=db,
                    user=legacy_user,
                    wechat_openid=openid,
                    wechat_unionid=unionid,
                    wechat_session_key=session_key,
                )
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to query WeChat user by openid={openid}: {exc}")
        raise BusinessException(message="数据库连接异常，请稍后重试", code=5002, status_code=500)

    if user is None:
        identity_phone = authorized_phone or identity_phone
        existing_phone_user = get_user_by_phone(db, identity_phone)
        if existing_phone_user is not None:
            if existing_phone_user.wechat_openid and existing_phone_user.wechat_openid != openid:
                raise BusinessException(message="该手机号已绑定其他微信账号", code=4113, status_code=409)
            user = bind_wechat_identity(
                db=db,
                user=existing_phone_user,
                wechat_openid=openid,
                wechat_unionid=unionid,
                wechat_session_key=session_key,
            )
        else:
            is_new_user = True
            inviter_user_pk = resolve_inviter_user_pk(db=db, invite_code=invite_code)

            try:
                user = create_user(
                    db=db,
                    phone=identity_phone,
                    wechat_openid=openid,
                    wechat_unionid=unionid,
                    wechat_session_key=session_key,
                    wechat_bound_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    city_name=normalized_city_name,
                    inviter_user_pk=inviter_user_pk,
                )
            except IntegrityError:
                db.rollback()
                user = get_user_by_wechat_openid(db, openid) or get_user_by_phone(db, identity_phone)
                if user is None:
                    raise BusinessException(message="用户创建失败，请稍后重试", code=5001, status_code=500)
                is_new_user = False
            except SQLAlchemyError as exc:
                db.rollback()
                logger.exception(f"Failed to create WeChat user identity={identity_phone}: {exc}")
                raise BusinessException(message="用户创建失败，请稍后重试", code=5001, status_code=500)

            if is_new_user:
                logger.info(f"Auto-created WeChat user, user_id={user.id}, identity={identity_phone}")
                try:
                    grant_invite_friend_points(db=db, invitee_user=user)
                except SQLAlchemyError as exc:
                    db.rollback()
                    logger.warning(f"Failed to grant invite points for new WeChat user user_pk={user.id}: {exc}")
    else:
        # Optional profile sync for existing users.
        user = _sync_authorized_phone_to_wechat_user(
            db=db,
            user=user,
            authorized_phone=authorized_phone,
        )
        if normalized_city_name and not _normalize_optional_text(user.city_name, 32):
            user.city_name = normalized_city_name
        if session_key:
            user.wechat_session_key = session_key

    try:
        user = update_user_login_meta(db=db, user=user, client_ip=client_ip)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to update WeChat login meta user_id={user.id}: {exc}")
        raise BusinessException(message="更新登录信息失败，请稍后重试", code=5003, status_code=500)

    return _build_login_data(user=user, is_new_user=is_new_user, db=db)


def get_wechat_bind_status(
    db: Session,
    current_user_pk: int,
) -> WechatBindData:
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    return WechatBindData(
        wechat_bound=bool(user.wechat_openid),
        is_bound_to_current_user=bool(user.wechat_openid),
        wechat_bound_at=user.wechat_bound_at.isoformat() if user.wechat_bound_at else None,
    )


async def bind_wechat_for_user(
    db: Session,
    current_user_pk: int,
    code: str,
    client_ip: str | None = None,
    nickname: str | None = None,
    avatar_url: str | None = None,
    device_id: str | None = None,
) -> WechatBindData:
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    openid, unionid, session_key = _resolve_wechat_openid(
        code=code,
        device_id=device_id,
        client_ip=client_ip,
    )

    try:
        existing_bound_user = get_user_by_wechat_openid(db=db, wechat_openid=openid)
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to query bound WeChat user by openid={openid}: {exc}")
        raise BusinessException(message="数据库连接异常，请稍后重试", code=5002, status_code=500)

    if existing_bound_user and existing_bound_user.id != user.id:
        can_transfer_legacy_binding = _is_wechat_virtual_phone(existing_bound_user.phone) and not (
            _is_wechat_virtual_phone(user.phone)
        )
        if not can_transfer_legacy_binding:
            raise BusinessException(message="该微信已绑定其他账号", code=4106, status_code=409)

        # Historical compatibility:
        # old versions bound WeChat login to virtual-phone accounts; when the same person
        # logs in by real phone and binds WeChat, transfer binding to the phone account.
        try:
            existing_bound_user.wechat_openid = None
            existing_bound_user.wechat_unionid = None
            existing_bound_user.wechat_bound_at = None
            db.add(existing_bound_user)
            db.commit()
            db.refresh(existing_bound_user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(
                "Failed to transfer legacy WeChat binding "
                f"from user_pk={existing_bound_user.id} to user_pk={user.id}: {exc}"
            )
            raise BusinessException(message="微信绑定失败，请稍后重试", code=5006, status_code=500)

    if user.wechat_openid and user.wechat_openid != openid:
        # Do not silently replace an existing binding to avoid account hijacking risks.
        raise BusinessException(message="当前账号已绑定其他微信，请先联系管理员处理", code=4107, status_code=409)

    # Legacy account compatibility:
    # if user is a historical WeChat virtual account and has no binding timestamp,补齐绑定标记。
    if not user.wechat_openid or not user.wechat_bound_at:
        try:
            user = bind_wechat_identity(
                db=db,
                user=user,
                wechat_openid=openid,
                wechat_unionid=unionid,
                wechat_session_key=session_key,
            )
        except IntegrityError:
            db.rollback()
            raise BusinessException(message="该微信已绑定其他账号", code=4106, status_code=409)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(f"Failed to bind WeChat for user_pk={user.id}: {exc}")
            raise BusinessException(message="微信绑定失败，请稍后重试", code=5006, status_code=500)

    if session_key:
        user.wechat_session_key = session_key

    try:
        user = update_user_login_meta(db=db, user=user, client_ip=client_ip)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to update bind login meta user_id={user.id}: {exc}")
        raise BusinessException(message="微信绑定失败，请稍后重试", code=5006, status_code=500)

    return WechatBindData(
        wechat_bound=bool(user.wechat_openid),
        is_bound_to_current_user=bool(user.wechat_openid),
        wechat_bound_at=user.wechat_bound_at.isoformat() if user.wechat_bound_at else None,
    )
