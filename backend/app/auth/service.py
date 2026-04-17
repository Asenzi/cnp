import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from random import randint
from uuid import uuid4
from urllib.parse import urlencode
from urllib.request import urlopen

from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.redis import get_redis
from app.core.security import create_access_token, get_password_hash, verify_password
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


def _default_nickname(phone: str) -> str:
    # First login nickname strategy: "用户" + phone last 4 digits.
    return f"用户{phone[-4:]}"


def _default_wechat_nickname(openid: str) -> str:
    return f"微信用户{openid[-4:]}"


def _default_avatar_url(seed: str) -> str:
    # Single stable default avatar for new users, configurable by env.
    # Supports "{seed}" placeholder if needed in future.
    template = _normalize_optional_text(settings.DEFAULT_AVATAR_URL, 255) or "/static/logo.png"
    if "{seed}" in template:
        return template.replace("{seed}", seed)
    return template


def _normalize_optional_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:max_len]


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

    user_info = UserBrief(
        userId=user.user_id,
        user_id=user.user_id,
        phone=user.phone,
        nickname=user.nickname,
        avatar_url=user.avatar_url or settings.DEFAULT_AVATAR_URL,
        wechat_bound=bool(user.wechat_openid),
        is_verified=bool(user.is_verified),
        intro=user.intro,
        industry_code=user.industry_code,
        industry_label=user.industry_label,
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
) -> tuple[str, str | None]:
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

        return str(openid), normalized_unionid

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
    return openid, None


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
        expire_at = datetime.now(UTC) + timedelta(seconds=_SMS_CODE_EXPIRE_SECONDS)
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
        expire_at = datetime.now(UTC) + timedelta(seconds=_PHONE_BIND_CODE_EXPIRE_SECONDS)
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
            if expire_at > datetime.now(UTC):
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
                nickname=_default_nickname(phone),
                avatar_url=_default_avatar_url(phone),
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
    elif not _normalize_optional_text(user.avatar_url, 255):
        # Backfill historical data that may have null/empty avatar.
        user.avatar_url = _default_avatar_url(phone)

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
            if expire_at > datetime.now(UTC):
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
        expire_at = datetime.now(UTC) + timedelta(seconds=_PASSWORD_CHANGE_CODE_EXPIRE_SECONDS)
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
            if expire_at > datetime.now(UTC):
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


async def login_with_wechat_code(
    code: str,
    db: Session,
    client_ip: str | None = None,
    nickname: str | None = None,
    avatar_url: str | None = None,
    device_id: str | None = None,
    invite_code: str | None = None,
) -> LoginData:
    openid, unionid = _resolve_wechat_openid(
        code=code,
        device_id=device_id,
        client_ip=client_ip,
    )
    identity_phone = _wechat_virtual_phone(openid)

    normalized_nickname = _normalize_optional_text(nickname, 64)
    normalized_avatar_url = _normalize_optional_text(avatar_url, 255)

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
                )
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to query WeChat user by openid={openid}: {exc}")
        raise BusinessException(message="数据库连接异常，请稍后重试", code=5002, status_code=500)

    if user is None:
        is_new_user = True
        initial_nickname = normalized_nickname or _default_wechat_nickname(openid)
        initial_avatar_url = normalized_avatar_url or _default_avatar_url(openid)
        inviter_user_pk = resolve_inviter_user_pk(db=db, invite_code=invite_code)

        try:
            user = create_user(
                db=db,
                phone=identity_phone,
                nickname=initial_nickname,
                avatar_url=initial_avatar_url,
                wechat_openid=openid,
                wechat_unionid=unionid,
                wechat_bound_at=datetime.now(UTC).replace(tzinfo=None),
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
        if normalized_nickname and normalized_nickname != user.nickname:
            user.nickname = normalized_nickname
        if normalized_avatar_url and normalized_avatar_url != user.avatar_url:
            user.avatar_url = normalized_avatar_url
        elif not _normalize_optional_text(user.avatar_url, 255):
            # Backfill historical data that may have null/empty avatar.
            user.avatar_url = _default_avatar_url(openid)

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

    openid, unionid = _resolve_wechat_openid(
        code=code,
        device_id=device_id,
        client_ip=client_ip,
    )

    normalized_nickname = _normalize_optional_text(nickname, 64)
    normalized_avatar_url = _normalize_optional_text(avatar_url, 255)

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
            )
        except IntegrityError:
            db.rollback()
            raise BusinessException(message="该微信已绑定其他账号", code=4106, status_code=409)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception(f"Failed to bind WeChat for user_pk={user.id}: {exc}")
            raise BusinessException(message="微信绑定失败，请稍后重试", code=5006, status_code=500)

    if normalized_nickname:
        user.nickname = normalized_nickname
    if normalized_avatar_url:
        user.avatar_url = normalized_avatar_url

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
