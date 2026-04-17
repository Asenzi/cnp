from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AdminContentReviewListItem(BaseModel):
    id: int
    review_type: str
    action_type: str
    status: str
    submitter_user_pk: int
    submitter_user_id: str
    submitter_nickname: str
    target_user_pk: int | None = None
    target_circle_code: str | None = None
    target_post_code: str | None = None
    target_label: str | None = None
    review_fee_amount: float = 0.0
    fee_paid: bool = False
    trigger_reason: str | None = None
    risk_tags: list[str] = Field(default_factory=list)
    reject_reason: str | None = None
    submit_payload: dict[str, Any] | None = None
    current_payload: dict[str, Any] | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None


class AdminContentReviewListData(BaseModel):
    items: list[AdminContentReviewListItem]
    total: int
    page: int
    page_size: int


class AdminContentReviewActionRequest(BaseModel):
    action: Literal["approve", "reject"]
    reject_reason: str | None = Field(default=None, max_length=255)
