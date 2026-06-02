from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    """通知基础模型"""

    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., min_length=1, description="通知内容")
    type: str = Field(default="system", description="通知类型")
    link_type: Optional[str] = Field(None, description="链接类型")
    link_id: Optional[str] = Field(None, description="关联ID")


class NotificationCreate(NotificationBase):
    """创建通知请求"""

    user_pk: int = Field(..., description="用户ID")


class NotificationResponse(NotificationBase):
    """通知响应"""

    id: int = Field(..., description="通知ID")
    user_pk: int = Field(..., description="用户ID")
    is_read: bool = Field(..., description="是否已读")
    read_at: Optional[datetime] = Field(None, description="阅读时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """通知列表响应"""

    items: list[NotificationResponse] = Field(default_factory=list, description="通知列表")
    total: int = Field(..., description="总数")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="每页数量")


class UnreadCountResponse(BaseModel):
    """未读通知数量响应"""

    count: int = Field(..., description="未读数量")
