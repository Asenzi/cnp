from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResourcePostCircleSync(Base):
    __tablename__ = "resource_post_circle_syncs"
    __table_args__ = (
        UniqueConstraint("post_pk", "circle_code", name="uq_resource_post_circle_sync_post_circle"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_pk: Mapped[int] = mapped_column(
        ForeignKey("resource_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    circle_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    request_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )
    reviewed_by_user_pk: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
