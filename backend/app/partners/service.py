from __future__ import annotations

from secrets import choice

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


PARTNER_INVITE_ALPHABET = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def normalize_city_name(value: str | None) -> str:
    normalized = "".join(str(value or "").strip().lower().split())
    for suffix in ("特别行政区", "自治区", "自治州", "地区", "市"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def partner_city_key(user: User) -> str:
    city_code = str(getattr(user, "city_code", "") or "").strip().upper()
    if city_code:
        return f"code:{city_code}"[:64]
    city_name = normalize_city_name(getattr(user, "city_name", None))
    return f"name:{city_name}"[:64] if city_name else ""


def _same_city(left: User, right: User) -> bool:
    left_code = str(getattr(left, "city_code", "") or "").strip().upper()
    right_code = str(getattr(right, "city_code", "") or "").strip().upper()
    if left_code and right_code and left_code == right_code:
        return True
    left_name = normalize_city_name(getattr(left, "city_name", None))
    right_name = normalize_city_name(getattr(right, "city_name", None))
    return bool(left_name and right_name and left_name == right_name)


def find_city_partner_for_user(
    db: Session,
    user: User,
    *,
    exclude_user_pk: int | None = None,
) -> User | None:
    partners = db.scalars(
        select(User).where(
            User.partner_type == "city_partner",
            User.is_active.is_(True),
        )
    ).all()
    for partner in partners:
        if exclude_user_pk and int(partner.id) == int(exclude_user_pk):
            continue
        if _same_city(user, partner):
            return partner
    return None


def resolve_partner_invite_code(db: Session, invite_code: str | None) -> User | None:
    raw_code = str(invite_code or "").strip()
    normalized = raw_code.upper()
    if len(normalized) == 4 and all(char in PARTNER_INVITE_ALPHABET for char in normalized):
        partner = db.scalar(
            select(User).where(
                User.partner_invite_code == normalized,
                User.partner_type.in_(("salon_owner", "city_partner")),
                User.is_active.is_(True),
            ).limit(1)
        )
        if partner is not None:
            return partner

    # Previously shared links used the account ID as their code. Keep those
    # links valid for active partners while new shares use four-character codes.
    return db.scalar(
        select(User).where(
            User.user_id == raw_code,
            User.partner_type.in_(("salon_owner", "city_partner")),
            User.is_active.is_(True),
        ).limit(1)
    )


def ensure_partner_invite_code(db: Session, user: User) -> str:
    current = str(getattr(user, "partner_invite_code", "") or "").strip().upper()
    if len(current) == 4 and all(char in PARTNER_INVITE_ALPHABET for char in current):
        return current
    for _ in range(200):
        candidate = "".join(choice(PARTNER_INVITE_ALPHABET) for _ in range(4))
        exists = db.scalar(select(User.id).where(User.partner_invite_code == candidate).limit(1))
        if exists is None:
            try:
                with db.begin_nested():
                    user.partner_invite_code = candidate
                    db.add(user)
                    db.flush()
                return candidate
            except IntegrityError:
                # Retry only a competing allocation of this code.
                if db.scalar(select(User.id).where(User.partner_invite_code == candidate).limit(1)) is None:
                    raise
    raise RuntimeError("无法生成唯一合作邀请码，请稍后重试")
