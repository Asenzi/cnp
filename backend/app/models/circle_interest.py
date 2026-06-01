from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CircleInterest(Base):
    __tablename__ = "circle_interests"
    __table_args__ = (
        UniqueConstraint("user_pk", "circle_pk", name="uq_circle_interest"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    circle_pk: Mapped[int] = mapped_column(
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
