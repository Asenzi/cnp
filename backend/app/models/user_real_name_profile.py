from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRealNameProfile(Base):
    __tablename__ = "user_real_name_profiles"
    __table_args__ = (
        UniqueConstraint("id_number_hash", name="uq_user_real_name_profiles_id_number_hash"),
        Index("ix_user_real_name_profiles_verified_at", "verified_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    real_name: Mapped[str] = mapped_column(String(32), nullable=False)
    id_number_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    id_number_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    id_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    id_front_url: Mapped[str] = mapped_column(String(255), nullable=False)
    id_back_url: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider_biz_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
