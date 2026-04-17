from pydantic import BaseModel, Field


class MemberSubscribeRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=32)
    pay_channel: str | None = Field(default=None, max_length=16)
    use_points_discount: bool | None = None


class MemberOrderConfirmRequest(BaseModel):
    transaction_id: str | None = Field(default=None, max_length=64)
    ext: dict | None = None


class WalletRechargeRequest(BaseModel):
    amount: float = Field(..., gt=0, le=200000)
    pay_channel: str | None = Field(default=None, max_length=16)


class WalletRechargeConfirmRequest(BaseModel):
    transaction_id: str | None = Field(default=None, max_length=64)
    ext: dict | None = None
