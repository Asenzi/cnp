from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CircleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    industry_label: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=2, max_length=500)
    cover_url: str = Field(..., min_length=1, max_length=255)
    avatar_url: str = Field(..., min_length=1, max_length=255)
    join_type: Literal["free", "paid", "review"] = "free"
    join_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    rules_text: str | None = Field(default=None, max_length=2000)
    need_post_review: bool = False


class CircleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=64)
    industry_label: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, min_length=2, max_length=500)
    cover_url: str | None = Field(default=None, min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, min_length=1, max_length=255)
    join_type: Literal["free", "paid", "review"] | None = None
    join_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    rules_text: str | None = Field(default=None, max_length=2000)
    need_post_review: bool | None = None


class CircleOwnerData(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str
    is_verified: bool


class CircleData(BaseModel):
    circle_code: str
    name: str
    industry_label: str
    description: str
    cover_url: str
    avatar_url: str
    join_type: str
    join_price: float
    rules_text: str | None = None
    need_post_review: bool
    member_count: int
    post_count: int
    owner: CircleOwnerData
    created_at: datetime | None = None


class MyCircleItem(BaseModel):
    circle_code: str
    name: str
    industry_label: str
    description: str
    cover_url: str
    avatar_url: str
    join_type: str
    member_count: int
    post_count: int
    is_owner: bool
    joined_at: datetime | None = None
    last_active_at: datetime | None = None


class MyCircleListData(BaseModel):
    items: list[MyCircleItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 20
    has_more: bool = False


class CircleDiscoverItem(BaseModel):
    circle_code: str
    name: str
    industry_label: str
    description: str
    cover_url: str
    avatar_url: str
    join_type: str
    join_price: float
    member_count: int
    post_count: int
    owner_user_id: str
    owner_nickname: str
    owner_avatar_url: str
    owner_city_name: str | None = None
    owner_is_verified: bool = False
    is_joined: bool = False
    reason_tags: list[str] = Field(default_factory=list)
    score: float = 0
    last_active_at: datetime | None = None
    created_at: datetime | None = None


class CircleDiscoverListData(BaseModel):
    items: list[CircleDiscoverItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 20
    has_more: bool = False
    tab: str = "recommend"
    city_name: str | None = None
    request_id: str | None = None


class CirclePostSyncReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    reject_reason: str | None = Field(default=None, max_length=120)
