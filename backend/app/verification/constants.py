from enum import Enum


class VerificationType(str, Enum):
    REAL_NAME = "real_name"
    ENTERPRISE = "enterprise"
    BUSINESS_CARD = "business_card"


class VerificationStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


VERIFICATION_TYPE_ORDER = [
    VerificationType.ENTERPRISE.value,
    VerificationType.REAL_NAME.value,
    VerificationType.BUSINESS_CARD.value,
]
