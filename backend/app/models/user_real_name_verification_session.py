from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRealNameVerificationSession(Base):
    __tablename__ = "user_real_name_verification_sessions"
    __table_args__ = (
        Index("ix_user_real_name_verify_sessions_user_status", "user_pk", "status"),
        Index("ix_user_real_name_verify_sessions_id_hash", "id_number_hash"),
        Index("ix_user_real_name_verify_sessions_provider_biz_token", "provider_biz_token", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="tencent_cloud")
    provider_biz_token: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    real_name: Mapped[str] = mapped_column(String(32), nullable=False)
    id_number_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    id_number_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    redirect_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
