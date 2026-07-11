from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SplitTransaction(Base):
    """分账交易记录表

    记录每笔订单的分账明细，包括分账金额、状态、执行时间等
    """
    __tablename__ = "split_transactions"
    __table_args__ = (
        UniqueConstraint("order_no", "split_to_user_pk", name="uq_split_transactions_order_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_no: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="原始订单号",
    )

    biz_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="业务类型",
    )

    split_from_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="分账来源用户ID（付款方）",
    )

    split_to_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="分账接收方用户ID",
    )

    role_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="分账角色类型",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="订单总金额",
    )

    split_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="分账金额",
    )

    platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="平台抽成金额",
    )

    split_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
        comment="分账状态: pending-待分账, frozen-冻结中, success-已分账, cancelled-已取消",
    )

    channel: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="分账通道: internal-内部账本, wxpay-微信分账",
    )

    receiver_openid: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="微信分账接收方 openid",
    )

    external_transaction_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="微信支付交易流水号",
    )

    external_order_no: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="外部分账单号",
    )

    external_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="外部分账状态",
    )

    external_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="外部分账错误信息",
    )

    freeze_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="冻结截止时间，过期后可执行分账",
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="分账执行时间",
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
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
