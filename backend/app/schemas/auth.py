from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$", description="11-digit Mainland China phone number")


class SendCodeData(BaseModel):
    phone: str
    expires_in: int
    debug_code: str | None = None


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$", description="11-digit Mainland China phone number")
    code: str = Field(..., min_length=4, max_length=8, description="SMS verification code")
    invite_code: str | None = Field(default=None, min_length=1, max_length=32)


class PasswordLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$", description="11-digit Mainland China phone number")
    password: str = Field(..., min_length=6, max_length=32, description="Password")
    invite_code: str | None = Field(default=None, min_length=1, max_length=32)


class WechatMiniLoginRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=128, description="WeChat miniapp login code")
    nickname: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=255)
    device_id: str | None = Field(default=None, max_length=128)
    invite_code: str | None = Field(default=None, min_length=1, max_length=32)


class WechatBindRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=128, description="WeChat miniapp bind code")
    nickname: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=255)
    device_id: str | None = Field(default=None, max_length=128)


class WechatBindData(BaseModel):
    wechat_bound: bool = True
    is_bound_to_current_user: bool = True
    wechat_bound_at: str | None = None


class PhoneBindCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$", description="Phone number to bind")


class PhoneBindRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1\d{10}$", description="Phone number to bind")
    code: str = Field(..., min_length=4, max_length=8, description="SMS verification code")


class PhoneBindData(BaseModel):
    phone: str
    masked_phone: str
    is_bound_to_current_user: bool = True
    updated: bool = True


class PasswordChangeCodeRequest(BaseModel):
    pass


class PasswordChangeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=8, description="SMS verification code")
    new_password: str = Field(..., min_length=6, max_length=32, description="New password")


class PasswordChangeData(BaseModel):
    updated: bool = True
    force_relogin: bool = True


class UserBrief(BaseModel):
    userId: str
    user_id: str
    phone: str
    nickname: str
    avatar_url: str
    wechat_bound: bool = False
    is_verified: bool = False
    intro: str | None = None
    industry_code: str | None = None
    industry_label: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    card_files: list[dict] | None = None
    show_contact: bool = True
    circle_count: int = 0
    network_count: int = 0
    points: int = 0
    balance: float = 0.0
    invite_code: str | None = None


class LoginData(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    is_new_user: bool = False
    user_info: UserBrief
