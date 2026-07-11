from pydantic import BaseModel, Field


class ContentReportRequest(BaseModel):
    target_type: str = Field(..., max_length=32)
    target_id: str = Field(..., max_length=64)
    reason: str | None = Field(default=None, max_length=255)
