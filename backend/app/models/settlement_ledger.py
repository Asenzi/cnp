from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SettlementLedger(Base):
    """结算账户不可变流水"""

    __tablename__ = "settlement_ledgers"
    __table_args__ = (
        UniqueConstraint("user_pk", "biz_type", "biz_key", name="uq_settlement_ledgers_user_biz"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    change_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    available_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0.00"))
    frozen_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0.00"))
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    biz_key: Mapped[str] = mapped_column(String(128), nullable=False, server_default=text("''"))
    title: Mapped[str] = mapped_column(String(128), nullable=False, server_default=text("''"))
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
