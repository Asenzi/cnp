from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NetworkRecoImpression(Base):
    __tablename__ = "network_reco_impressions"

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
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
