from pydantic import BaseModel, Field


class WithdrawalCreateRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1000000)
    withdraw_type: str = Field(default="wechat", max_length=32)
    withdraw_account: str | None = Field(default=None, max_length=128)
