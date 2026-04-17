from pydantic import BaseModel, Field


class CardFileItem(BaseModel):
    name: str = Field(..., max_length=128)
    url: str = Field(..., max_length=255)
    size: int | None = Field(default=None, ge=0)


class UpdateCurrentUserProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=255)
    intro: str | None = Field(default=None, max_length=255)
    industry_code: str | None = Field(default=None, max_length=32)
    industry_label: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=128)
    job_title: str | None = Field(default=None, max_length=64)
    display_phone: str | None = Field(default=None, max_length=20)
    display_wechat: str | None = Field(default=None, max_length=64)
    city_code: str | None = Field(default=None, max_length=16)
    city_name: str | None = Field(default=None, max_length=32)
    card_files: list[CardFileItem] | None = None
    show_contact: bool | None = None


class PrivacySettingsData(BaseModel):
    phone_visible_to_friends: bool = Field(default=False)
    protect_real_name: bool = Field(default=True)
    allow_find_by_email: bool = Field(default=False)
    friend_request_scope: str = Field(default="all")
    message_scope: str = Field(default="friends_or_contacts")
    allow_auto_add_friend: bool = Field(default=False)
    blocked_count: int = Field(default=0, ge=0)


class UpdatePrivacySettingsRequest(BaseModel):
    phone_visible_to_friends: bool | None = None
    protect_real_name: bool | None = None
    allow_find_by_email: bool | None = None
    friend_request_scope: str | None = Field(default=None, max_length=32)
    message_scope: str | None = Field(default=None, max_length=32)
    allow_auto_add_friend: bool | None = None


class BlockUserRequest(BaseModel):
    target_user_id: str = Field(..., min_length=8, max_length=8)


class BlockedUserItem(BaseModel):
    userId: str
    user_id: str
    nickname: str
    avatar_url: str
    is_verified: bool = False
    blocked_at: str | None = None


class BlockedUserListData(BaseModel):
    items: list[BlockedUserItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 20
