import json
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_verification import UserVerification
from app.verification.constants import VerificationStatus


def list_user_verifications(db: Session, user_pk: int) -> list[UserVerification]:
    stmt = select(UserVerification).where(UserVerification.user_pk == user_pk)
    return list(db.execute(stmt).scalars().all())


def get_user_verification(db: Session, user_pk: int, verify_type: str) -> UserVerification | None:
    stmt = select(UserVerification).where(
        UserVerification.user_pk == user_pk,
        UserVerification.verify_type == verify_type,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_verification_by_id(db: Session, verification_id: int) -> UserVerification | None:
    stmt = select(UserVerification).where(UserVerification.id == verification_id)
    return db.execute(stmt).scalar_one_or_none()


def list_verifications_for_admin(
    db: Session,
    *,
    status: str | None = None,
    verify_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[UserVerification], int]:
    stmt = select(UserVerification)
    count_stmt = select(func.count(UserVerification.id))

    if status:
        stmt = stmt.where(UserVerification.status == status)
        count_stmt = count_stmt.where(UserVerification.status == status)

    if verify_type:
        stmt = stmt.where(UserVerification.verify_type == verify_type)
        count_stmt = count_stmt.where(UserVerification.verify_type == verify_type)

    stmt = stmt.order_by(desc(UserVerification.id)).offset(offset).limit(limit)

    records = list(db.execute(stmt).scalars().all())
    total = int(db.execute(count_stmt).scalar_one() or 0)
    return records, total


def upsert_user_verification_submit(
    db: Session,
    user_pk: int,
    verify_type: str,
    payload: dict,
) -> UserVerification:
    record = get_user_verification(db=db, user_pk=user_pk, verify_type=verify_type)
    payload_json = json.dumps(payload, ensure_ascii=False)
    now = datetime.now(UTC).replace(tzinfo=None)

    if record is None:
        record = UserVerification(
            user_pk=user_pk,
            verify_type=verify_type,
            status=VerificationStatus.PENDING.value,
            submit_payload_json=payload_json,
            submitted_at=now,
            reviewed_at=None,
            reject_reason=None,
        )
        db.add(record)
    else:
        record.status = VerificationStatus.PENDING.value
        record.submit_payload_json = payload_json
        record.submitted_at = now
        record.reviewed_at = None
        record.reject_reason = None
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def set_user_verification_status(
    db: Session,
    user_pk: int,
    verify_type: str,
    status: VerificationStatus,
    reject_reason: str | None = None,
) -> UserVerification:
    record = get_user_verification(db=db, user_pk=user_pk, verify_type=verify_type)
    if record is None:
        record = UserVerification(
            user_pk=user_pk,
            verify_type=verify_type,
        )
        db.add(record)
        db.flush()

    record.status = status.value
    record.reject_reason = reject_reason
    record.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    if record.submitted_at is None:
        record.submitted_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def sync_user_verified_flag(db: Session, user: User) -> User:
    stmt = select(func.count(UserVerification.id)).where(
        UserVerification.user_pk == user.id,
        UserVerification.status == VerificationStatus.APPROVED.value,
    )
    approved_count = int(db.execute(stmt).scalar_one() or 0)
    should_be_verified = approved_count > 0

    if bool(user.is_verified) == should_be_verified:
        return user

    user.is_verified = should_be_verified
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
