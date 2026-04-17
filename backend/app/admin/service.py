from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.exceptions import BusinessException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.admin_user import AdminUser
from app.models.circle import Circle
from app.models.resource_post import ResourcePost
from app.models.sys_config import SysConfig
from app.models.system_notice import SystemNotice
from app.models.user import User
from app.models.user_verification import UserVerification
from app.models.wallet_recharge_order import WalletRechargeOrder
from app.schemas.admin import AdminLoginResponse, AdminProfile

ADMIN_JWT_SCOPE = "admin"


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip()


def _normalize_lower(value: str | None) -> str:
    return _normalize_text(value).lower()


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    safe_value = value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value
    return safe_value.isoformat()


def _normalize_filter_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


def _serialize_decimal(value: Decimal | int | float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _serialize_admin_profile(admin: AdminUser) -> AdminProfile:
    return AdminProfile(
        id=int(admin.id),
        username=_normalize_text(admin.username),
        display_name=_normalize_text(admin.display_name),
        role=_normalize_text(admin.role) or "super_admin",
        is_active=bool(admin.is_active),
        last_login_at=admin.last_login_at,
    )


def _paginate(page: int, page_size: int, *, max_page_size: int = 100) -> tuple[int, int, int]:
    safe_page = max(int(page or 1), 1)
    safe_page_size = min(max(int(page_size or 20), 1), max_page_size)
    offset = (safe_page - 1) * safe_page_size
    return safe_page, safe_page_size, offset


def ensure_default_admin_user() -> None:
    AdminUser.__table__.create(bind=engine, checkfirst=True)

    username = _normalize_text(settings.ADMIN_DEFAULT_USERNAME)
    password = _normalize_text(settings.ADMIN_DEFAULT_PASSWORD)
    display_name = _normalize_text(settings.ADMIN_DEFAULT_DISPLAY_NAME) or "系统管理员"
    if not username or not password:
        return

    with SessionLocal() as db:
        existing = db.execute(select(AdminUser).where(AdminUser.username == username).limit(1)).scalar_one_or_none()
        if existing is not None:
            return

        row = AdminUser(
            username=username,
            display_name=display_name,
            password_hash=get_password_hash(password),
            role="super_admin",
            token_version=0,
            is_active=True,
            last_login_at=None,
        )
        db.add(row)
        db.commit()


def get_admin_by_id(db: Session, *, admin_id: int) -> AdminUser | None:
    return db.execute(select(AdminUser).where(AdminUser.id == int(admin_id)).limit(1)).scalar_one_or_none()


def get_admin_by_username(db: Session, *, username: str) -> AdminUser | None:
    normalized = _normalize_text(username)
    if not normalized:
        return None
    return db.execute(select(AdminUser).where(AdminUser.username == normalized).limit(1)).scalar_one_or_none()


def login_admin(db: Session, *, username: str, password: str) -> AdminLoginResponse:
    admin = get_admin_by_username(db=db, username=username)
    if admin is None or not verify_password(str(password or ""), str(admin.password_hash or "")):
        raise BusinessException(message="管理员账号或密码错误", code=4601, status_code=401)
    if not bool(admin.is_active):
        raise BusinessException(message="管理员账号已被禁用", code=4602, status_code=403)

    admin.last_login_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token(
        subject=str(admin.id),
        extra_claims={
            "scope": ADMIN_JWT_SCOPE,
            "role": _normalize_text(admin.role) or "super_admin",
            "tv": int(admin.token_version or 0),
        },
    )
    return AdminLoginResponse(
        access_token=token,
        expires_in=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
        admin=_serialize_admin_profile(admin),
    )


def get_admin_profile_data(admin: AdminUser) -> dict[str, Any]:
    payload = _serialize_admin_profile(admin).model_dump(mode="json")
    payload["last_login_at"] = _serialize_datetime(admin.last_login_at)
    return payload


def get_admin_dashboard_overview(db: Session) -> dict[str, Any]:
    user_total = int(db.execute(select(func.count(User.id))).scalar_one() or 0)
    active_user_total = int(db.execute(select(func.count(User.id)).where(User.is_active.is_(True))).scalar_one() or 0)
    verified_user_total = int(db.execute(select(func.count(User.id)).where(User.is_verified.is_(True))).scalar_one() or 0)

    circle_total = int(db.execute(select(func.count(Circle.id))).scalar_one() or 0)
    active_circle_total = int(
        db.execute(select(func.count(Circle.id)).where(Circle.status == "active")).scalar_one() or 0
    )

    resource_total = int(db.execute(select(func.count(ResourcePost.id))).scalar_one() or 0)
    active_resource_total = int(
        db.execute(select(func.count(ResourcePost.id)).where(ResourcePost.status == "active")).scalar_one() or 0
    )

    pending_verification_total = int(
        db.execute(
            select(func.count(UserVerification.id)).where(UserVerification.status == "pending")
        ).scalar_one()
        or 0
    )
    notice_total = int(db.execute(select(func.count(SystemNotice.id))).scalar_one() or 0)

    paid_recharge_total = int(
        db.execute(
            select(func.count(WalletRechargeOrder.id)).where(WalletRechargeOrder.status == "paid")
        ).scalar_one()
        or 0
    )
    pending_recharge_total = int(
        db.execute(
            select(func.count(WalletRechargeOrder.id)).where(WalletRechargeOrder.status == "pending")
        ).scalar_one()
        or 0
    )
    recharge_amount_total = _serialize_decimal(
        db.execute(
            select(func.coalesce(func.sum(WalletRechargeOrder.amount), 0)).where(
                WalletRechargeOrder.status == "paid"
            )
        ).scalar_one()
    )

    recent_users = db.execute(select(User).order_by(User.created_at.desc(), User.id.desc()).limit(5)).scalars().all()

    circle_owner = aliased(User)
    recent_circles = db.execute(
        select(Circle, circle_owner)
        .join(circle_owner, circle_owner.id == Circle.owner_user_pk)
        .order_by(Circle.created_at.desc(), Circle.id.desc())
        .limit(5)
    ).all()

    post_author = aliased(User)
    recent_posts = db.execute(
        select(ResourcePost, post_author)
        .join(post_author, post_author.id == ResourcePost.author_user_pk)
        .order_by(ResourcePost.created_at.desc(), ResourcePost.id.desc())
        .limit(5)
    ).all()

    recharge_user = aliased(User)
    recent_recharges = db.execute(
        select(WalletRechargeOrder, recharge_user)
        .join(recharge_user, recharge_user.id == WalletRechargeOrder.user_pk)
        .order_by(WalletRechargeOrder.created_at.desc(), WalletRechargeOrder.id.desc())
        .limit(5)
    ).all()

    return {
        "summary": {
            "user_total": user_total,
            "active_user_total": active_user_total,
            "verified_user_total": verified_user_total,
            "circle_total": circle_total,
            "active_circle_total": active_circle_total,
            "resource_total": resource_total,
            "active_resource_total": active_resource_total,
            "pending_verification_total": pending_verification_total,
            "paid_recharge_total": paid_recharge_total,
            "pending_recharge_total": pending_recharge_total,
            "recharge_amount_total": recharge_amount_total,
            "notice_total": notice_total,
        },
        "recent_users": [
            {
                "id": int(item.id),
                "user_id": _normalize_text(item.user_id),
                "nickname": _normalize_text(item.nickname),
                "phone": _normalize_text(item.phone),
                "city_name": _normalize_text(item.city_name),
                "industry_label": _normalize_text(item.industry_label),
                "is_verified": bool(item.is_verified),
                "is_active": bool(item.is_active),
                "created_at": _serialize_datetime(item.created_at),
            }
            for item in recent_users
        ],
        "recent_circles": [
            {
                "circle_code": _normalize_text(circle.circle_code),
                "name": _normalize_text(circle.name),
                "industry_label": _normalize_text(circle.industry_label),
                "status": _normalize_text(circle.status),
                "member_count": int(circle.member_count or 0),
                "post_count": int(circle.post_count or 0),
                "owner_user_id": _normalize_text(owner.user_id),
                "owner_nickname": _normalize_text(owner.nickname),
                "created_at": _serialize_datetime(circle.created_at),
            }
            for circle, owner in recent_circles
        ],
        "recent_posts": [
            {
                "post_code": _normalize_text(post.post_code),
                "title": _normalize_text(post.title),
                "mode": _normalize_text(post.mode),
                "status": _normalize_text(post.status),
                "industry_label": _normalize_text(post.industry_label),
                "author_user_id": _normalize_text(author.user_id),
                "author_nickname": _normalize_text(author.nickname),
                "view_count": int(post.view_count or 0),
                "like_count": int(post.like_count or 0),
                "created_at": _serialize_datetime(post.created_at),
            }
            for post, author in recent_posts
        ],
        "recent_recharges": [
            {
                "order_no": _normalize_text(order.order_no),
                "user_id": _normalize_text(user.user_id),
                "nickname": _normalize_text(user.nickname),
                "amount": _serialize_decimal(order.amount),
                "status": _normalize_text(order.status),
                "pay_channel": _normalize_text(order.pay_channel),
                "created_at": _serialize_datetime(order.created_at),
                "paid_at": _serialize_datetime(order.paid_at),
            }
            for order, user in recent_recharges
        ],
    }


def list_admin_users(
    db: Session,
    *,
    created_from: datetime | None,
    created_to: datetime | None,
    is_verified: bool | None,
    keyword: str | None,
    is_active: bool | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page, safe_page_size, offset = _paginate(page, page_size)
    normalized_keyword = _normalize_text(keyword)
    safe_created_from = _normalize_filter_datetime(created_from)
    safe_created_to = _normalize_filter_datetime(created_to)

    if safe_created_from and safe_created_to and safe_created_from > safe_created_to:
        raise BusinessException(message="开始时间不能晚于结束时间", code=4609, status_code=400)

    where_conditions = []
    if is_active is not None:
        where_conditions.append(User.is_active.is_(bool(is_active)))
    if is_verified is not None:
        where_conditions.append(User.is_verified.is_(bool(is_verified)))
    if safe_created_from is not None:
        where_conditions.append(User.created_at >= safe_created_from)
    if safe_created_to is not None:
        where_conditions.append(User.created_at <= safe_created_to)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                User.user_id.like(pattern),
                User.phone.like(pattern),
                User.nickname.like(pattern),
                User.city_name.like(pattern),
                User.industry_label.like(pattern),
                User.company_name.like(pattern),
            )
        )

    items = db.execute(
        select(User)
        .where(*where_conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).scalars().all()
    total = int(db.execute(select(func.count(User.id)).where(*where_conditions)).scalar_one() or 0)

    return {
        "items": [
            {
                "id": int(item.id),
                "user_id": _normalize_text(item.user_id),
                "phone": _normalize_text(item.phone),
                "nickname": _normalize_text(item.nickname),
                "avatar_url": _normalize_text(item.avatar_url),
                "industry_label": _normalize_text(item.industry_label),
                "company_name": _normalize_text(item.company_name),
                "job_title": _normalize_text(item.job_title),
                "city_name": _normalize_text(item.city_name),
                "circle_count": int(item.circle_count or 0),
                "network_count": int(item.network_count or 0),
                "is_verified": bool(item.is_verified),
                "is_active": bool(item.is_active),
                "created_at": _serialize_datetime(item.created_at),
                "last_login_at": _serialize_datetime(item.last_login_at),
            }
            for item in items
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def set_admin_user_active(
    db: Session,
    *,
    user_pk: int,
    is_active: bool,
    actor_admin_id: int | None = None,
) -> dict[str, Any]:
    user = db.execute(select(User).where(User.id == int(user_pk)).limit(1)).scalar_one_or_none()
    if user is None:
        raise BusinessException(message="用户不存在", code=4603, status_code=404)

    user.is_active = bool(is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": int(user.id),
        "user_id": _normalize_text(user.user_id),
        "nickname": _normalize_text(user.nickname),
        "is_active": bool(user.is_active),
    }


def list_admin_circles(
    db: Session,
    *,
    created_from: datetime | None,
    created_to: datetime | None,
    keyword: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page, safe_page_size, offset = _paginate(page, page_size)
    safe_created_from = _normalize_filter_datetime(created_from)
    safe_created_to = _normalize_filter_datetime(created_to)
    normalized_keyword = _normalize_text(keyword)
    normalized_status = _normalize_lower(status)
    owner_user = aliased(User)

    if safe_created_from and safe_created_to and safe_created_from > safe_created_to:
        raise BusinessException(message="开始时间不能晚于结束时间", code=4609, status_code=400)

    where_conditions = []
    if safe_created_from is not None:
        where_conditions.append(Circle.created_at >= safe_created_from)
    if safe_created_to is not None:
        where_conditions.append(Circle.created_at <= safe_created_to)
    if normalized_status:
        where_conditions.append(Circle.status == normalized_status)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                Circle.circle_code.like(pattern),
                Circle.name.like(pattern),
                Circle.industry_label.like(pattern),
                Circle.description.like(pattern),
                owner_user.nickname.like(pattern),
                owner_user.user_id.like(pattern),
            )
        )

    items = db.execute(
        select(Circle, owner_user)
        .join(owner_user, owner_user.id == Circle.owner_user_pk)
        .where(*where_conditions)
        .order_by(Circle.created_at.desc(), Circle.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).all()
    total = int(
        db.execute(
            select(func.count(Circle.id))
            .select_from(Circle)
            .join(owner_user, owner_user.id == Circle.owner_user_pk)
            .where(*where_conditions)
        ).scalar_one()
        or 0
    )

    return {
        "items": [
            {
                "id": int(circle.id),
                "circle_code": _normalize_text(circle.circle_code),
                "name": _normalize_text(circle.name),
                "industry_label": _normalize_text(circle.industry_label),
                "status": _normalize_text(circle.status),
                "join_type": _normalize_text(circle.join_type),
                "join_price": _serialize_decimal(circle.join_price),
                "member_count": int(circle.member_count or 0),
                "post_count": int(circle.post_count or 0),
                "owner_user_id": _normalize_text(owner.user_id),
                "owner_nickname": _normalize_text(owner.nickname),
                "created_at": _serialize_datetime(circle.created_at),
                "last_active_at": _serialize_datetime(circle.last_active_at),
            }
            for circle, owner in items
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def set_admin_circle_status(db: Session, *, circle_code: str, status: str) -> dict[str, Any]:
    normalized_code = _normalize_text(circle_code).upper()
    normalized_status = _normalize_lower(status)
    if normalized_status not in {"active", "inactive"}:
        raise BusinessException(message="圈子状态不合法", code=4604, status_code=400)

    circle = db.execute(select(Circle).where(Circle.circle_code == normalized_code).limit(1)).scalar_one_or_none()
    if circle is None:
        raise BusinessException(message="圈子不存在", code=4605, status_code=404)

    circle.status = normalized_status
    db.add(circle)
    db.commit()
    db.refresh(circle)
    return {
        "circle_code": _normalize_text(circle.circle_code),
        "name": _normalize_text(circle.name),
        "status": _normalize_text(circle.status),
    }


def list_admin_resource_posts(
    db: Session,
    *,
    keyword: str | None,
    status: str | None,
    mode: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page, safe_page_size, offset = _paginate(page, page_size)
    normalized_keyword = _normalize_text(keyword)
    normalized_status = _normalize_lower(status)
    normalized_mode = _normalize_lower(mode)
    author_user = aliased(User)

    where_conditions = []
    if normalized_status:
        where_conditions.append(ResourcePost.status == normalized_status)
    if normalized_mode in {"cooperate", "resource"}:
        where_conditions.append(ResourcePost.mode == normalized_mode)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                ResourcePost.post_code.like(pattern),
                ResourcePost.title.like(pattern),
                ResourcePost.description.like(pattern),
                ResourcePost.industry_label.like(pattern),
                author_user.nickname.like(pattern),
                author_user.user_id.like(pattern),
            )
        )

    items = db.execute(
        select(ResourcePost, author_user)
        .join(author_user, author_user.id == ResourcePost.author_user_pk)
        .where(*where_conditions)
        .order_by(ResourcePost.is_pinned.desc(), ResourcePost.created_at.desc(), ResourcePost.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).all()
    total = int(
        db.execute(
            select(func.count(ResourcePost.id))
            .select_from(ResourcePost)
            .join(author_user, author_user.id == ResourcePost.author_user_pk)
            .where(*where_conditions)
        ).scalar_one()
        or 0
    )

    return {
        "items": [
            {
                "id": int(post.id),
                "post_code": _normalize_text(post.post_code),
                "title": _normalize_text(post.title),
                "mode": _normalize_text(post.mode),
                "status": _normalize_text(post.status),
                "industry_label": _normalize_text(post.industry_label),
                "is_pinned": bool(post.is_pinned),
                "view_count": int(post.view_count or 0),
                "like_count": int(post.like_count or 0),
                "comment_count": int(post.comment_count or 0),
                "author_user_id": _normalize_text(author.user_id),
                "author_nickname": _normalize_text(author.nickname),
                "created_at": _serialize_datetime(post.created_at),
            }
            for post, author in items
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def set_admin_resource_post_status(db: Session, *, post_code: str, status: str) -> dict[str, Any]:
    normalized_code = _normalize_text(post_code).upper()
    normalized_status = _normalize_lower(status)
    if normalized_status not in {"active", "offline"}:
        raise BusinessException(message="资源状态不合法", code=4606, status_code=400)

    post = db.execute(select(ResourcePost).where(ResourcePost.post_code == normalized_code).limit(1)).scalar_one_or_none()
    if post is None:
        raise BusinessException(message="资源不存在", code=4607, status_code=404)

    post.status = normalized_status
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "post_code": _normalize_text(post.post_code),
        "title": _normalize_text(post.title),
        "status": _normalize_text(post.status),
        "is_pinned": bool(post.is_pinned),
    }


def set_admin_resource_post_pin(db: Session, *, post_code: str, pinned: bool) -> dict[str, Any]:
    normalized_code = _normalize_text(post_code).upper()
    post = db.execute(select(ResourcePost).where(ResourcePost.post_code == normalized_code).limit(1)).scalar_one_or_none()
    if post is None:
        raise BusinessException(message="资源不存在", code=4607, status_code=404)

    post.is_pinned = bool(pinned)
    post.pinned_at = datetime.now(UTC).replace(tzinfo=None) if bool(pinned) else None
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "post_code": _normalize_text(post.post_code),
        "title": _normalize_text(post.title),
        "status": _normalize_text(post.status),
        "is_pinned": bool(post.is_pinned),
        "pinned_at": _serialize_datetime(post.pinned_at),
    }


def list_admin_recharge_orders(
    db: Session,
    *,
    keyword: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page, safe_page_size, offset = _paginate(page, page_size)
    normalized_keyword = _normalize_text(keyword)
    normalized_status = _normalize_lower(status)
    recharge_user = aliased(User)

    where_conditions = []
    if normalized_status:
        where_conditions.append(WalletRechargeOrder.status == normalized_status)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                WalletRechargeOrder.order_no.like(pattern),
                WalletRechargeOrder.transaction_id.like(pattern),
                recharge_user.user_id.like(pattern),
                recharge_user.nickname.like(pattern),
                recharge_user.phone.like(pattern),
            )
        )

    items = db.execute(
        select(WalletRechargeOrder, recharge_user)
        .join(recharge_user, recharge_user.id == WalletRechargeOrder.user_pk)
        .where(*where_conditions)
        .order_by(WalletRechargeOrder.created_at.desc(), WalletRechargeOrder.id.desc())
        .offset(offset)
        .limit(safe_page_size)
    ).all()
    total = int(
        db.execute(
            select(func.count(WalletRechargeOrder.id))
            .select_from(WalletRechargeOrder)
            .join(recharge_user, recharge_user.id == WalletRechargeOrder.user_pk)
            .where(*where_conditions)
        ).scalar_one()
        or 0
    )

    return {
        "items": [
            {
                "id": int(order.id),
                "order_no": _normalize_text(order.order_no),
                "amount": _serialize_decimal(order.amount),
                "pay_channel": _normalize_text(order.pay_channel),
                "status": _normalize_text(order.status),
                "transaction_id": _normalize_text(order.transaction_id),
                "remark": _normalize_text(order.remark),
                "user_id": _normalize_text(user.user_id),
                "nickname": _normalize_text(user.nickname),
                "phone": _normalize_text(user.phone),
                "created_at": _serialize_datetime(order.created_at),
                "paid_at": _serialize_datetime(order.paid_at),
            }
            for order, user in items
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def list_admin_sys_configs(
    db: Session,
    *,
    keyword: str | None,
    config_group: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    safe_page, safe_page_size, offset = _paginate(page, page_size)
    normalized_keyword = _normalize_text(keyword)
    normalized_group = _normalize_text(config_group)

    where_conditions = []
    if normalized_group:
        where_conditions.append(SysConfig.config_group == normalized_group)
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        where_conditions.append(
            or_(
                SysConfig.config_key.like(pattern),
                SysConfig.config_value.like(pattern),
                SysConfig.description.like(pattern),
            )
        )

    items = db.execute(
        select(SysConfig)
        .where(*where_conditions)
        .order_by(SysConfig.config_group.asc(), SysConfig.config_key.asc())
        .offset(offset)
        .limit(safe_page_size)
    ).scalars().all()
    total = int(db.execute(select(func.count(SysConfig.id)).where(*where_conditions)).scalar_one() or 0)

    return {
        "items": [
            {
                "id": int(item.id),
                "config_key": _normalize_text(item.config_key),
                "config_value": _normalize_text(item.config_value),
                "config_group": _normalize_text(item.config_group),
                "description": _normalize_text(item.description),
                "created_at": _serialize_datetime(item.created_at),
                "updated_at": _serialize_datetime(item.updated_at),
            }
            for item in items
        ],
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
    }


def upsert_admin_sys_config(
    db: Session,
    *,
    config_key: str,
    config_value: str,
    config_group: str | None,
    description: str | None,
) -> dict[str, Any]:
    normalized_key = _normalize_text(config_key)
    if not normalized_key:
        raise BusinessException(message="配置键不能为空", code=4608, status_code=400)

    row = db.execute(select(SysConfig).where(SysConfig.config_key == normalized_key).limit(1)).scalar_one_or_none()
    if row is None:
        row = SysConfig(
            config_key=normalized_key,
            config_value=_normalize_text(config_value),
            config_group=_normalize_text(config_group) or None,
            description=_normalize_text(description) or None,
        )
    else:
        row.config_value = _normalize_text(config_value)
        row.config_group = _normalize_text(config_group) or None
        row.description = _normalize_text(description) or None

    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": int(row.id),
        "config_key": _normalize_text(row.config_key),
        "config_value": _normalize_text(row.config_value),
        "config_group": _normalize_text(row.config_group),
        "description": _normalize_text(row.description),
        "created_at": _serialize_datetime(row.created_at),
        "updated_at": _serialize_datetime(row.updated_at),
    }
