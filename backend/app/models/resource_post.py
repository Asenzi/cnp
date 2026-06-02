from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResourcePost(Base):
    __tablename__ = "resource_posts"
    __table_args__ = (
        Index(
            "ix_resource_posts_status_industry_mode_created",
            "status",
            "industry_label",
            "mode",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    author_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="cooperate",
        server_default=text("'cooperate'"),
    )
    industry_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    images_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    like_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    comment_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="active",
        server_default=text("'active'"),
        index=True,
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        index=True,
    )
    pinned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    # 活动相关字段
    event_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    price: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    participant_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
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


class ResourcePostLike(Base):
    __tablename__ = "resource_post_likes"
    __table_args__ = (
        UniqueConstraint("post_pk", "user_pk", name="uq_resource_post_likes_post_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_pk: Mapped[int] = mapped_column(
        ForeignKey("resource_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


class ResourcePostImpression(Base):
    __tablename__ = "resource_post_impressions"
    __table_args__ = (
        UniqueConstraint(
            "viewer_user_pk",
            "post_pk",
            "scene",
            "tab_key",
            "request_id",
            name="uq_resource_post_impressions_request_post",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    viewer_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_pk: Mapped[int] = mapped_column(
        ForeignKey("resource_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scene: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="resources",
    )
    tab_key: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="cooperate",
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )


class ResourcePostRecoFeedback(Base):
    __tablename__ = "resource_post_reco_feedback"
    __table_args__ = (
        UniqueConstraint(
            "viewer_user_pk",
            "post_pk",
            "scene",
            "tab_key",
            "request_id",
            "event_type",
            name="uq_resource_post_reco_feedback_request_event",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    viewer_user_pk: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_pk: Mapped[int] = mapped_column(
        ForeignKey("resource_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    scene: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="resources",
    )
    tab_key: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="cooperate",
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ext_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
