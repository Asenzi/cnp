from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_real_name_profile import UserRealNameProfile


def get_user_real_name_profile(db: Session, *, user_pk: int) -> UserRealNameProfile | None:
    stmt = select(UserRealNameProfile).where(UserRealNameProfile.user_pk == int(user_pk))
    return db.execute(stmt).scalar_one_or_none()


def get_user_real_name_profile_by_hash(
    db: Session,
    *,
    id_number_hash: str,
) -> UserRealNameProfile | None:
    normalized_hash = str(id_number_hash or "").strip().lower()
    if not normalized_hash:
        return None
    stmt = select(UserRealNameProfile).where(UserRealNameProfile.id_number_hash == normalized_hash)
    return db.execute(stmt).scalar_one_or_none()


def upsert_user_real_name_profile(
    db: Session,
    *,
    user_pk: int,
    real_name: str,
    id_number_masked: str,
    id_number_hash: str,
    id_number_encrypted: str,
    id_front_url: str,
    id_back_url: str,
    verification_provider: str | None = None,
    provider_biz_token: str | None = None,
    provider_request_id: str | None = None,
    provider_result_json: str | None = None,
    verified_source: str | None = None,
    last_verified_at: datetime | None = None,
) -> UserRealNameProfile:
    record = get_user_real_name_profile(db=db, user_pk=user_pk)
    if record is None:
        record = UserRealNameProfile(
            user_pk=int(user_pk),
            real_name=str(real_name or "").strip(),
            id_number_masked=str(id_number_masked or "").strip(),
            id_number_hash=str(id_number_hash or "").strip().lower(),
            id_number_encrypted=str(id_number_encrypted or "").strip(),
            id_front_url=str(id_front_url or "").strip(),
            id_back_url=str(id_back_url or "").strip(),
            verification_provider=str(verification_provider or "").strip() or None,
            provider_biz_token=str(provider_biz_token or "").strip() or None,
            provider_request_id=str(provider_request_id or "").strip() or None,
            provider_result_json=str(provider_result_json or "").strip() or None,
            verified_source=str(verified_source or "").strip() or None,
            last_verified_at=last_verified_at,
            verified_at=None,
        )
        db.add(record)
        return record

    record.real_name = str(real_name or "").strip()
    record.id_number_masked = str(id_number_masked or "").strip()
    record.id_number_hash = str(id_number_hash or "").strip().lower()
    record.id_number_encrypted = str(id_number_encrypted or "").strip()
    record.id_front_url = str(id_front_url or "").strip()
    record.id_back_url = str(id_back_url or "").strip()
    record.verification_provider = str(verification_provider or "").strip() or None
    record.provider_biz_token = str(provider_biz_token or "").strip() or None
    record.provider_request_id = str(provider_request_id or "").strip() or None
    record.provider_result_json = str(provider_result_json or "").strip() or None
    record.verified_source = str(verified_source or "").strip() or None
    record.last_verified_at = last_verified_at
    record.verified_at = None
    db.add(record)
    return record


def set_user_real_name_profile_verified_at(
    db: Session,
    *,
    user_pk: int,
    verified_at: datetime | None,
) -> UserRealNameProfile | None:
    record = get_user_real_name_profile(db=db, user_pk=user_pk)
    if record is None:
        return None
    record.verified_at = verified_at
    db.add(record)
    return record


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
