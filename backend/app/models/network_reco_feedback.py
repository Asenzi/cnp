from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NetworkRecoFeedback(Base):
    __tablename__ = "network_reco_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    viewer_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    scene: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="discover",
    )
    tab_key: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="recommend",
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ext_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
