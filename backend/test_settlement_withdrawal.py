from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base, SettlementLedger, User, UserSettlement, WithdrawalOrder
from app.settlement import create_user_withdrawal, review_admin_withdrawal


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def demo():
    db = _session()
    user = User(user_id="U0000001", phone="18800000001", nickname="owner")
    db.add(user)
    db.commit()
    db.refresh(user)

    account = UserSettlement(user_pk=user.id, available_balance=Decimal("100.00"))
    db.add(account)
    db.commit()

    first = create_user_withdrawal(db, user_pk=user.id, amount=30)
    account = db.scalar(select(UserSettlement).where(UserSettlement.user_pk == user.id))
    assert account.available_balance == Decimal("70.00")
    assert account.frozen_balance == Decimal("30.00")

    review_admin_withdrawal(db, withdrawal_id=first["id"], action="reject", remark="bad account")
    account = db.scalar(select(UserSettlement).where(UserSettlement.user_pk == user.id))
    assert account.available_balance == Decimal("100.00")
    assert account.frozen_balance == Decimal("0.00")

    second = create_user_withdrawal(db, user_pk=user.id, amount=40)
    review_admin_withdrawal(db, withdrawal_id=second["id"], action="approve", transaction_id="TX123")
    account = db.scalar(select(UserSettlement).where(UserSettlement.user_pk == user.id))
    assert account.available_balance == Decimal("60.00")
    assert account.frozen_balance == Decimal("0.00")
    assert account.total_withdrawn == Decimal("40.00")

    orders = db.scalars(select(WithdrawalOrder).order_by(WithdrawalOrder.id)).all()
    assert [item.status for item in orders] == ["failed", "success"]
    assert len(db.scalars(select(SettlementLedger)).all()) == 4


if __name__ == "__main__":
    demo()
