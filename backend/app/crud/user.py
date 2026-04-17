from datetime import UTC, datetime
from random import randint

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.models.user import User


def get_user_by_phone(db: Session, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_wechat_openid(db: Session, wechat_openid: str) -> User | None:
    stmt = select(User).where(User.wechat_openid == wechat_openid)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_business_user_id(db: Session, business_user_id: str) -> User | None:
    stmt = select(User).where(User.user_id == business_user_id)
    return db.execute(stmt).scalar_one_or_none()


def _generate_business_user_id() -> str:
    timestamp_tail = str(int(datetime.now(UTC).timestamp() * 1000))[-5:]
    random_tail = f"{randint(0, 999):03d}"
    return f"{timestamp_tail}{random_tail}"


def create_user(
    db: Session,
    phone: str,
    nickname: str,
    avatar_url: str | None = None,
    intro: str | None = None,
    industry_code: str | None = None,
    industry_label: str | None = None,
    company_name: str | None = None,
    show_contact: bool = False,
    business_user_id: str | None = None,
    is_verified: bool = False,
    wechat_openid: str | None = None,
    wechat_unionid: str | None = None,
    wechat_bound_at: datetime | None = None,
    inviter_user_pk: int | None = None,
) -> User:
    resolved_avatar_url = avatar_url.strip() if isinstance(avatar_url, str) else ""
    if not resolved_avatar_url:
        resolved_avatar_url = settings.DEFAULT_AVATAR_URL

    provided_business_user_id = (
        business_user_id.strip() if isinstance(business_user_id, str) else ""
    )
    max_attempts = 1 if provided_business_user_id else 20

    for _ in range(max_attempts):
        candidate_user_id = provided_business_user_id or _generate_business_user_id()

        user = User(
            user_id=candidate_user_id,
            phone=phone,
            wechat_openid=wechat_openid,
            wechat_unionid=wechat_unionid,
            wechat_bound_at=wechat_bound_at,
            nickname=nickname,
            avatar_url=resolved_avatar_url,
            intro=intro,
            industry_code=industry_code,
            industry_label=industry_label,
            company_name=company_name,
            show_contact=show_contact,
            is_verified=is_verified,
            inviter_user_pk=int(inviter_user_pk) if inviter_user_pk else None,
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)

            try:
                from app.crud.user_points import ensure_user_points_account
                from app.crud.user_stats import ensure_user_wallet

                ensure_user_wallet(db=db, user_pk=user.id, default_balance=user.balance or 0)
                ensure_user_points_account(db=db, user_pk=user.id, default_balance=0)
            except SQLAlchemyError as exc:
                db.rollback()
                logger.warning(
                    f"Create user succeeded but init account failed. "
                    f"user_pk={user.id}, error={exc}"
                )

            return user
        except IntegrityError as exc:
            db.rollback()
            if provided_business_user_id:
                raise

            error_text = str(exc).lower()
            is_user_id_conflict = "user_id" in error_text and (
                "duplicate" in error_text or "unique" in error_text or "1062" in error_text
            )
            if is_user_id_conflict:
                continue
            raise

    raise RuntimeError("Failed to generate unique user_id")


def update_user_login_meta(db: Session, user: User, client_ip: str | None = None) -> User:
    user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
    user.last_login_ip = client_ip
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(
    db: Session,
    user: User,
    **fields,
) -> User:
    for field_name, field_value in fields.items():
        setattr(user, field_name, field_value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def bind_wechat_identity(
    db: Session,
    user: User,
    wechat_openid: str,
    wechat_unionid: str | None = None,
) -> User:
    user.wechat_openid = wechat_openid
    user.wechat_unionid = wechat_unionid
    user.wechat_bound_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
