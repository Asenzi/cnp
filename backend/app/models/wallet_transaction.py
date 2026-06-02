from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WalletTransaction(Base):
    """钱包交易流水记录表"""
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        UniqueConstraint("user_pk", "biz_type", "biz_key", name="uq_wallet_transactions_user_biz"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="变动金额，正数为收入，负数为支出",
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="交易后余额",
    )
    biz_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="业务类型: recharge-充值, member_subscribe-会员订阅, refund-退款等",
    )
    biz_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="",
        server_default=text("''"),
        comment="业务唯一标识，如订单号",
    )
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="",
        server_default=text("''"),
        comment="交易标题",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注信息")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
