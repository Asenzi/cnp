from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base, SettlementLedger, SplitTransaction, User, UserSettlement, WithdrawalOrder
from app.settlement import create_user_withdrawal, get_user_income_overview, list_user_withdrawals, review_admin_withdrawal


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def demo():
    db = _session()
    user = User(user_id="U0000001", phone="18800000001", nickname="owner", wechat_openid="test_openid", is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    account = UserSettlement(user_pk=user.id, available_balance=Decimal("100.00"))
    db.add(account)
    db.commit()

    first = create_user_withdrawal(db, user_pk=user.id, amount=30)
    try:
        create_user_withdrawal(db, user_pk=user.id, amount=10)
        assert False, "pending withdrawal should reject a second request"
    except Exception as exc:
        assert "已有提现申请" in str(exc)
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

    latest = list_user_withdrawals(db, user_pk=user.id, limit=1)
    assert latest["has_more"] is True
    assert latest["items"][0]["id"] == second["id"]
    older = list_user_withdrawals(db, user_pk=user.id, limit=1, before_id=latest["next_before_id"])
    assert [item["id"] for item in older["items"]] == [first["id"]]
    assert older["has_more"] is False
    failed = list_user_withdrawals(db, user_pk=user.id, status="failed")
    assert [item["id"] for item in failed["items"]] == [first["id"]]

    for index, biz_type in enumerate(("circle_join", "salon", "circle_join"), start=1):
        db.add(SplitTransaction(
            order_no=f"ORDER{index}", biz_type=biz_type,
            split_from_user_pk=user.id, split_to_user_pk=user.id,
            role_type="circle_owner", total_amount=Decimal("10.00"),
            split_amount=Decimal("9.00"), platform_fee=Decimal("1.00"),
            split_status="success",
        ))
    db.commit()
    overview = get_user_income_overview(db, user_pk=user.id, limit=2)
    assert overview["has_more"] is True
    assert overview["source_types"] == ["circle_join", "salon"]
    assert overview["payout"]["wechat_bound"] is True
    assert [item["order_no"] for item in overview["items"]] == ["ORDER3", "ORDER2"]
    older_income = get_user_income_overview(db, user_pk=user.id, limit=2, before_id=overview["next_before_id"])
    assert [item["order_no"] for item in older_income["items"]] == ["ORDER1"]
    salon_income = get_user_income_overview(db, user_pk=user.id, biz_type="salon")
    assert [item["order_no"] for item in salon_income["items"]] == ["ORDER2"]

    user.is_verified = False
    db.commit()
    try:
        create_user_withdrawal(db, user_pk=user.id, amount=1)
        assert False, "unverified user should not withdraw"
    except Exception as exc:
        assert "实名认证" in str(exc)


if __name__ == "__main__":
    demo()
