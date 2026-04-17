from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.verification.constants import VerificationStatus, VerificationType


class VerificationItem(BaseModel):
    type: VerificationType
    status: VerificationStatus
    reject_reason: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None


class VerificationOverviewData(BaseModel):
    is_verified: bool = False
    items: list[VerificationItem]


class RealNameVerificationSubmitRequest(BaseModel):
    real_name: str = Field(..., min_length=2, max_length=32)
    id_number: str = Field(..., min_length=15, max_length=18)
    id_front_url: str = Field(..., max_length=255)
    id_back_url: str = Field(..., max_length=255)


class RealNameVerificationDetailData(BaseModel):
    status: VerificationStatus = VerificationStatus.NOT_SUBMITTED
    reject_reason: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    verified_at: datetime | None = None
    verification_provider: str | None = None
    verified_source: str | None = None
    real_name: str | None = None
    id_number: str | None = None
    id_number_masked: str | None = None
    id_front_url: str | None = None
    id_back_url: str | None = None


class TencentRealNameStartRequest(BaseModel):
    real_name: str = Field(..., min_length=2, max_length=32)
    id_number: str = Field(..., min_length=15, max_length=18)


class TencentRealNameStartData(BaseModel):
    session_id: int
    provider: str
    provider_biz_token: str
    redirect_url: str | None = None
    status: str
    real_name: str
    id_number_masked: str


class TencentRealNameFinishRequest(BaseModel):
    provider_biz_token: str = Field(..., min_length=8, max_length=128)


class TencentRealNameFinishData(BaseModel):
    session_id: int
    provider: str
    provider_biz_token: str
    provider_request_id: str | None = None
    status: str
    is_verified: bool
    real_name: str
    id_number_masked: str
    verified_at: datetime | None = None


class EnterpriseVerificationSubmitRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=128)
    job_title: str | None = Field(default=None, max_length=64)
    license_file_url: str = Field(..., max_length=255)
    credit_code: str | None = Field(default=None, max_length=18)


class BusinessCardVerificationSubmitRequest(BaseModel):
    card_holder_name: str = Field(..., min_length=2, max_length=32)
    company_name: str | None = Field(default=None, max_length=128)
    card_title: str | None = Field(default=None, max_length=64)
    card_file_url: str = Field(..., max_length=255)


class AdminVerificationListItem(BaseModel):
    id: int
    user_pk: int
    user_id: str
    phone: str
    nickname: str
    type: VerificationType
    status: VerificationStatus
    reject_reason: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    submit_payload: dict[str, Any] | None = None
    real_name_profile: RealNameVerificationDetailData | None = None


class AdminVerificationListData(BaseModel):
    items: list[AdminVerificationListItem]
    total: int
    page: int
    page_size: int


class AdminVerificationReviewRequest(BaseModel):
    action: Literal['approve', 'reject']
    reject_reason: str | None = Field(default=None, max_length=255)
