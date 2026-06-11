from datetime import datetime

from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CircleJoinRequest(Base):
    """圈子加入申请"""
    __tablename__ = "circle_join_requests"
    __table_args__ = (
        UniqueConstraint("user_pk", "circle_code", name="uq_circle_join_requests_user_circle"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    circle_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        comment="pending: 待审核, approved: 已通过, rejected: 已拒绝"
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="申请留言")
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="拒绝原因")
    order_no: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    pay_channel: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payment_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="unpaid",
        server_default=text("'unpaid'"),
        index=True,
    )
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    refund_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="none",
        server_default=text("'none'"),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_approve_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="审核时间")
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
