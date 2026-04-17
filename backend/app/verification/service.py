import json
import re
from base64 import urlsafe_b64encode
from hashlib import sha256
from typing import Literal

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.crud import (
    get_user_by_id,
    get_user_real_name_profile,
    get_user_real_name_profile_by_hash,
    get_user_verification,
    get_user_verification_by_id,
    list_user_verifications,
    list_verifications_for_admin,
    set_user_real_name_profile_verified_at,
    set_user_verification_status,
    sync_user_verified_flag,
    upsert_user_real_name_profile,
    upsert_user_verification_submit,
)
from app.models.user import User
from app.models.user_real_name_profile import UserRealNameProfile
from app.points import grant_real_name_verification_points
from app.schemas.verification import (
    AdminVerificationListData,
    AdminVerificationListItem,
    RealNameVerificationDetailData,
    VerificationItem,
    VerificationOverviewData,
)
from app.verification.constants import (
    VERIFICATION_TYPE_ORDER,
    VerificationStatus,
    VerificationType,
)

ID_NUMBER_PATTERN = re.compile(r"^\d{17}[\dXx]$|^\d{15}$")
CREDIT_CODE_PATTERN = re.compile(r"^[0-9A-Z]{18}$")


def _normalize_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:max_len]


def _get_verification_secret() -> str:
    return str(settings.VERIFICATION_DATA_SECRET or settings.JWT_SECRET_KEY or "verification-secret").strip()


def _build_fernet() -> Fernet:
    digest = sha256(_get_verification_secret().encode("utf-8")).digest()
    return Fernet(urlsafe_b64encode(digest))


def _encrypt_sensitive_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return _build_fernet().encrypt(text.encode("utf-8")).decode("utf-8")


def _decrypt_sensitive_text(value: str | None) -> str | None:
    encrypted = str(value or "").strip()
    if not encrypted:
        return None
    try:
        return _build_fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        logger.warning("Failed to decrypt stored real-name value.")
        return None


def _mask_id_number(id_number: str | None) -> str | None:
    normalized = _normalize_text(id_number, 18)
    if not normalized:
        return None
    if len(normalized) <= 7:
        return f"{normalized[:1]}{'*' * max(len(normalized) - 2, 1)}{normalized[-1:]}"
    return f"{normalized[:3]}{'*' * max(len(normalized) - 7, 1)}{normalized[-4:]}"


def _hash_id_number(id_number: str | None) -> str | None:
    normalized = _normalize_text(id_number, 18)
    if not normalized:
        return None
    payload = f"{_get_verification_secret()}:{normalized.upper()}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _validate_payload(verify_type: VerificationType, payload: dict) -> dict:
    if verify_type == VerificationType.REAL_NAME:
        real_name = _normalize_text(payload.get("real_name"), 32)
        id_number = _normalize_text(payload.get("id_number"), 18)
        id_front_url = _normalize_text(payload.get("id_front_url"), 255)
        id_back_url = _normalize_text(payload.get("id_back_url"), 255)
        if not real_name:
            raise BusinessException(message="请输入真实姓名", code=4301, status_code=400)
        if not id_number or not ID_NUMBER_PATTERN.match(id_number):
            raise BusinessException(message="身份证号码格式不正确", code=4302, status_code=400)
        if not id_front_url:
            raise BusinessException(message="请上传身份证人像面", code=4303, status_code=400)
        if not id_back_url:
            raise BusinessException(message="请上传身份证国徽面", code=4304, status_code=400)
        return {
            "real_name": real_name,
            "id_number": id_number.upper(),
            "id_front_url": id_front_url,
            "id_back_url": id_back_url,
        }

    if verify_type == VerificationType.ENTERPRISE:
        company_name = _normalize_text(payload.get("company_name"), 128)
        job_title = _normalize_text(payload.get("job_title"), 64)
        license_file_url = _normalize_text(payload.get("license_file_url"), 255)
        credit_code = _normalize_text(payload.get("credit_code"), 18)

        if not company_name:
            raise BusinessException(message="请输入企业名称", code=4311, status_code=400)
        if not license_file_url:
            raise BusinessException(message="请上传营业执照", code=4312, status_code=400)
        if credit_code and not CREDIT_CODE_PATTERN.match(credit_code.upper()):
            raise BusinessException(message="统一社会信用代码格式不正确", code=4313, status_code=400)

        return {
            "company_name": company_name,
            "job_title": job_title,
            "license_file_url": license_file_url,
            "credit_code": credit_code.upper() if credit_code else None,
        }

    if verify_type == VerificationType.BUSINESS_CARD:
        card_holder_name = _normalize_text(payload.get("card_holder_name"), 32)
        company_name = _normalize_text(payload.get("company_name"), 128)
        card_title = _normalize_text(payload.get("card_title"), 64)
        card_file_url = _normalize_text(payload.get("card_file_url"), 255)
        if not card_holder_name:
            raise BusinessException(message="请输入名片姓名", code=4321, status_code=400)
        if not card_file_url:
            raise BusinessException(message="请上传名片文件", code=4322, status_code=400)
        return {
            "card_holder_name": card_holder_name,
            "company_name": company_name,
            "card_title": card_title,
            "card_file_url": card_file_url,
        }

    raise BusinessException(message="不支持的认证类型", code=4399, status_code=400)


def _parse_submit_payload(payload_json: str | None) -> dict | None:
    if not payload_json:
        return None
    try:
        parsed = json.loads(payload_json)
        return parsed if isinstance(parsed, dict) else None
    except (TypeError, ValueError):
        return None


def _sanitize_admin_payload(
    verify_type: VerificationType,
    payload: dict | None,
) -> dict | None:
    if not payload:
        return payload

    safe_payload = dict(payload)
    if verify_type == VerificationType.REAL_NAME:
        if safe_payload.get("id_front_url"):
            safe_payload["id_front_url"] = "[protected]"
        if safe_payload.get("id_back_url"):
            safe_payload["id_back_url"] = "[protected]"
    return safe_payload


def _to_overview_item_map(user: User, db: Session) -> dict[str, VerificationItem]:
    record_map: dict[str, VerificationItem] = {}
    records = list_user_verifications(db=db, user_pk=user.id)

    for record in records:
        record_map[record.verify_type] = VerificationItem(
            type=VerificationType(record.verify_type),
            status=VerificationStatus(record.status),
            reject_reason=record.reject_reason,
            submitted_at=record.submitted_at,
            reviewed_at=record.reviewed_at,
        )

    for verify_type in VERIFICATION_TYPE_ORDER:
        if verify_type in record_map:
            continue
        record_map[verify_type] = VerificationItem(
            type=VerificationType(verify_type),
            status=VerificationStatus.NOT_SUBMITTED,
            reject_reason=None,
            submitted_at=None,
            reviewed_at=None,
        )

    return record_map


def _build_real_name_detail(
    *,
    profile: UserRealNameProfile | None,
    record,
    fallback_payload: dict | None,
    include_sensitive_id_number: bool,
) -> RealNameVerificationDetailData:
    status = VerificationStatus(record.status) if record else VerificationStatus.NOT_SUBMITTED
    real_name = str(profile.real_name or "").strip() if profile else str((fallback_payload or {}).get("real_name") or "").strip()
    id_front_url = str(profile.id_front_url or "").strip() if profile else str((fallback_payload or {}).get("id_front_url") or "").strip()
    id_back_url = str(profile.id_back_url or "").strip() if profile else str((fallback_payload or {}).get("id_back_url") or "").strip()
    id_number_masked = (
        str(profile.id_number_masked or "").strip()
        if profile
        else str((fallback_payload or {}).get("id_number_masked") or _mask_id_number((fallback_payload or {}).get("id_number")) or "").strip()
    )

    id_number = None
    if include_sensitive_id_number:
        if profile:
            id_number = _decrypt_sensitive_text(profile.id_number_encrypted)
        elif fallback_payload:
            id_number = _normalize_text(str(fallback_payload.get("id_number") or ""), 18)

    return RealNameVerificationDetailData(
        status=status,
        reject_reason=record.reject_reason if record else None,
        submitted_at=record.submitted_at if record else None,
        reviewed_at=record.reviewed_at if record else None,
        verified_at=(profile.verified_at if profile else None),
        verification_provider=(str(profile.verification_provider or "").strip() if profile else None),
        verified_source=(str(profile.verified_source or "").strip() if profile else None),
        real_name=real_name or None,
        id_number=id_number,
        id_number_masked=id_number_masked or None,
        id_front_url=id_front_url or None,
        id_back_url=id_back_url or None,
    )


def _assert_real_name_id_number_available(
    db: Session,
    *,
    user_pk: int,
    id_number_hash: str,
) -> None:
    existing_profile = get_user_real_name_profile_by_hash(db=db, id_number_hash=id_number_hash)
    if existing_profile is None or int(existing_profile.user_pk) == int(user_pk):
        return

    existing_record = get_user_verification(
        db=db,
        user_pk=int(existing_profile.user_pk),
        verify_type=VerificationType.REAL_NAME.value,
    )
    if existing_record and existing_record.status == VerificationStatus.APPROVED.value:
        raise BusinessException(message="该身份证件已完成实名认证", code=4307, status_code=400)
    if existing_record and existing_record.status == VerificationStatus.PENDING.value:
        raise BusinessException(message="该身份证件已被其他账号提交认证", code=4308, status_code=400)


def _upsert_legacy_real_name_profile(
    db: Session,
    *,
    user_pk: int,
    payload: dict | None,
) -> UserRealNameProfile | None:
    safe_payload = payload or {}
    id_number = _normalize_text(safe_payload.get("id_number"), 18)
    real_name = _normalize_text(safe_payload.get("real_name"), 32)
    id_front_url = _normalize_text(safe_payload.get("id_front_url"), 255)
    id_back_url = _normalize_text(safe_payload.get("id_back_url"), 255)
    if not (id_number and real_name and id_front_url and id_back_url):
        return None

    id_number_masked = _mask_id_number(id_number)
    id_number_hash = _hash_id_number(id_number)
    if not id_number_masked or not id_number_hash:
        return None

    return upsert_user_real_name_profile(
        db=db,
        user_pk=int(user_pk),
        real_name=real_name,
        id_number_masked=id_number_masked,
        id_number_hash=id_number_hash,
        id_number_encrypted=_encrypt_sensitive_text(id_number),
        id_front_url=id_front_url,
        id_back_url=id_back_url,
    )


def get_user_verification_overview(db: Session, user: User) -> VerificationOverviewData:
    item_map = _to_overview_item_map(user=user, db=db)
    items = [item_map[verify_type] for verify_type in VERIFICATION_TYPE_ORDER]
    return VerificationOverviewData(
        is_verified=bool(user.is_verified),
        items=items,
    )


def get_user_real_name_verification_detail(
    db: Session,
    *,
    user: User,
) -> RealNameVerificationDetailData:
    record = get_user_verification(db=db, user_pk=user.id, verify_type=VerificationType.REAL_NAME.value)
    profile = get_user_real_name_profile(db=db, user_pk=user.id)
    payload = _parse_submit_payload(record.submit_payload_json) if record else None
    return _build_real_name_detail(
        profile=profile,
        record=record,
        fallback_payload=payload,
        include_sensitive_id_number=True,
    )


def submit_user_verification(
    db: Session,
    user: User,
    verify_type: VerificationType,
    payload: dict,
) -> VerificationItem:
    normalized_payload = _validate_payload(verify_type=verify_type, payload=payload)

    current_record = get_user_verification(db=db, user_pk=user.id, verify_type=verify_type.value)
    if current_record and current_record.status == VerificationStatus.PENDING.value:
        raise BusinessException(message="当前认证正在审核中，请勿重复提交", code=4305, status_code=400)
    if current_record and current_record.status == VerificationStatus.APPROVED.value:
        raise BusinessException(message="当前认证已通过，无需重复提交", code=4306, status_code=400)

    verification_payload = dict(normalized_payload)
    if verify_type == VerificationType.REAL_NAME:
        id_number_hash = _hash_id_number(normalized_payload["id_number"])
        id_number_masked = _mask_id_number(normalized_payload["id_number"])
        if not id_number_hash or not id_number_masked:
            raise BusinessException(message="身份证号码格式不正确", code=4302, status_code=400)

        _assert_real_name_id_number_available(
            db=db,
            user_pk=int(user.id),
            id_number_hash=id_number_hash,
        )
        upsert_user_real_name_profile(
            db=db,
            user_pk=int(user.id),
            real_name=str(normalized_payload["real_name"]),
            id_number_masked=id_number_masked,
            id_number_hash=id_number_hash,
            id_number_encrypted=_encrypt_sensitive_text(str(normalized_payload["id_number"])),
            id_front_url=str(normalized_payload["id_front_url"]),
            id_back_url=str(normalized_payload["id_back_url"]),
        )
        verification_payload = {
            "real_name": str(normalized_payload["real_name"]),
            "id_number_masked": id_number_masked,
            "id_front_url": str(normalized_payload["id_front_url"]),
            "id_back_url": str(normalized_payload["id_back_url"]),
        }

    try:
        record = upsert_user_verification_submit(
            db=db,
            user_pk=user.id,
            verify_type=verify_type.value,
            payload=verification_payload,
        )
        sync_user_verified_flag(db=db, user=user)
    except SQLAlchemyError as exc:
        logger.exception(
            f"Failed to submit verification. user_pk={user.id}, type={verify_type.value}, error={exc}"
        )
        raise BusinessException(message="认证提交失败，请稍后重试", code=5006, status_code=500) from exc

    status_value = VerificationStatus(record.status)
    return VerificationItem(
        type=verify_type,
        status=status_value,
        reject_reason=record.reject_reason,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
    )


def _build_admin_item(db: Session, verification_id: int) -> AdminVerificationListItem:
    record = get_user_verification_by_id(db=db, verification_id=verification_id)
    if record is None:
        raise BusinessException(message="认证记录不存在", code=4404, status_code=404)

    user = get_user_by_id(db=db, user_id=record.user_pk)
    if user is None:
        raise BusinessException(message="认证关联用户不存在", code=4405, status_code=404)

    payload = _parse_submit_payload(record.submit_payload_json)
    safe_payload = _sanitize_admin_payload(VerificationType(record.verify_type), payload)
    profile = None
    if record.verify_type == VerificationType.REAL_NAME.value:
        profile = _build_real_name_detail(
            profile=get_user_real_name_profile(db=db, user_pk=user.id),
            record=record,
            fallback_payload=payload,
            include_sensitive_id_number=False,
        )

    return AdminVerificationListItem(
        id=record.id,
        user_pk=user.id,
        user_id=user.user_id,
        phone=user.phone,
        nickname=user.nickname,
        type=VerificationType(record.verify_type),
        status=VerificationStatus(record.status),
        reject_reason=record.reject_reason,
        submitted_at=record.submitted_at,
        reviewed_at=record.reviewed_at,
        submit_payload=safe_payload,
        real_name_profile=profile,
    )


def list_admin_verifications(
    db: Session,
    *,
    status: VerificationStatus | None,
    verify_type: VerificationType | None,
    page: int,
    page_size: int,
) -> AdminVerificationListData:
    safe_page = max(1, int(page))
    safe_page_size = max(1, min(int(page_size), 100))
    offset = (safe_page - 1) * safe_page_size

    status_value = status.value if status else None
    verify_type_value = verify_type.value if verify_type else None

    records, total = list_verifications_for_admin(
        db=db,
        status=status_value,
        verify_type=verify_type_value,
        offset=offset,
        limit=safe_page_size,
    )

    items: list[AdminVerificationListItem] = []
    for record in records:
        user = get_user_by_id(db=db, user_id=record.user_pk)
        if user is None:
            continue

        payload = _parse_submit_payload(record.submit_payload_json)
        safe_payload = _sanitize_admin_payload(VerificationType(record.verify_type), payload)
        real_name_profile = None
        if record.verify_type == VerificationType.REAL_NAME.value:
            real_name_profile = _build_real_name_detail(
                profile=get_user_real_name_profile(db=db, user_pk=user.id),
                record=record,
                fallback_payload=payload,
                include_sensitive_id_number=False,
            )

        items.append(
            AdminVerificationListItem(
                id=record.id,
                user_pk=user.id,
                user_id=user.user_id,
                phone=user.phone,
                nickname=user.nickname,
                type=VerificationType(record.verify_type),
                status=VerificationStatus(record.status),
                reject_reason=record.reject_reason,
                submitted_at=record.submitted_at,
                reviewed_at=record.reviewed_at,
                submit_payload=safe_payload,
                real_name_profile=real_name_profile,
            )
        )

    return AdminVerificationListData(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


def review_verification_submission(
    db: Session,
    *,
    verification_id: int,
    action: Literal["approve", "reject"],
    reject_reason: str | None,
) -> AdminVerificationListItem:
    record = get_user_verification_by_id(db=db, verification_id=verification_id)
    if record is None:
        raise BusinessException(message="认证记录不存在", code=4404, status_code=404)

    normalized_reason = _normalize_text(reject_reason, 255)
    if action == "reject" and not normalized_reason:
        raise BusinessException(message="驳回时必须填写驳回原因", code=4406, status_code=400)

    target_status = VerificationStatus.APPROVED if action == "approve" else VerificationStatus.REJECTED

    try:
        updated_record = set_user_verification_status(
            db=db,
            user_pk=record.user_pk,
            verify_type=record.verify_type,
            status=target_status,
            reject_reason=normalized_reason if target_status == VerificationStatus.REJECTED else None,
        )

        if record.verify_type == VerificationType.REAL_NAME.value:
            profile = get_user_real_name_profile(db=db, user_pk=int(record.user_pk))
            if profile is None:
                _upsert_legacy_real_name_profile(
                    db=db,
                    user_pk=int(record.user_pk),
                    payload=_parse_submit_payload(record.submit_payload_json),
                )
            set_user_real_name_profile_verified_at(
                db=db,
                user_pk=int(record.user_pk),
                verified_at=updated_record.reviewed_at if target_status == VerificationStatus.APPROVED else None,
            )
            db.commit()

        user = get_user_by_id(db=db, user_id=record.user_pk)
        if user:
            sync_user_verified_flag(db=db, user=user)
            if (
                target_status == VerificationStatus.APPROVED
                and record.verify_type == VerificationType.REAL_NAME.value
            ):
                try:
                    grant_real_name_verification_points(
                        db=db,
                        user_pk=int(record.user_pk),
                        verification_id=int(record.id),
                    )
                except SQLAlchemyError as award_exc:
                    db.rollback()
                    logger.warning(
                        f"Failed to grant real-name verification points. "
                        f"verification_id={verification_id}, user_pk={record.user_pk}, error={award_exc}"
                    )
    except SQLAlchemyError as exc:
        logger.exception(
            f"Failed to review verification. verification_id={verification_id}, action={action}, error={exc}"
        )
        raise BusinessException(message="审核处理失败，请稍后重试", code=5009, status_code=500) from exc

    return _build_admin_item(db=db, verification_id=verification_id)
