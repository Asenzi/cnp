from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import get_user_by_id
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.admin_user import AdminUser


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_db_dep() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(db_session),
) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    subject = payload.get("sub")
    token_version_claim = payload.get("tv")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    try:
        token_version = int(token_version_claim) if token_version_claim is not None else 0
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token version")

    if token_version != int(user.token_version or 0):
        raise HTTPException(status_code=401, detail="Token has been invalidated")

    if not bool(user.is_active):
        raise HTTPException(status_code=403, detail="User is disabled")

    return user_id


def get_current_user_id_from_header_or_query(
    authorization: str | None = Header(default=None, alias="Authorization"),
    access_token: str | None = Query(default=None, alias="access_token"),
    db: Session = Depends(db_session),
) -> int:
    if not authorization and access_token:
        authorization = f"Bearer {access_token}"
    return get_current_user_id(authorization=authorization, db=db)


def require_admin_token(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> str:
    token = settings.ADMIN_REVIEW_TOKEN.strip()
    if not token:
        raise HTTPException(status_code=503, detail="Admin review token is not configured")
    if not x_admin_token or x_admin_token.strip() != token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return "admin"


def get_current_admin_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(db_session),
) -> AdminUser:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Invalid Authorization header")

        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        if str(payload.get("scope") or "").strip().lower() != "admin":
            raise HTTPException(status_code=403, detail="Admin scope required")

        subject = payload.get("sub")
        token_version_claim = payload.get("tv")
        try:
            admin_id = int(subject)
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid admin token subject")

        admin = db.execute(select(AdminUser).where(AdminUser.id == admin_id).limit(1)).scalar_one_or_none()
        if admin is None:
            raise HTTPException(status_code=401, detail="Admin user not found")
        if not bool(admin.is_active):
            raise HTTPException(status_code=403, detail="Admin user is disabled")

        try:
            token_version = int(token_version_claim) if token_version_claim is not None else 0
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid admin token version")
        if token_version != int(admin.token_version or 0):
            raise HTTPException(status_code=401, detail="Admin token has been invalidated")
        return admin

    review_token = settings.ADMIN_REVIEW_TOKEN.strip()
    if review_token and x_admin_token and x_admin_token.strip() == review_token:
        preferred_username = str(settings.ADMIN_DEFAULT_USERNAME or "").strip()
        admin = None
        if preferred_username:
            admin = db.execute(
                select(AdminUser).where(AdminUser.username == preferred_username).limit(1)
            ).scalar_one_or_none()
        if admin is None:
            admin = db.execute(
                select(AdminUser).where(AdminUser.is_active.is_(True)).order_by(AdminUser.id.asc()).limit(1)
            ).scalar_one_or_none()
        if admin is None:
            raise HTTPException(status_code=503, detail="Admin user is not initialized")
        return admin

    raise HTTPException(status_code=401, detail="Missing admin authorization")


def get_current_admin_user_from_header_or_query(
    authorization: str | None = Header(default=None, alias="Authorization"),
    access_token: str | None = Query(default=None, alias="access_token"),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    db: Session = Depends(db_session),
) -> AdminUser:
    if not authorization and access_token:
        authorization = f"Bearer {access_token}"
    return get_current_admin_user(
        authorization=authorization,
        x_admin_token=x_admin_token,
        db=db,
    )
