from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    member_referral_snapshot: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="首次会员成交归属；NULL未锁定，{}平台来源"
    )

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
    wechat_session_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wechat_bound_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_candidate_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_review_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    avatar_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    nickname_candidate: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname_review_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="approved",
        server_default=text("'approved'"),
    )
    nickname_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    intro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intro_candidate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intro_review_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="approved",
        server_default=text("'approved'"),
    )
    intro_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    risk_level: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="L0",
        server_default=text("'L0'"),
    )
    profile_edit_blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    muted_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    industry_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    industry_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    display_wechat: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    city_name: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    district_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
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
    is_circle_owner: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        index=True,
    )
    partner_type: Mapped[str | None] = mapped_column(
        String(24), nullable=True, index=True,
        comment="合作身份: salon_owner / city_partner",
    )
    partner_invite_code: Mapped[str | None] = mapped_column(
        String(4), nullable=True, unique=True, index=True,
        comment="合作身份专属四位邀请码",
    )
    partner_city_key: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True,
        comment="城市合伙人唯一城市键，仅城市合伙人使用",
    )
    city_partner_user_pk: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="沙龙主理人所属城市合伙人",
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
