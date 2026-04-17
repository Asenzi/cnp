from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AdminProfile(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    admin: AdminProfile


class AdminUserStatusPayload(BaseModel):
    is_active: bool


class AdminCircleStatusPayload(BaseModel):
    status: Literal["active", "inactive"] = "active"


class AdminResourcePostStatusPayload(BaseModel):
    status: Literal["active", "offline"] = "active"


class AdminResourcePostPinPayload(BaseModel):
    pinned: bool


class AdminConfigUpsertPayload(BaseModel):
    config_value: str = Field(default="", max_length=255)
    config_group: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=1000)
