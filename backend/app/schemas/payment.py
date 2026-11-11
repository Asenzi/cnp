from pydantic import BaseModel, Field


class MemberSubscribeRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=32)
    pay_channel: str | None = Field(default=None, max_length=16)
    use_points_discount: bool | None = None
    client_platform: str | None = Field(default=None, max_length=16)
    referral_invite_code: str | None = Field(default=None, max_length=16)


class MemberOrderConfirmRequest(BaseModel):
    transaction_id: str | None = Field(default=None, max_length=64)
    ext: dict | None = None


class MemberPaymentClientErrorRequest(BaseModel):
    order_no: str = Field(..., min_length=1, max_length=64)
    scene: str | None = Field(default=None, max_length=64)
    err_msg: str | None = Field(default=None, max_length=512)
    err_code: str | int | None = None
    ext: dict | None = None


class CircleOwnerPurchaseRequest(BaseModel):
    pay_channel: str | None = Field(default=None, max_length=16)
    client_platform: str | None = Field(default=None, max_length=16)


class PartnerPurchaseRequest(BaseModel):
    pay_channel: str | None = Field(default=None, max_length=16)
    client_platform: str | None = Field(default=None, max_length=16)
