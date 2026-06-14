import json
from datetime import UTC, datetime
from decimal import Decimal
import re
from pathlib import Path
from secrets import token_hex
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id, get_optional_current_user_id
from app.core.asset_urls import normalize_persisted_asset_url, sanitize_public_asset_url
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.response import success_response
from app.core.storage import upload_public_asset
from app.crud import (
    add_user_block,
    count_user_blocks,
    get_user_by_business_user_id,
    get_user_by_id,
    get_user_realtime_stats,
    get_user_verification,
    list_blocked_users,
    remove_user_block,
    update_user_profile,
)
from app.schemas.user import (
    BlockedUserItem,
    BlockedUserListData,
    BlockUserRequest,
    CircleOwnerApplicationRequest,
    PrivacySettingsData,
    UpdateCurrentUserProfileRequest,
    UpdatePrivacySettingsRequest,
)
from app.payment import consume_contact_package_view, resolve_contact_package_snapshot, resolve_member_snapshot
from app.models.circle_owner_application import CircleOwnerApplication
from app.models.user import User
from app.models.circle_interest import CircleInterest
from app.models.resource_post import ResourcePostLike
from app.models.user_interest import UserInterest
from app.review import submit_profile_update_review
from app.verification.constants import VerificationStatus, VerificationType

router = APIRouter(prefix="/user", tags=["User"])

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"
AVATAR_UPLOAD_DIR = STATIC_DIR / "uploads" / "avatars"
CARD_UPLOAD_DIR = STATIC_DIR / "uploads" / "cards"
MINIAPP_CODE_DIR = STATIC_DIR / "uploads" / "miniapp-codes"

MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024
MAX_CARD_FILE_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CONTENT_TYPE_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
}

VALID_FRIEND_REQUEST_SCOPES = {"all", "friends_of_friends", "nobody"}
VALID_MESSAGE_SCOPES = {"friends_or_contacts", "all", "mutual_follow"}
DISPLAY_PHONE_REGEX = re.compile(r"^1\d{10}$")
_WECHAT_ACCESS_TOKEN_CACHE: dict[str, str | float] = {"token": "", "expires_at": 0.0}


def _normalize_optional_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:max_len]


def _normalize_display_phone(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value, 20)
    if normalized is None:
        return None
    if not DISPLAY_PHONE_REGEX.fullmatch(normalized):
        raise BusinessException(message="展示手机号格式不正确", code=4234, status_code=400)
    return normalized


def _normalize_display_wechat(value: str | None) -> str | None:
    return _normalize_optional_text(value, 64)


def _to_public_file_url(file_url: str, request: Request) -> str:
    normalized = sanitize_public_asset_url(file_url)
    if not normalized:
        return normalized
    if normalized.startswith(("http://", "https://")):
        return normalized

    if normalized.startswith("/static/uploads/"):
        return f"{str(request.base_url).rstrip('/')}{normalized}"

    return normalized


def _to_public_avatar_url(avatar_url: str | None, request: Request) -> str:
    final_avatar_url = sanitize_public_asset_url(avatar_url, settings.DEFAULT_AVATAR_URL)
    return _to_public_file_url(final_avatar_url, request)


def _parse_card_files(card_files_json: str | None, request: Request) -> list[dict]:
    if not card_files_json:
        return []

    try:
        parsed = json.loads(card_files_json)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    result: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue

        raw_name = item.get("name")
        raw_url = item.get("url")
        raw_size = item.get("size")

        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        if not isinstance(raw_url, str) or not raw_url.strip():
            continue

        result.append(
            {
                "name": raw_name.strip()[:128],
                "url": _to_public_file_url(raw_url.strip()[:255], request),
                "size": int(raw_size) if isinstance(raw_size, int) and raw_size >= 0 else None,
            }
        )

    return result


def _to_public_static_url(path: Path, request: Request) -> str:
    relative = path.relative_to(STATIC_DIR).as_posix()
    return f"{str(request.base_url).rstrip('/')}/static/{relative}"


def _request_json(url: str, *, data: bytes | None = None) -> dict:
    req = UrlRequest(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urlopen(req, timeout=10) as resp:  # noqa: S310 - trusted WeChat API URL from settings/code.
        body = resp.read()
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _get_wechat_access_token() -> str:
    app_id = str(settings.WECHAT_MINI_APP_ID or "").strip()
    app_secret = str(settings.WECHAT_MINI_APP_SECRET or "").strip()
    if not app_id or not app_secret:
        return ""

    now = time.time()
    cached_token = str(_WECHAT_ACCESS_TOKEN_CACHE.get("token") or "")
    cached_expires_at = float(_WECHAT_ACCESS_TOKEN_CACHE.get("expires_at") or 0)
    if cached_token and cached_expires_at > now + 60:
        return cached_token

    query = urlencode(
        {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        }
    )
    payload = _request_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}")
    token = str(payload.get("access_token") or "").strip()
    if not token:
        logger.warning(f"Failed to get WeChat access_token: {payload}")
        return ""

    expires_in = int(payload.get("expires_in") or 7200)
    _WECHAT_ACCESS_TOKEN_CACHE["token"] = token
    _WECHAT_ACCESS_TOKEN_CACHE["expires_at"] = now + max(expires_in - 120, 300)
    return token


def _download_profile_miniapp_code(*, target_user_id: str, output_path: Path) -> bool:
    token = _get_wechat_access_token()
    if not token:
        return False

    payload = {
        "scene": target_user_id,
        "page": "pages/me/card/index",
        "check_path": False,
        "env_version": "release",
    }
    request_url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={token}"
    req = UrlRequest(
        request_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=15) as resp:  # noqa: S310 - trusted WeChat API URL from settings/code.
            body = resp.read()
            content_type = str(resp.headers.get("Content-Type") or "").lower()
    except URLError as exc:
        logger.warning(f"Failed to download WeChat miniapp code. target={target_user_id}, error={exc}")
        return False

    if "json" in content_type or body.startswith(b"{"):
        try:
            error_payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            error_payload = {"raw": body[:200].decode("utf-8", errors="ignore")}
        logger.warning(f"WeChat miniapp code API returned error. target={target_user_id}, payload={error_payload}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(body)
    return True


def _get_profile_miniapp_code_url(*, target_user_id: str, request: Request) -> str:
    safe_target_user_id = re.sub(r"[^A-Za-z0-9_-]", "", target_user_id)[:32]
    if not safe_target_user_id:
        return ""

    output_path = MINIAPP_CODE_DIR / f"profile_{safe_target_user_id}.png"
    if output_path.exists() and output_path.stat().st_size > 0:
        return _to_public_static_url(output_path, request)

    if _download_profile_miniapp_code(target_user_id=safe_target_user_id, output_path=output_path):
        return _to_public_static_url(output_path, request)

    return ""


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


def _resolve_interest_stats(db: Session, *, user_pk: int) -> dict:
    stats = {
        "network_interest_count": 0,
        "resource_interest_count": 0,
        "circle_interest_count": 0,
        "interest_count": 0,
    }
    try:
        network_count = db.execute(
            select(func.count(UserInterest.id)).where(UserInterest.user_pk == int(user_pk))
        ).scalar_one_or_none()
        resource_count = db.execute(
            select(func.count(ResourcePostLike.id)).where(ResourcePostLike.user_pk == int(user_pk))
        ).scalar_one_or_none()
        circle_count = db.execute(
            select(func.count(CircleInterest.id)).where(CircleInterest.user_pk == int(user_pk))
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.warning(f"Failed to query user interest stats. user_pk={user_pk}, error={exc}")
        db.rollback()
        return stats

    stats["network_interest_count"] = int(network_count or 0)
    stats["resource_interest_count"] = int(resource_count or 0)
    stats["circle_interest_count"] = int(circle_count or 0)
    stats["interest_count"] = (
        stats["network_interest_count"]
        + stats["resource_interest_count"]
        + stats["circle_interest_count"]
    )
    return stats


def _serialize_privacy_settings(user, blocked_count: int) -> dict:
    return PrivacySettingsData(
        phone_visible_to_friends=bool(user.show_contact),
        protect_real_name=bool(user.protect_real_name),
        allow_find_by_email=bool(user.allow_find_by_email),
        friend_request_scope=str(user.friend_request_scope or "all"),
        message_scope=str(user.message_scope or "friends_or_contacts"),
        allow_auto_add_friend=bool(user.allow_auto_add_friend),
        blocked_count=int(blocked_count),
    ).model_dump()


def _serialize_blocked_user(target_user, blocked_record, request: Request) -> dict:
    blocked_at = blocked_record.created_at.isoformat() if blocked_record.created_at else None
    return BlockedUserItem(
        userId=target_user.user_id,
        user_id=target_user.user_id,
        nickname=target_user.nickname,
        avatar_url=_to_public_avatar_url(target_user.avatar_url, request),
        is_verified=bool(target_user.is_verified),
        blocked_at=blocked_at,
    ).model_dump()


def _has_approved_real_name_verification(db: Session, *, user) -> bool:
    record = get_user_verification(
        db=db,
        user_pk=int(user.id),
        verify_type=VerificationType.REAL_NAME.value,
    )
    return bool(record and record.status == VerificationStatus.APPROVED.value)


def _resolve_contact_view_state(
    db: Session,
    *,
    viewer_user,
    target_user,
) -> dict:
    target_display_phone = _normalize_optional_text(target_user.display_phone, 20)
    target_display_wechat = _normalize_optional_text(target_user.display_wechat, 64)
    target_has_contact = bool(target_display_phone or target_display_wechat)
    target_contact_enabled = bool(target_user.show_contact)
    is_self = int(viewer_user.id) == int(target_user.id)

    if is_self:
        return {
            "display_phone": target_display_phone,
            "display_wechat": target_display_wechat,
            "contact_visible": bool(target_has_contact),
            "contact_locked_reason": None if target_has_contact else "你还未完善展示手机号或微信号",
            "target_has_contact": target_has_contact,
            "target_contact_enabled": target_contact_enabled,
            "viewer_contact_package_remaining_views": 0,
            "viewer_contact_package_used_for_view": False,
        }

    viewer_display_phone = _normalize_optional_text(viewer_user.display_phone, 20)
    viewer_display_wechat = _normalize_optional_text(viewer_user.display_wechat, 64)
    viewer_real_name_verified = _has_approved_real_name_verification(db=db, user=viewer_user)
    viewer_member_snapshot = resolve_member_snapshot(db=db, user_pk=int(viewer_user.id))
    viewer_is_yearly_member = bool(viewer_member_snapshot["is_member"]) and str(
        viewer_member_snapshot.get("member_plan_id") or viewer_member_snapshot.get("plan_id") or ""
    ).strip() == "yearly"
    viewer_contact_package_snapshot = resolve_contact_package_snapshot(db=db, user_pk=int(viewer_user.id))
    viewer_has_contact_package = bool(viewer_contact_package_snapshot["has_remaining_views"])

    locked_reason = None
    if not target_contact_enabled:
        locked_reason = "对方暂未开启联系方式展示"
    elif not target_has_contact:
        locked_reason = "对方暂未填写展示联系方式"
    elif not (viewer_display_phone and viewer_display_wechat):
        locked_reason = "请先完善自己的展示手机号和微信号"
    elif not viewer_real_name_verified:
        locked_reason = "完成实名认证后可查看对方联系方式"
    elif viewer_is_yearly_member:
        locked_reason = None
    elif viewer_has_contact_package:
        locked_reason = "消耗1人脉值可查看该用户联系方式"
    else:
        locked_reason = "开通年度会员或购买人群包后可查看对方联系方式"

    contact_visible = locked_reason is None
    return {
        "display_phone": target_display_phone if contact_visible else None,
        "display_wechat": target_display_wechat if contact_visible else None,
        "contact_visible": contact_visible,
        "contact_locked_reason": locked_reason,
        "target_has_contact": target_has_contact,
        "target_contact_enabled": target_contact_enabled,
        "viewer_contact_package_remaining_views": int(viewer_contact_package_snapshot["remaining_views"]),
        "viewer_contact_package_used_for_view": False,
    }


def _unlock_contact_with_package(
    db: Session,
    *,
    viewer_user,
    target_user,
) -> dict:
    target_display_phone = _normalize_optional_text(target_user.display_phone, 20)
    target_display_wechat = _normalize_optional_text(target_user.display_wechat, 64)
    target_has_contact = bool(target_display_phone or target_display_wechat)
    target_contact_enabled = bool(target_user.show_contact)

    if int(viewer_user.id) == int(target_user.id):
        return {
            "display_phone": target_display_phone,
            "display_wechat": target_display_wechat,
            "contact_visible": bool(target_has_contact),
            "contact_locked_reason": None if target_has_contact else "你还未完善展示手机号或微信号",
            "target_has_contact": target_has_contact,
            "target_contact_enabled": target_contact_enabled,
            "viewer_contact_package_remaining_views": 0,
            "viewer_contact_package_used_for_view": False,
        }

    if not target_contact_enabled:
        raise BusinessException(message="对方暂未开启联系方式展示", code=4561, status_code=403)
    if not target_has_contact:
        raise BusinessException(message="对方暂未填写展示联系方式", code=4562, status_code=403)

    viewer_display_phone = _normalize_optional_text(viewer_user.display_phone, 20)
    viewer_display_wechat = _normalize_optional_text(viewer_user.display_wechat, 64)
    if not (viewer_display_phone and viewer_display_wechat):
        raise BusinessException(message="请先完善自己的展示手机号和微信号", code=4563, status_code=403)

    if not _has_approved_real_name_verification(db=db, user=viewer_user):
        raise BusinessException(message="完成实名认证后可查看对方联系方式", code=4564, status_code=403)

    viewer_member_snapshot = resolve_member_snapshot(db=db, user_pk=int(viewer_user.id))
    viewer_is_yearly_member = bool(viewer_member_snapshot["is_member"]) and str(
        viewer_member_snapshot.get("member_plan_id") or viewer_member_snapshot.get("plan_id") or ""
    ).strip() == "yearly"

    if viewer_is_yearly_member:
        viewer_contact_package_snapshot = resolve_contact_package_snapshot(db=db, user_pk=int(viewer_user.id))
        used_for_view = False
    else:
        current_contact_package_snapshot = resolve_contact_package_snapshot(db=db, user_pk=int(viewer_user.id))
        if not bool(current_contact_package_snapshot["has_remaining_views"]):
            raise BusinessException(message="人群包剩余次数不足", code=4565, status_code=403)
        viewer_contact_package_snapshot = consume_contact_package_view(
            db=db,
            user_pk=int(viewer_user.id),
            commit=True,
        )
        used_for_view = True

    return {
        "display_phone": target_display_phone,
        "display_wechat": target_display_wechat,
        "contact_visible": True,
        "contact_locked_reason": None,
        "target_has_contact": target_has_contact,
        "target_contact_enabled": target_contact_enabled,
        "viewer_contact_package_remaining_views": int(viewer_contact_package_snapshot["remaining_views"]),
        "viewer_contact_package_used_for_view": used_for_view,
    }


def _serialize_user(user, request: Request, db: Session) -> dict:
    stats = _resolve_user_stats(db=db, user=user)
    interest_stats = _resolve_interest_stats(db=db, user_pk=int(user.id))
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(user.id))
    contact_package_snapshot = resolve_contact_package_snapshot(db=db, user_pk=int(user.id))
    circle_owner_application = db.scalar(
        select(CircleOwnerApplication).where(CircleOwnerApplication.user_pk == int(user.id))
    )
    real_name_verified = _has_approved_real_name_verification(db=db, user=user)
    display_phone = _normalize_optional_text(user.display_phone, 20)
    display_wechat = _normalize_optional_text(user.display_wechat, 64)
    email = _normalize_optional_text(user.email, 100)

    # 获取关注数和粉丝数（如果表不存在则返回0）
    following_count = 0
    fans_count = 0
    try:
        from app.crud.network import get_user_following_count, get_user_fans_count
        following_count = get_user_following_count(db=db, user_pk=int(user.id))
        fans_count = get_user_fans_count(db=db, user_pk=int(user.id))
    except Exception as e:
        # 如果user_follows表还不存在，忽略错误
        pass

    # 获取用户发布的活动数量
    activity_count = 0
    try:
        from app.models.resource_post import ResourcePost
        activity_count = db.scalar(
            select(func.count(ResourcePost.id))
            .where(
                ResourcePost.author_user_pk == user.id,
                ResourcePost.mode == "venue",
                ResourcePost.status == "active"
            )
        ) or 0
    except Exception:
        pass

    return {
        "userId": user.user_id,
        "user_id": user.user_id,
        "phone": user.phone,
        "display_phone": display_phone,
        "display_wechat": display_wechat,
        "email": email,
        "display_email": email,
        "wechat_bound": bool(user.wechat_openid),
        "wechat_bound_at": user.wechat_bound_at.isoformat() if user.wechat_bound_at else None,
        "nickname": user.nickname,
        "avatar_url": _to_public_avatar_url(user.avatar_url, request),
        "miniapp_code_url": _get_profile_miniapp_code_url(target_user_id=user.user_id, request=request),
        "is_verified": bool(user.is_verified),
        "is_circle_owner": bool(user.is_circle_owner),
        "circle_owner_application_status": (
            str(circle_owner_application.status) if circle_owner_application is not None else ""
        ),
        "intro": user.intro,
        "industry_code": user.industry_code,
        "industry_label": user.industry_label,
        "company_name": user.company_name,
        "job_title": user.job_title,
        "city_code": user.city_code,
        "city_name": user.city_name,
        "latitude": float(user.latitude) if user.latitude is not None else None,
        "longitude": float(user.longitude) if user.longitude is not None else None,
        "card_files": _parse_card_files(user.card_files_json, request),
        "show_contact": bool(user.show_contact),
        "protect_real_name": bool(user.protect_real_name),
        "allow_find_by_email": bool(user.allow_find_by_email),
        "friend_request_scope": str(user.friend_request_scope or "all"),
        "message_scope": str(user.message_scope or "friends_or_contacts"),
        "allow_auto_add_friend": bool(user.allow_auto_add_friend),
        "circle_count": int(stats["circle_count"] or 0),
        "network_count": int(stats["network_count"] or 0),
        "interest_count": int(interest_stats["interest_count"] or 0),
        "interested_count": int(interest_stats["interest_count"] or 0),
        "follow_favorite_count": int(interest_stats["interest_count"] or 0),
        "network_interest_count": int(interest_stats["network_interest_count"] or 0),
        "resource_interest_count": int(interest_stats["resource_interest_count"] or 0),
        "circle_interest_count": int(interest_stats["circle_interest_count"] or 0),
        "following_count": int(following_count),
        "follow_count": int(following_count),
        "fans_count": int(fans_count),
        "follower_count": int(fans_count),
        "activity_count": int(activity_count),
        "event_count": int(activity_count),
        "points": int(stats.get("points") or 0),
        "available_points": int(stats.get("available_points") or 0),
        "frozen_points": int(stats.get("frozen_points") or 0),
        "balance": float(stats["balance"] or 0),
        "invite_code": str(user.user_id or "").strip() or None,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "is_member": bool(member_snapshot["is_member"]),
        "member_opened": bool(member_snapshot["member_opened"]),
        "is_vip": bool(member_snapshot["is_vip"]),
        "vip_opened": bool(member_snapshot["vip_opened"]),
        "member_status": str(member_snapshot["member_status"]),
        "vip_status": str(member_snapshot["vip_status"]),
        "member_expire_at": member_snapshot["member_expire_at"],
        "vip_expire_at": member_snapshot["vip_expire_at"],
        "member_plan_id": str(member_snapshot["member_plan_id"]),
        "member_plan_name": str(member_snapshot["member_plan_name"]),
        "real_name_verified": bool(real_name_verified),
        "contact_package_remaining_views": int(contact_package_snapshot["remaining_views"]),
        "contact_package_used_views": int(contact_package_snapshot["used_views"]),
        "contact_package_purchased_views": int(contact_package_snapshot["purchased_views"]),
        "can_view_others_contact": bool(
            display_phone
            and display_wechat
            and real_name_verified
            and (member_snapshot["is_member"] or contact_package_snapshot["has_remaining_views"])
        ),
    }


def _serialize_public_user_profile(
    target_user,
    request: Request,
    db: Session,
    *,
    viewer_user_pk: int | None,
) -> dict:
    stats = _resolve_user_stats(db=db, user=target_user)
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(target_user.id))
    if viewer_user_pk is not None:
        viewer = _require_current_user(db=db, current_user_pk=viewer_user_pk)
        contact_state = _resolve_contact_view_state(
            db=db,
            viewer_user=viewer,
            target_user=target_user,
        )
    else:
        contact_state = {
            "display_phone": "",
            "display_wechat": "",
            "contact_visible": False,
            "contact_locked_reason": "登录后可查看联系方式",
            "target_has_contact": bool(
                str(target_user.display_phone or "").strip()
                or str(target_user.display_wechat or "").strip()
            ),
            "target_contact_enabled": bool(target_user.show_contact),
            "viewer_contact_package_remaining_views": 0,
            "viewer_contact_package_used_for_view": False,
        }
    return {
        "userId": target_user.user_id,
        "user_id": target_user.user_id,
        "nickname": target_user.nickname,
        "avatar_url": _to_public_avatar_url(target_user.avatar_url, request),
        "is_verified": bool(target_user.is_verified),
        "intro": target_user.intro,
        "industry_code": target_user.industry_code,
        "industry_label": target_user.industry_label,
        "company_name": target_user.company_name,
        "job_title": target_user.job_title,
        "city_code": target_user.city_code,
        "city_name": target_user.city_name,
        "card_files": _parse_card_files(target_user.card_files_json, request),
        "circle_count": int(stats["circle_count"] or 0),
        "network_count": int(stats["network_count"] or 0),
        "is_active": bool(target_user.is_active),
        "is_self": bool(viewer_user_pk is not None and int(target_user.id) == int(viewer_user_pk)),
        "created_at": target_user.created_at.isoformat() if target_user.created_at else None,
        "last_login_at": target_user.last_login_at.isoformat() if target_user.last_login_at else None,
        "is_member": bool(member_snapshot["is_member"]),
        "member_status": str(member_snapshot["member_status"]),
        "member_expire_at": member_snapshot["member_expire_at"],
        "member_plan_name": str(member_snapshot["member_plan_name"]),
        "display_phone": contact_state["display_phone"],
        "display_wechat": contact_state["display_wechat"],
        "contact_visible": contact_state["contact_visible"],
        "contact_locked_reason": contact_state["contact_locked_reason"],
        "target_has_contact": contact_state["target_has_contact"],
        "target_contact_enabled": contact_state["target_contact_enabled"],
        "viewer_contact_package_remaining_views": int(contact_state["viewer_contact_package_remaining_views"] or 0),
        "viewer_contact_package_used_for_view": bool(contact_state["viewer_contact_package_used_for_view"]),
    }


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)
    return user


@router.get("/me", summary="Get current user profile")
def get_current_user_profile(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    return success_response(data=_serialize_user(user, request, db))


def _serialize_circle_owner_application(
    *,
    user: User,
    application: CircleOwnerApplication | None,
    db: Session,
) -> dict:
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(user.id))
    yearly_member = bool(member_snapshot["is_member"]) and str(
        member_snapshot.get("member_plan_id") or member_snapshot.get("plan_id") or ""
    ).strip() == "yearly"

    return {
        "is_circle_owner": bool(user.is_circle_owner),
        "is_yearly_member": yearly_member,
        "member_plan_id": str(member_snapshot.get("member_plan_id") or ""),
        "member_plan_name": str(member_snapshot.get("member_plan_name") or ""),
        "status": (
            "approved"
            if bool(user.is_circle_owner)
            else str(application.status or "") if application is not None else ""
        ),
        "reason": str(application.reason or "") if application is not None else "",
        "experience": str(application.experience or "") if application is not None else "",
        "reject_reason": str(application.reject_reason or "") if application is not None else "",
        "submitted_at": application.created_at.isoformat() if application and application.created_at else None,
        "reviewed_at": application.reviewed_at.isoformat() if application and application.reviewed_at else None,
    }


@router.get("/me/circle-owner-application", summary="Get circle owner application status")
def get_circle_owner_application(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    application = db.scalar(
        select(CircleOwnerApplication).where(CircleOwnerApplication.user_pk == int(user.id))
    )
    return success_response(
        data=_serialize_circle_owner_application(user=user, application=application, db=db)
    )


@router.post("/me/circle-owner-application", summary="Apply to become a circle owner")
def apply_for_circle_owner(
    payload: CircleOwnerApplicationRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    del payload, user_id, db
    raise BusinessException(
        message="圈主已改为一次付费永久开通，请前往圈主开通页面购买",
        code=4367,
        status_code=410,
    )


@router.get("/profiles/{target_user_id}", summary="Get public profile by business user id")
def get_public_user_profile(
    target_user_id: str,
    request: Request,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is not None:
        _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = str(target_user_id or "").strip()
    if len(normalized_target_user_id) != 8:
        raise BusinessException(message="目标用户ID格式无效", code=4233, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None or not bool(target_user.is_active):
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    return success_response(
        data=_serialize_public_user_profile(
            target_user=target_user,
            request=request,
            db=db,
            viewer_user_pk=user_id,
        )
    )


@router.post("/profiles/{target_user_id}/contact-unlock", summary="Unlock public profile contact with contact package")
def unlock_public_user_profile_contact(
    target_user_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = str(target_user_id or "").strip()
    if len(normalized_target_user_id) != 8:
        raise BusinessException(message="目标用户ID格式无效", code=4233, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None or not bool(target_user.is_active):
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    return success_response(
        data=_unlock_contact_with_package(
            db=db,
            viewer_user=viewer,
            target_user=target_user,
        )
    )


@router.get("/profiles/{target_user_id}/miniapp-code", summary="Get profile miniapp code")
def get_profile_miniapp_code(
    target_user_id: str,
    request: Request,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is not None:
        _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = str(target_user_id or "").strip()
    if len(normalized_target_user_id) != 8:
        raise BusinessException(message="目标用户ID格式无效", code=4233, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None or not bool(target_user.is_active):
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    return success_response(
        data={
            "miniapp_code_url": _get_profile_miniapp_code_url(
                target_user_id=normalized_target_user_id,
                request=request,
            )
        }
    )


@router.patch("/me", summary="Update current user profile")
def update_current_user_profile(
    payload: UpdateCurrentUserProfileRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    updates: dict = {}
    if (payload.latitude is None) != (payload.longitude is None):
        raise BusinessException(message="经纬度必须同时提交", code=4234, status_code=400)

    if payload.nickname is not None:
        normalized_nickname = payload.nickname.strip()
        if not normalized_nickname:
            raise BusinessException(message="昵称不能为空", code=4221, status_code=400)
        updates["nickname"] = normalized_nickname[:64]

    if payload.avatar_url is not None:
        normalized_avatar = normalize_persisted_asset_url(
            payload.avatar_url,
            request=request,
            field_label="头像",
            allow_empty=True,
        )
        updates["avatar_url"] = normalized_avatar[:255] if normalized_avatar else settings.DEFAULT_AVATAR_URL

    if payload.intro is not None:
        updates["intro"] = _normalize_optional_text(payload.intro, 255)

    if payload.industry_code is not None:
        updates["industry_code"] = _normalize_optional_text(payload.industry_code, 32)

    if payload.industry_label is not None:
        updates["industry_label"] = _normalize_optional_text(payload.industry_label, 64)

    if payload.company_name is not None:
        updates["company_name"] = _normalize_optional_text(payload.company_name, 128)

    if payload.job_title is not None:
        updates["job_title"] = _normalize_optional_text(payload.job_title, 64)

    if payload.display_phone is not None:
        updates["display_phone"] = _normalize_display_phone(payload.display_phone)

    if payload.display_wechat is not None:
        updates["display_wechat"] = _normalize_display_wechat(payload.display_wechat)

    if payload.email is not None:
        updates["email"] = _normalize_optional_text(payload.email, 100)

    if payload.city_code is not None:
        updates["city_code"] = _normalize_optional_text(payload.city_code, 16)

    if payload.city_name is not None:
        updates["city_name"] = _normalize_optional_text(payload.city_name, 32)

    if payload.latitude is not None:
        updates["latitude"] = Decimal(str(payload.latitude)).quantize(Decimal("0.0000001"))

    if payload.longitude is not None:
        updates["longitude"] = Decimal(str(payload.longitude)).quantize(Decimal("0.0000001"))

    if payload.card_files is not None:
        normalized_files = []
        for item in payload.card_files[:10]:
            file_name = item.name.strip()
            file_url = normalize_persisted_asset_url(
                item.url,
                request=request,
                field_label="名片附件",
            )
            if not file_name or not file_url:
                continue
            normalized_files.append(
                {
                    "name": file_name[:128],
                    "url": file_url[:255],
                    "size": item.size if isinstance(item.size, int) and item.size >= 0 else None,
                }
            )
        updates["card_files_json"] = json.dumps(normalized_files, ensure_ascii=False)

    if payload.show_contact is not None:
        updates["show_contact"] = bool(payload.show_contact)

    updates = {
        field_name: field_value
        for field_name, field_value in updates.items()
        if getattr(user, field_name) != field_value
    }

    if not updates:
        raise BusinessException(message="没有可更新的字段", code=4222, status_code=400)

    coordinate_updates = {
        field_name: updates.pop(field_name)
        for field_name in ("latitude", "longitude")
        if field_name in updates
    }

    try:
        if coordinate_updates and not updates:
            user = update_user_profile(db=db, user=user, **coordinate_updates)
            payload = _serialize_user(user, request, db)
            payload["_review"] = {
                "review_required": False,
                "fee_paid": False,
                "fee_amount": 0,
            }
            return success_response(data=payload, message="保存成功")

        for field_name, field_value in coordinate_updates.items():
            setattr(user, field_name, field_value)
        if coordinate_updates:
            db.add(user)

        review_result = submit_profile_update_review(
            db=db,
            user=user,
            updates=updates,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="更新资料失败，请稍后重试", code=5004, status_code=500) from exc

    payload = _serialize_user(user, request, db)
    payload["_review"] = review_result["review"]
    review_required = bool(review_result["review"]["review_required"])
    return success_response(
        data=payload,
        message="资料已提交审核" if review_required else "保存成功",
    )


@router.get("/me/privacy", summary="Get current user privacy settings")
def get_current_user_privacy_settings(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    blocked_count = count_user_blocks(db=db, user_pk=user.id)
    return success_response(data=_serialize_privacy_settings(user, blocked_count=blocked_count))


@router.patch("/me/privacy", summary="Update current user privacy settings")
def update_current_user_privacy_settings(
    payload: UpdatePrivacySettingsRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    updates: dict = {}

    if payload.phone_visible_to_friends is not None:
        updates["show_contact"] = bool(payload.phone_visible_to_friends)

    if payload.protect_real_name is not None:
        updates["protect_real_name"] = bool(payload.protect_real_name)

    if payload.allow_find_by_email is not None:
        updates["allow_find_by_email"] = bool(payload.allow_find_by_email)

    if payload.friend_request_scope is not None:
        scope = payload.friend_request_scope.strip()
        if scope not in VALID_FRIEND_REQUEST_SCOPES:
            raise BusinessException(message="好友请求权限值无效", code=4229, status_code=400)
        updates["friend_request_scope"] = scope

    if payload.message_scope is not None:
        scope = payload.message_scope.strip()
        if scope not in VALID_MESSAGE_SCOPES:
            raise BusinessException(message="私信接收范围值无效", code=4230, status_code=400)
        updates["message_scope"] = scope

    if payload.allow_auto_add_friend is not None:
        updates["allow_auto_add_friend"] = bool(payload.allow_auto_add_friend)

    if not updates:
        raise BusinessException(message="没有可更新的字段", code=4222, status_code=400)

    try:
        user = update_user_profile(db=db, user=user, **updates)
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="隐私设置更新失败，请稍后重试", code=5009, status_code=500) from exc

    blocked_count = count_user_blocks(db=db, user_pk=user.id)
    return success_response(
        data=_serialize_privacy_settings(user, blocked_count=blocked_count),
        message="保存成功",
    )


@router.get("/me/blocked-users", summary="List blocked users of current user")
def get_current_user_blocked_users(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    safe_offset = max(offset, 0)
    safe_limit = min(max(limit, 1), 100)
    rows, total = list_blocked_users(
        db=db,
        user_pk=user.id,
        offset=safe_offset,
        limit=safe_limit,
    )

    items = [
        _serialize_blocked_user(target_user=target_user, blocked_record=blocked_record, request=request)
        for target_user, blocked_record in rows
    ]
    payload = BlockedUserListData(
        items=items,
        total=int(total),
        offset=safe_offset,
        limit=safe_limit,
    ).model_dump()
    return success_response(data=payload)


@router.post("/me/blocked-users", summary="Add a blocked user for current user")
def add_current_user_blocked_user(
    payload: BlockUserRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    target_business_user_id = payload.target_user_id.strip()
    target_user = get_user_by_business_user_id(db=db, business_user_id=target_business_user_id)
    if target_user is None:
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    if target_user.id == user.id:
        raise BusinessException(message="不能将自己加入黑名单", code=4231, status_code=400)

    try:
        block_record, created = add_user_block(
            db=db,
            user_pk=user.id,
            blocked_user_pk=target_user.id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="加入黑名单失败，请稍后重试", code=5010, status_code=500) from exc

    return success_response(
        data={
            "blocked_user": _serialize_blocked_user(
                target_user=target_user,
                blocked_record=block_record,
                request=request,
            ),
            "created": bool(created),
        },
        message="已加入黑名单" if created else "该用户已在黑名单中",
    )


@router.delete("/me/blocked-users/{target_user_id}", summary="Remove a blocked user for current user")
def remove_current_user_blocked_user(
    target_user_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = (target_user_id or "").strip()
    if not normalized_target_user_id:
        raise BusinessException(message="目标用户ID不能为空", code=4232, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None:
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    try:
        removed = remove_user_block(
            db=db,
            user_pk=user.id,
            blocked_user_pk=target_user.id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="移出黑名单失败，请稍后重试", code=5011, status_code=500) from exc

    return success_response(
        data={
            "removed": bool(removed),
            "target_user_id": target_user.user_id,
        },
        message="已移出黑名单" if removed else "该用户不在黑名单中",
    )


@router.post("/me/avatar", summary="Upload avatar for current user")
async def upload_current_user_avatar(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or "").lower().strip()
    if not content_type.startswith("image/"):
        raise BusinessException(message="头像文件仅支持图片格式", code=4223, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=4224, status_code=400)

    if len(file_bytes) > MAX_AVATAR_SIZE_BYTES:
        raise BusinessException(message="头像文件不能超过 5MB", code=4225, status_code=400)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        suffix = CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".jpg")

    stored = upload_public_asset(
        prefix="uploads/avatars",
        file_bytes=file_bytes,
        suffix=suffix,
        content_type=content_type,
        request=request,
    )

    try:
        user = update_user_profile(db=db, user=user, avatar_url=stored.path)
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="头像更新失败，请稍后重试", code=5005, status_code=500) from exc

    return success_response(
        data={
            "avatar_url": _to_public_avatar_url(user.avatar_url, request),
        },
        message="头像上传成功",
    )


@router.post("/me/card-file", summary="Upload business card attachment for current user")
async def upload_current_user_card_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or "").lower().strip()
    if content_type not in {"image/jpeg", "image/png", "image/webp", "application/pdf"}:
        raise BusinessException(message="附件仅支持 JPG/PNG/WEBP/PDF", code=4226, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=4227, status_code=400)

    if len(file_bytes) > MAX_CARD_FILE_SIZE_BYTES:
        raise BusinessException(message="附件文件不能超过 10MB", code=4228, status_code=400)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        suffix = CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".pdf")

    stored = upload_public_asset(
        prefix="uploads/cards",
        file_bytes=file_bytes,
        suffix=suffix,
        content_type=content_type,
        request=request,
    )
    display_name = (file.filename or "附件").strip() or "附件"
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            "name": display_name,
            "url": stored.url,
            "path": stored.path,
            "size": len(file_bytes),
        },
        message="附件上传成功",
    )


@router.get("/ping", summary="User module placeholder endpoint")
def user_ping():
    return success_response(message="user module placeholder")


@router.get("/me/following", summary="Get my following list")
def get_my_following_list(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """获取当前用户的关注列表"""
    from app.models.user_follow import UserFollow

    viewer = _require_current_user(db=db, current_user_pk=user_id)

    # 查询关注的用户
    stmt = (
        select(User)
        .join(UserFollow, UserFollow.following_user_pk == User.id)
        .where(
            UserFollow.follower_user_pk == viewer.id,
            User.is_active.is_(True)
        )
        .order_by(UserFollow.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
    )

    users = list(db.execute(stmt).scalars().all())
    has_more = len(users) > limit
    if has_more:
        users = users[:limit]

    # 序列化用户信息
    items = []
    for user in users:
        items.append({
            "user_id": user.user_id,
            "userId": user.user_id,
            "nickname": user.nickname,
            "avatar_url": _to_public_avatar_url(user.avatar_url, request),
            "intro": user.intro,
            "industry_label": user.industry_label,
            "city_name": user.city_name,
            "company_name": user.company_name,
            "job_title": user.job_title,
            "is_verified": bool(user.is_verified),
        })

    return success_response(
        data={
            "items": items,
            "has_more": has_more,
            "total": len(items)
        }
    )


@router.get("/me/followers", summary="Get my followers list")
def get_my_followers_list(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """获取当前用户的粉丝列表"""
    from app.models.user_follow import UserFollow
    from app.crud.network import get_user_follows

    viewer = _require_current_user(db=db, current_user_pk=user_id)

    # 查询粉丝（关注我的用户）
    stmt = (
        select(User)
        .join(UserFollow, UserFollow.follower_user_pk == User.id)
        .where(
            UserFollow.following_user_pk == viewer.id,
            User.is_active.is_(True)
        )
        .order_by(UserFollow.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
    )

    users = list(db.execute(stmt).scalars().all())
    has_more = len(users) > limit
    if has_more:
        users = users[:limit]

    # 查询我是否关注了这些粉丝（判断是否互相关注）
    user_pks = {int(user.id) for user in users}
    follow_back_status = get_user_follows(
        db=db,
        follower_user_pk=viewer.id,
        following_user_pks=user_pks
    )

    # 序列化用户信息
    items = []
    for user in users:
        items.append({
            "user_id": user.user_id,
            "userId": user.user_id,
            "nickname": user.nickname,
            "avatar_url": _to_public_avatar_url(user.avatar_url, request),
            "intro": user.intro,
            "industry_label": user.industry_label,
            "city_name": user.city_name,
            "company_name": user.company_name,
            "job_title": user.job_title,
            "is_verified": bool(user.is_verified),
            "is_followed_back": follow_back_status.get(int(user.id), False),
            "followed": follow_back_status.get(int(user.id), False),
        })

    return success_response(
        data={
            "items": items,
            "has_more": has_more,
            "total": len(items)
        }
    )
