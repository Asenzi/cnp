from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_no: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feedback_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    images_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="pages/me/help-feedback/index",
        server_default=text("'pages/me/help-feedback/index'"),
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
