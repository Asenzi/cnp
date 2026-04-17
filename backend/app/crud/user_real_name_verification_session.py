import json
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.user_real_name_verification_session import UserRealNameVerificationSession


def create_user_real_name_verification_session(
    db: Session,
    *,
    user_pk: int,
    provider: str,
    provider_biz_token: str,
    provider_request_id: str | None,
    real_name: str,
    id_number_masked: str,
    id_number_hash: str,
    redirect_url: str | None,
    request_payload: dict | None,
) -> UserRealNameVerificationSession:
    record = UserRealNameVerificationSession(
        user_pk=int(user_pk),
        provider=str(provider or "").strip() or "tencent_cloud",
        provider_biz_token=str(provider_biz_token or "").strip(),
        provider_request_id=str(provider_request_id or "").strip() or None,
        status="pending",
        real_name=str(real_name or "").strip(),
        id_number_masked=str(id_number_masked or "").strip(),
        id_number_hash=str(id_number_hash or "").strip().lower(),
        redirect_url=str(redirect_url or "").strip() or None,
        request_payload_json=json.dumps(request_payload or {}, ensure_ascii=False, separators=(",", ":")),
        result_payload_json=None,
        fail_reason=None,
        started_at=datetime.now(UTC).replace(tzinfo=None),
        finished_at=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_real_name_verification_session_by_biz_token(
    db: Session,
    *,
    provider_biz_token: str,
) -> UserRealNameVerificationSession | None:
    normalized = str(provider_biz_token or "").strip()
    if not normalized:
        return None
    stmt = select(UserRealNameVerificationSession).where(
        UserRealNameVerificationSession.provider_biz_token == normalized
    )
    return db.execute(stmt).scalar_one_or_none()


def get_latest_user_real_name_verification_session(
    db: Session,
    *,
    user_pk: int,
) -> UserRealNameVerificationSession | None:
    stmt = (
        select(UserRealNameVerificationSession)
        .where(UserRealNameVerificationSession.user_pk == int(user_pk))
        .order_by(desc(UserRealNameVerificationSession.id))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def update_user_real_name_verification_session_result(
    db: Session,
    *,
    session_record: UserRealNameVerificationSession,
    status: str,
    provider_request_id: str | None,
    fail_reason: str | None,
    result_payload: dict | None,
) -> UserRealNameVerificationSession:
    session_record.status = str(status or "").strip() or session_record.status
    session_record.provider_request_id = str(provider_request_id or "").strip() or session_record.provider_request_id
    session_record.fail_reason = str(fail_reason or "").strip() or None
    session_record.result_payload_json = json.dumps(
        result_payload or {},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    session_record.finished_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(session_record)
    db.commit()
    db.refresh(session_record)
    return session_record
