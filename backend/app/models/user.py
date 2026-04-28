from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    wechat_openid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    wechat_bound_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default=text("'/static/logo.png'"),
    )
    intro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    industry_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    display_wechat: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    city_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    card_files_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    circle_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    network_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    show_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    protect_real_name: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    allow_find_by_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    friend_request_scope: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="all",
        server_default=text("'all'"),
    )
    message_scope: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="friends_or_contacts",
        server_default=text("'friends_or_contacts'"),
    )
    allow_auto_add_friend: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
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
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    inviter_user_pk: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
