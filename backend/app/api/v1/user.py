import json
from datetime import UTC, datetime
import re
from pathlib import Path
from secrets import token_hex

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.response import success_response
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
    PrivacySettingsData,
    UpdateCurrentUserProfileRequest,
    UpdatePrivacySettingsRequest,
)
from app.payment import resolve_member_snapshot
from app.review import submit_profile_update_review
from app.verification.constants import VerificationStatus, VerificationType

router = APIRouter(prefix="/user", tags=["User"])

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"
AVATAR_UPLOAD_DIR = STATIC_DIR / "uploads" / "avatars"
CARD_UPLOAD_DIR = STATIC_DIR / "uploads" / "cards"

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
    if file_url.startswith(("http://", "https://", "data:image/", "wxfile://")):
        return file_url

    if file_url.startswith("/static/uploads/"):
        return f"{str(request.base_url).rstrip('/')}{file_url}"

    return file_url


def _to_public_avatar_url(avatar_url: str | None, request: Request) -> str:
    final_avatar_url = avatar_url or settings.DEFAULT_AVATAR_URL
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
        }

    viewer_display_phone = _normalize_optional_text(viewer_user.display_phone, 20)
    viewer_display_wechat = _normalize_optional_text(viewer_user.display_wechat, 64)
    viewer_real_name_verified = _has_approved_real_name_verification(db=db, user=viewer_user)
    viewer_member_snapshot = resolve_member_snapshot(db=db, user_pk=int(viewer_user.id))
    viewer_is_member = bool(viewer_member_snapshot["is_member"])

    locked_reason = None
    if not target_contact_enabled:
        locked_reason = "对方暂未开启联系方式展示"
    elif not target_has_contact:
        locked_reason = "对方暂未填写展示联系方式"
    elif not (viewer_display_phone and viewer_display_wechat):
        locked_reason = "请先完善自己的展示手机号和微信号"
    elif not viewer_real_name_verified:
        locked_reason = "完成实名认证后可查看对方联系方式"
    elif not viewer_is_member:
        locked_reason = "开通会员后可查看对方联系方式"

    contact_visible = locked_reason is None
    return {
        "display_phone": target_display_phone if contact_visible else None,
        "display_wechat": target_display_wechat if contact_visible else None,
        "contact_visible": contact_visible,
        "contact_locked_reason": locked_reason,
        "target_has_contact": target_has_contact,
        "target_contact_enabled": target_contact_enabled,
    }


def _serialize_user(user, request: Request, db: Session) -> dict:
    stats = _resolve_user_stats(db=db, user=user)
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(user.id))
    real_name_verified = _has_approved_real_name_verification(db=db, user=user)
    display_phone = _normalize_optional_text(user.display_phone, 20)
    display_wechat = _normalize_optional_text(user.display_wechat, 64)

    return {
        "userId": user.user_id,
        "user_id": user.user_id,
        "phone": user.phone,
        "display_phone": display_phone,
        "display_wechat": display_wechat,
        "wechat_bound": bool(user.wechat_openid),
        "wechat_bound_at": user.wechat_bound_at.isoformat() if user.wechat_bound_at else None,
        "nickname": user.nickname,
        "avatar_url": _to_public_avatar_url(user.avatar_url, request),
        "is_verified": bool(user.is_verified),
        "intro": user.intro,
        "industry_code": user.industry_code,
        "industry_label": user.industry_label,
        "company_name": user.company_name,
        "job_title": user.job_title,
        "city_code": user.city_code,
        "city_name": user.city_name,
        "card_files": _parse_card_files(user.card_files_json, request),
        "show_contact": bool(user.show_contact),
        "protect_real_name": bool(user.protect_real_name),
        "allow_find_by_email": bool(user.allow_find_by_email),
        "friend_request_scope": str(user.friend_request_scope or "all"),
        "message_scope": str(user.message_scope or "friends_or_contacts"),
        "allow_auto_add_friend": bool(user.allow_auto_add_friend),
        "circle_count": int(stats["circle_count"] or 0),
        "network_count": int(stats["network_count"] or 0),
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
        "can_view_others_contact": bool(
            display_phone and display_wechat and real_name_verified and member_snapshot["is_member"]
        ),
    }


def _serialize_public_user_profile(
    target_user,
    request: Request,
    db: Session,
    *,
    viewer_user_pk: int,
) -> dict:
    stats = _resolve_user_stats(db=db, user=target_user)
    member_snapshot = resolve_member_snapshot(db=db, user_pk=int(target_user.id))
    viewer = _require_current_user(db=db, current_user_pk=viewer_user_pk)
    contact_state = _resolve_contact_view_state(
        db=db,
        viewer_user=viewer,
        target_user=target_user,
    )
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
        "is_self": bool(int(target_user.id) == int(viewer_user_pk)),
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


@router.get("/profiles/{target_user_id}", summary="Get public profile by business user id")
def get_public_user_profile(
    target_user_id: str,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
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


@router.patch("/me", summary="Update current user profile")
def update_current_user_profile(
    payload: UpdateCurrentUserProfileRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)

    updates: dict = {}

    if payload.nickname is not None:
        normalized_nickname = payload.nickname.strip()
        if not normalized_nickname:
            raise BusinessException(message="昵称不能为空", code=4221, status_code=400)
        updates["nickname"] = normalized_nickname[:64]

    if payload.avatar_url is not None:
        normalized_avatar = payload.avatar_url.strip()
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

    if payload.city_code is not None:
        updates["city_code"] = _normalize_optional_text(payload.city_code, 16)

    if payload.city_name is not None:
        updates["city_name"] = _normalize_optional_text(payload.city_name, 32)

    if payload.card_files is not None:
        normalized_files = []
        for item in payload.card_files[:10]:
            file_name = item.name.strip()
            file_url = item.url.strip()
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

    try:
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

    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = AVATAR_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    avatar_path = f"/static/uploads/avatars/{file_name}"

    try:
        user = update_user_profile(db=db, user=user, avatar_url=avatar_path)
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

    CARD_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = CARD_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f"/static/uploads/cards/{file_name}"
    display_name = (file.filename or "附件").strip() or "附件"
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            "name": display_name,
            "url": _to_public_file_url(relative_url, request),
            "size": len(file_bytes),
        },
        message="附件上传成功",
    )


@router.get("/ping", summary="User module placeholder endpoint")
def user_ping():
    return success_response(message="user module placeholder")
