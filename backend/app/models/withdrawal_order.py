from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WithdrawalOrder(Base):
    """提现订单表

    记录用户的提现申请和处理状态
    """
    __tablename__ = "withdrawal_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_no: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="提现订单号",
    )

    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="提现金额",
    )

    fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="手续费",
    )

    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="实际到账金额",
    )

    withdraw_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="wechat",
        server_default=text("'wechat'"),
        comment="提现方式: wechat-微信, alipay-支付宝, bank-银行卡",
    )

    withdraw_account: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="提现账户",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
        comment="状态: pending-待处理, processing-处理中, success-成功, failed-失败",
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="第三方交易流水号",
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="处理时间",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
