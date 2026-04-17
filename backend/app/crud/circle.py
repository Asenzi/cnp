from datetime import UTC, datetime
from decimal import Decimal
from random import randint

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.models.circle import Circle
from app.models.user_circle_membership import UserCircleMembership
from app.models.user import User


def get_circle_by_code(db: Session, circle_code: str) -> Circle | None:
    stmt = select(Circle).where(Circle.circle_code == circle_code)
    return db.execute(stmt).scalar_one_or_none()


def count_circle_members(db: Session, circle_code: str) -> int:
    stmt = select(func.count(UserCircleMembership.id)).where(
        UserCircleMembership.circle_code == circle_code,
        UserCircleMembership.is_active.is_(True),
    )
    count_value = db.execute(stmt).scalar_one_or_none()
    return int(count_value or 0)


def list_joined_circle_codes(db: Session, *, user_pk: int) -> set[str]:
    stmt = select(UserCircleMembership.circle_code).where(
        UserCircleMembership.user_pk == user_pk,
        UserCircleMembership.is_active.is_(True),
    )
    return {
        str(circle_code).strip()
        for circle_code in db.execute(stmt).scalars().all()
        if str(circle_code or "").strip()
    }


def _apply_circle_keyword_filter(stmt, keyword: str | None):
    normalized_keyword = str(keyword or "").strip()
    if not normalized_keyword:
        return stmt

    pattern = f"%{normalized_keyword}%"
    return stmt.where(
        or_(
            Circle.circle_code.like(pattern),
            Circle.name.like(pattern),
            Circle.industry_label.like(pattern),
            Circle.description.like(pattern),
        )
    )


def list_user_joined_circles(
    db: Session,
    *,
    user_pk: int,
    offset: int,
    limit: int,
    keyword: str | None = None,
) -> list[tuple[Circle, UserCircleMembership]]:
    stmt = (
        select(Circle, UserCircleMembership)
        .join(
            UserCircleMembership,
            UserCircleMembership.circle_code == Circle.circle_code,
        )
        .where(
            UserCircleMembership.user_pk == user_pk,
            UserCircleMembership.is_active.is_(True),
        )
        .order_by(
            UserCircleMembership.created_at.desc(),
            Circle.last_active_at.desc(),
            Circle.id.desc(),
        )
    )
    stmt = _apply_circle_keyword_filter(stmt, keyword=keyword)
    stmt = stmt.offset(max(offset, 0)).limit(max(limit, 1))
    return list(db.execute(stmt).all())


def count_user_joined_circles(
    db: Session,
    *,
    user_pk: int,
    keyword: str | None = None,
) -> int:
    stmt = (
        select(func.count(UserCircleMembership.id))
        .select_from(UserCircleMembership)
        .join(
            Circle,
            UserCircleMembership.circle_code == Circle.circle_code,
        )
        .where(
            UserCircleMembership.user_pk == user_pk,
            UserCircleMembership.is_active.is_(True),
        )
    )
    stmt = _apply_circle_keyword_filter(stmt, keyword=keyword)
    value = db.execute(stmt).scalar_one_or_none()
    return int(value or 0)


def list_discover_circles(
    db: Session,
    *,
    keyword: str | None = None,
    city_name: str | None = None,
    industry_label: str | None = None,
    order_by: str = "default",
) -> list[tuple[Circle, User]]:
    owner_user = aliased(User)
    stmt = (
        select(Circle, owner_user)
        .join(owner_user, owner_user.id == Circle.owner_user_pk)
        .where(
            Circle.status == "active",
            owner_user.is_active.is_(True),
        )
    )
    
    # Apply city filter if provided
    if city_name:
        normalized_city = str(city_name or "").strip()
        if normalized_city:
            stmt = stmt.where(owner_user.city_name == normalized_city)

    normalized_industry_label = str(industry_label or "").strip()
    if normalized_industry_label:
        stmt = stmt.where(Circle.industry_label == normalized_industry_label)
    
    # Apply keyword filter
    stmt = _apply_circle_keyword_filter(stmt, keyword=keyword)
    
    # Determine order based on order_by parameter
    if order_by == "latest":
        stmt = stmt.order_by(
            Circle.created_at.desc(),
            Circle.id.desc(),
        )
    elif order_by == "nearby":
        # For nearby, still use default order but city filtering already applied
        stmt = stmt.order_by(
            Circle.last_active_at.desc(),
            Circle.post_count.desc(),
            Circle.member_count.desc(),
            Circle.created_at.desc(),
            Circle.id.desc(),
        )
    else:  # default or recommend
        stmt = stmt.order_by(
            Circle.last_active_at.desc(),
            Circle.post_count.desc(),
            Circle.member_count.desc(),
            Circle.created_at.desc(),
            Circle.id.desc(),
        )
    
    return list(db.execute(stmt).all())


def _generate_circle_code() -> str:
    millis_tail = str(int(datetime.now(UTC).timestamp() * 1000))[-8:]
    rand_tail = f"{randint(0, 9999):04d}"
    return f"C{millis_tail}{rand_tail}"


def _is_circle_code_conflict(error: IntegrityError) -> bool:
    error_text = str(error).lower()
    return (
        "circle_code" in error_text
        and ("duplicate" in error_text or "unique" in error_text or "1062" in error_text)
    )


def create_circle(
    db: Session,
    *,
    owner_user_pk: int,
    name: str,
    industry_label: str,
    description: str,
    cover_url: str,
    avatar_url: str,
    join_type: str,
    join_price: Decimal,
    rules_text: str | None,
    need_post_review: bool,
) -> Circle:
    for _ in range(20):
        circle_code = _generate_circle_code()

        circle = Circle(
            circle_code=circle_code,
            owner_user_pk=owner_user_pk,
            name=name,
            industry_label=industry_label,
            description=description,
            cover_url=cover_url,
            avatar_url=avatar_url,
            join_type=join_type,
            join_price=join_price,
            rules_text=rules_text,
            need_post_review=need_post_review,
            member_count=1,
            post_count=0,
            last_active_at=datetime.now(UTC).replace(tzinfo=None),
        )
        membership = UserCircleMembership(
            user_pk=owner_user_pk,
            circle_code=circle_code,
            is_active=True,
        )

        db.add(circle)
        db.add(membership)

        try:
            db.commit()
            db.refresh(circle)
            return circle
        except IntegrityError as exc:
            db.rollback()
            if _is_circle_code_conflict(exc):
                continue
            raise

    raise RuntimeError("Failed to generate unique circle_code")
