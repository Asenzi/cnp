from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Index
from sqlalchemy.sql import func

from app.models.base import Base


class Notification(Base):
    """系统通知表"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="通知ID")
    user_pk = Column(Integer, nullable=False, index=True, comment="用户ID")
    type = Column(String(50), nullable=False, default="system", comment="通知类型: system, circle, event, post")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    link_type = Column(String(50), nullable=True, comment="链接类型: circle, event, post, user, none")
    link_id = Column(String(100), nullable=True, comment="关联ID")
    is_read = Column(Boolean, default=False, nullable=False, index=True, comment="是否已读")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_pk", "is_read"),
        Index("ix_notifications_user_created", "user_pk", "created_at"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_pk={self.user_pk}, title='{self.title}', is_read={self.is_read})>"
