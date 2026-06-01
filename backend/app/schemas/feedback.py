from typing import Literal

from pydantic import BaseModel, Field

FeedbackType = Literal["account", "payment", "circles", "verification", "other"]


class FeedbackImageItem(BaseModel):
    path: str = Field(..., min_length=1, max_length=255)
    name: str | None = Field(default=None, max_length=128)
    size: int | None = Field(default=None, ge=0)


class HelpFeedbackSubmitRequest(BaseModel):
    feedback_type: FeedbackType
    description: str = Field(..., min_length=5, max_length=500)
    contact: str | None = Field(default=None, max_length=100)
    images: list[FeedbackImageItem] = Field(default_factory=list, max_length=3)
    source_page: str = Field(default="pages/me/help-feedback/index", max_length=64)


class HelpFeedbackSubmitData(BaseModel):
    id: int
    ticket_no: str
    status: str = "pending"
    created_at: str | None = None
