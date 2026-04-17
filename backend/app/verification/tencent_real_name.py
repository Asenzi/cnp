from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.crud import (
    create_user_real_name_verification_session,
    get_user_real_name_profile,
    get_user_real_name_profile_by_hash,
    get_user_real_name_verification_session_by_biz_token,
    set_user_real_name_profile_verified_at,
    set_user_verification_status,
    sync_user_verified_flag,
    update_user_real_name_verification_session_result,
    upsert_user_real_name_profile,
    upsert_user_verification_submit,
)
from app.models.user import User
from app.schemas.verification import TencentRealNameFinishData, TencentRealNameStartData
from app.verification.constants import VerificationStatus, VerificationType
from app.verification.tencent_cloud import (
    PROVIDER_NAME,
    create_detect_auth,
    get_detect_info_enhanced,
)

ID_NUMBER_PATTERN = re.compile(r"^\d{17}[\dXx]$|^\d{15}$")


def _normalize_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_len]


def _normalize_id_number(value: str | None) -> str | None:
    text = _normalize_text(value, 18)
    if not text:
        return None
    return text.upper()


def _mask_id_number(id_number: str | None) -> str | None:
    normalized = _normalize_id_number(id_number)
    if not normalized:
        return None
    if len(normalized) <= 7:
        return f"{normalized[:1]}{'*' * max(len(normalized) - 2, 1)}{normalized[-1:]}"
    return f"{normalized[:3]}{'*' * max(len(normalized) - 7, 1)}{normalized[-4:]}"


def _hash_id_number(id_number: str | None) -> str | None:
    from hashlib import sha256

    from app.core.config import settings

    normalized = _normalize_id_number(id_number)
    if not normalized:
        return None
    secret = str(settings.VERIFICATION_DATA_SECRET or settings.JWT_SECRET_KEY or "verification-secret").strip()
    payload = f"{secret}:{normalized}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _encrypt_sensitive_text(value: str | None) -> str:
    from app.verification.service import _encrypt_sensitive_text as _encrypt

    return _encrypt(str(value or "").strip())


def _assert_real_name_id_number_available(
    db: Session,
    *,
    user_pk: int,
    id_number_hash: str,
) -> None:
    existing_profile = get_user_real_name_profile_by_hash(db=db, id_number_hash=id_number_hash)
    if existing_profile is None or int(existing_profile.user_pk) == int(user_pk):
        return
    raise BusinessException(message="该身份已绑定其他账号", code=4359, status_code=400)


def start_tencent_real_name_verification(
    db: Session,
    *,
    user: User,
    real_name: str,
    id_number: str,
) -> TencentRealNameStartData:
    normalized_name = _normalize_text(real_name, 32)
    normalized_id_number = _normalize_id_number(id_number)
    if not normalized_name:
        raise BusinessException(message="请输入真实姓名", code=4301, status_code=400)
    if not normalized_id_number or not ID_NUMBER_PATTERN.match(normalized_id_number):
        raise BusinessException(message="身份证号码格式不正确", code=4302, status_code=400)

    current_profile = get_user_real_name_profile(db=db, user_pk=int(user.id))
    if current_profile and current_profile.verified_at:
        raise BusinessException(message="当前账号已完成实名认证", code=4360, status_code=400)

    id_number_hash = _hash_id_number(normalized_id_number)
    id_number_masked = _mask_id_number(normalized_id_number)
    if not id_number_hash or not id_number_masked:
        raise BusinessException(message="身份证号码格式不正确", code=4302, status_code=400)

    _assert_real_name_id_number_available(db=db, user_pk=int(user.id), id_number_hash=id_number_hash)

    detect_result = create_detect_auth(real_name=normalized_name, id_number=normalized_id_number)
    submit_payload = {
        "provider": PROVIDER_NAME,
        "provider_biz_token": detect_result.provider_biz_token,
        "provider_request_id": detect_result.provider_request_id,
        "real_name": normalized_name,
        "id_number_masked": id_number_masked,
        "verification_mode": "tencent_detect_auth",
    }

    try:
        verification_record = upsert_user_verification_submit(
            db=db,
            user_pk=int(user.id),
            verify_type=VerificationType.REAL_NAME.value,
            payload=submit_payload,
        )
        session_record = create_user_real_name_verification_session(
            db=db,
            user_pk=int(user.id),
            provider=PROVIDER_NAME,
            provider_biz_token=detect_result.provider_biz_token,
            provider_request_id=detect_result.provider_request_id,
            real_name=normalized_name,
            id_number_masked=id_number_masked,
            id_number_hash=id_number_hash,
            redirect_url=detect_result.redirect_url,
            request_payload=detect_result.raw_response,
        )
        sync_user_verified_flag(db=db, user=user)
    except IntegrityError as exc:
        logger.warning(f"Duplicate real-name verification session detected. user_pk={user.id}, error={exc}")
        raise BusinessException(message="实名认证会话创建失败，请稍后重试", code=4361, status_code=400) from exc
    except SQLAlchemyError as exc:
        logger.exception(f"Failed to start Tencent real-name verification. user_pk={user.id}, error={exc}")
        raise BusinessException(message="实名认证发起失败，请稍后重试", code=4362, status_code=500) from exc

    return TencentRealNameStartData(
        session_id=int(session_record.id),
        provider=PROVIDER_NAME,
        provider_biz_token=detect_result.provider_biz_token,
        redirect_url=detect_result.redirect_url,
        status=verification_record.status,
        real_name=normalized_name,
        id_number_masked=id_number_masked,
    )


def finish_tencent_real_name_verification(
    db: Session,
    *,
    user: User,
    provider_biz_token: str,
) -> TencentRealNameFinishData:
    normalized_token = _normalize_text(provider_biz_token, 128)
    if not normalized_token:
        raise BusinessException(message="实名认证会话不存在", code=4363, status_code=404)

    session_record = get_user_real_name_verification_session_by_biz_token(
        db=db,
        provider_biz_token=normalized_token,
    )
    if session_record is None or int(session_record.user_pk) != int(user.id):
        raise BusinessException(message="实名认证会话不存在", code=4363, status_code=404)

    detect_info = get_detect_info_enhanced(provider_biz_token=normalized_token)
    result_status = "verified" if detect_info.is_success else "failed"
    session_record = update_user_real_name_verification_session_result(
        db=db,
        session_record=session_record,
        status=result_status,
        provider_request_id=detect_info.provider_request_id,
        fail_reason=detect_info.fail_reason,
        result_payload=detect_info.raw_response,
    )

    if not detect_info.is_success:
        verification_record = set_user_verification_status(
            db=db,
            user_pk=int(user.id),
            verify_type=VerificationType.REAL_NAME.value,
            status=VerificationStatus.REJECTED,
            reject_reason=detect_info.fail_reason or "实名认证未通过",
        )
        sync_user_verified_flag(db=db, user=user)
        return TencentRealNameFinishData(
            session_id=int(session_record.id),
            provider=PROVIDER_NAME,
            provider_biz_token=session_record.provider_biz_token,
            provider_request_id=session_record.provider_request_id,
            status=verification_record.status,
            is_verified=False,
            real_name=session_record.real_name,
            id_number_masked=session_record.id_number_masked,
            verified_at=None,
        )

    detected_real_name = _normalize_text(detect_info.real_name, 32) or session_record.real_name
    detected_id_number = _normalize_id_number(detect_info.id_number)
    id_number_hash = _hash_id_number(detected_id_number) if detected_id_number else session_record.id_number_hash
    id_number_masked = _mask_id_number(detected_id_number) if detected_id_number else session_record.id_number_masked
    if not id_number_hash or not id_number_masked:
        raise BusinessException(message="腾讯云实名认证结果缺少有效身份信息", code=4364, status_code=502)

    _assert_real_name_id_number_available(db=db, user_pk=int(user.id), id_number_hash=id_number_hash)

    now = datetime.now(UTC).replace(tzinfo=None)
    try:
        profile = upsert_user_real_name_profile(
            db=db,
            user_pk=int(user.id),
            real_name=detected_real_name,
            id_number_masked=id_number_masked,
            id_number_hash=id_number_hash,
            id_number_encrypted=_encrypt_sensitive_text(detected_id_number),
            id_front_url='',
            id_back_url='',
            verification_provider=PROVIDER_NAME,
            provider_biz_token=session_record.provider_biz_token,
            provider_request_id=detect_info.provider_request_id,
            provider_result_json=json.dumps(detect_info.raw_response, ensure_ascii=False, separators=(",", ":")),
            verified_source="tencent_detect_auth",
            last_verified_at=now,
        )
        db.commit()
        set_user_real_name_profile_verified_at(db=db, user_pk=int(user.id), verified_at=now)
        verification_record = set_user_verification_status(
            db=db,
            user_pk=int(user.id),
            verify_type=VerificationType.REAL_NAME.value,
            status=VerificationStatus.APPROVED,
            reject_reason=None,
        )
        sync_user_verified_flag(db=db, user=user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning(f"Duplicate real-name identity binding detected. user_pk={user.id}, error={exc}")
        raise BusinessException(message="该身份已绑定其他账号", code=4359, status_code=400) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"Failed to complete Tencent real-name verification. user_pk={user.id}, error={exc}")
        raise BusinessException(message="实名认证结果落库失败，请稍后重试", code=4365, status_code=500) from exc

    return TencentRealNameFinishData(
        session_id=int(session_record.id),
        provider=PROVIDER_NAME,
        provider_biz_token=session_record.provider_biz_token,
        provider_request_id=profile.provider_request_id,
        status=verification_record.status,
        is_verified=True,
        real_name=profile.real_name,
        id_number_masked=profile.id_number_masked,
        verified_at=now,
    )
