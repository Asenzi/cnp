from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserInterest(Base):
    """用户感兴趣关系表 - 记录用户对其他用户的感兴趣状态"""
    __tablename__ = "user_interests"
    __table_args__ = (
        UniqueConstraint("user_pk", "target_user_pk", name="uq_user_interest"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="感兴趣的用户ID"
    )
    target_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="被感兴趣的目标用户ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
