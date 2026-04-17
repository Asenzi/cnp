from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_points_account import UserPointsAccount


def _normalize_int(value: int | float | str | None) -> int:
    try:
        parsed = int(str(value))
    except Exception:  # noqa: BLE001
        return 0
    return max(parsed, 0)


def get_user_points_account(db: Session, *, user_pk: int) -> UserPointsAccount | None:
    stmt = select(UserPointsAccount).where(UserPointsAccount.user_pk == int(user_pk))
    return db.execute(stmt).scalar_one_or_none()


def ensure_user_points_account(
    db: Session,
    *,
    user_pk: int,
    default_balance: int | float | str = 0,
    default_frozen_balance: int | float | str = 0,
) -> UserPointsAccount:
    stmt = select(UserPointsAccount).where(UserPointsAccount.user_pk == int(user_pk))
    account = db.execute(stmt).scalar_one_or_none()
    if account is not None:
        return account

    account = UserPointsAccount(
        user_pk=int(user_pk),
        balance=_normalize_int(default_balance),
        frozen_balance=_normalize_int(default_frozen_balance),
    )
    db.add(account)

    try:
        db.commit()
        db.refresh(account)
        return account
    except IntegrityError:
        db.rollback()
        account = db.execute(stmt).scalar_one_or_none()
        if account is not None:
            return account
        raise
