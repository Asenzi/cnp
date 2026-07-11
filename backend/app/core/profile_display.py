from app.core.config import settings


def review_status(user, field_name: str) -> str:
    return str(getattr(user, f"{field_name}_review_status", "approved") or "approved").strip()


def public_avatar_url(user) -> str:
    if review_status(user, "avatar") != "approved":
        return settings.DEFAULT_AVATAR_URL
    return str(getattr(user, "avatar_url", "") or "").strip() or settings.DEFAULT_AVATAR_URL


def public_nickname(user) -> str:
    if review_status(user, "nickname") != "approved":
        return f"用户{str(getattr(user, 'user_id', '') or '')[-4:] or '0000'}"
    return str(getattr(user, "nickname", "") or "").strip() or "未命名用户"


def public_intro(user) -> str | None:
    if review_status(user, "intro") != "approved":
        return None
    value = str(getattr(user, "intro", "") or "").strip()
    return value or None
