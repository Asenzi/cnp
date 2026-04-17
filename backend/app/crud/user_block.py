from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_block import UserBlock


def count_user_blocks(db: Session, user_pk: int) -> int:
    stmt = select(func.count(UserBlock.id)).where(UserBlock.user_pk == user_pk)
    return int(db.execute(stmt).scalar_one() or 0)


def list_blocked_users(
    db: Session,
    user_pk: int,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[User, UserBlock]], int]:
    base_stmt = (
        select(User, UserBlock)
        .join(UserBlock, User.id == UserBlock.blocked_user_pk)
        .where(UserBlock.user_pk == user_pk)
    )
    list_stmt = (
        base_stmt.order_by(UserBlock.created_at.desc(), UserBlock.id.desc())
        .offset(max(offset, 0))
        .limit(max(limit, 1))
    )
    count_stmt = select(func.count(UserBlock.id)).where(UserBlock.user_pk == user_pk)

    rows = list(db.execute(list_stmt).all())
    total = int(db.execute(count_stmt).scalar_one() or 0)
    return rows, total


def add_user_block(db: Session, user_pk: int, blocked_user_pk: int) -> tuple[UserBlock, bool]:
    stmt = select(UserBlock).where(
        UserBlock.user_pk == user_pk,
        UserBlock.blocked_user_pk == blocked_user_pk,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing, False

    record = UserBlock(
        user_pk=user_pk,
        blocked_user_pk=blocked_user_pk,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
        return record, True
    except IntegrityError:
        db.rollback()
        existing = db.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return existing, False
        raise


def remove_user_block(db: Session, user_pk: int, blocked_user_pk: int) -> bool:
    stmt = delete(UserBlock).where(
        UserBlock.user_pk == user_pk,
        UserBlock.blocked_user_pk == blocked_user_pk,
    )
    result = db.execute(stmt)
    db.commit()
    return int(result.rowcount or 0) > 0

