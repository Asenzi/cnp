from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SplitRule(Base):
    """分账规则配置表

    用于定义不同业务类型的分账规则，支持按比例或固定金额分账
    """
    __tablename__ = "split_rules"
    __table_args__ = (
        UniqueConstraint("biz_type", "role_type", name="uq_split_rules_biz_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    biz_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="业务类型: circle_join-圈子入圈, member_subscribe-会员订阅等",
    )

    role_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="分账角色: platform-平台, circle_owner-圈主, content_creator-内容创作者等",
    )

    split_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="percentage",
        server_default=text("'percentage'"),
        comment="分账类型: percentage-按比例, fixed-固定金额",
    )

    split_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default=text("0.0000"),
        comment="分账值：percentage类型为比例(0-1)，fixed类型为金额",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default=text("100"),
        comment="分账优先级，数字越小优先级越高",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
        comment="是否启用",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="规则描述",
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
