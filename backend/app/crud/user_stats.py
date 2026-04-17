from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_circle_membership import UserCircleMembership
from app.models.user_connection import UserConnection
from app.models.user_points_account import UserPointsAccount
from app.models.user_wallet import UserWallet


def _normalize_decimal(value: Decimal | int | float | str | None) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0.00")
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return Decimal("0.00")


def ensure_user_wallet(
    db: Session,
    user_pk: int,
    default_balance: Decimal | int | float | str = Decimal("0.00"),
) -> UserWallet:
    stmt = select(UserWallet).where(UserWallet.user_pk == user_pk)
    wallet = db.execute(stmt).scalar_one_or_none()
    if wallet is not None:
        return wallet

    wallet = UserWallet(
        user_pk=user_pk,
        balance=_normalize_decimal(default_balance),
    )
    db.add(wallet)

    try:
        db.commit()
        db.refresh(wallet)
        return wallet
    except IntegrityError:
        # Concurrent insert fallback.
        db.rollback()
        wallet = db.execute(stmt).scalar_one_or_none()
        if wallet is not None:
            return wallet
        raise


def get_user_realtime_stats(
    db: Session,
    user_pk: int,
    fallback_circle_count: int = 0,
    fallback_network_count: int = 0,
    fallback_balance: Decimal | int | float | str = Decimal("0.00"),
    fallback_points: int = 0,
) -> dict[str, Decimal | int]:
    circle_stmt = select(func.count(UserCircleMembership.id)).where(
        UserCircleMembership.user_pk == user_pk,
        UserCircleMembership.is_active.is_(True),
    )
    network_stmt = select(func.count(UserConnection.id)).where(
        UserConnection.user_pk == user_pk,
        UserConnection.is_active.is_(True),
    )
    wallet_stmt = select(UserWallet.balance).where(UserWallet.user_pk == user_pk)
    points_stmt = select(UserPointsAccount.balance, UserPointsAccount.frozen_balance).where(UserPointsAccount.user_pk == user_pk)

    circle_count = db.execute(circle_stmt).scalar_one_or_none()
    network_count = db.execute(network_stmt).scalar_one_or_none()
    wallet_balance = db.execute(wallet_stmt).scalar_one_or_none()
    points_row = db.execute(points_stmt).first()
    points_balance = int(points_row[0]) if points_row is not None and points_row[0] is not None else int(fallback_points or 0)
    frozen_balance = int(points_row[1]) if points_row is not None and points_row[1] is not None else 0

    return {
        "circle_count": int(circle_count if circle_count is not None else fallback_circle_count),
        "network_count": int(network_count if network_count is not None else fallback_network_count),
        "balance": _normalize_decimal(wallet_balance if wallet_balance is not None else fallback_balance),
        "points": max(points_balance, 0),
        "frozen_points": max(frozen_balance, 0),
        "available_points": max(points_balance - frozen_balance, 0),
    }
