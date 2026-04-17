from pydantic import BaseModel, Field


class FriendRequestCreateRequest(BaseModel):
    target_user_id: str = Field(min_length=1, max_length=32)
    message: str | None = Field(default=None, max_length=255)


class MessageSendRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    content_type: str = Field(default="text", max_length=16)
