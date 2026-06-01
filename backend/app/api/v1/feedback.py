import json
import re
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.logger import logger
from app.core.response import success_response
from app.crud import get_user_by_id
from app.models.user_feedback import UserFeedback
from app.schemas.feedback import HelpFeedbackSubmitData, HelpFeedbackSubmitRequest

router = APIRouter(prefix="/feedback", tags=["Feedback"])

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"
FEEDBACK_UPLOAD_DIR = STATIC_DIR / "uploads" / "feedback"

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
IMAGE_CONTENT_TYPE_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
CONTACT_PHONE_REGEX = re.compile(r"^1\d{10}$")
CONTACT_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4704, status_code=404)
    return user


def _to_public_file_url(file_url: str, request: Request) -> str:
    if file_url.startswith(("http://", "https://")):
        return file_url
    if file_url.startswith("/static/uploads/"):
        return f"{str(request.base_url).rstrip('/')}{file_url}"
    return file_url


def _normalize_contact(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    if len(normalized) > 100:
        normalized = normalized[:100]
    if CONTACT_PHONE_REGEX.fullmatch(normalized) or CONTACT_EMAIL_REGEX.fullmatch(normalized):
        return normalized
    raise BusinessException(message="联系方式仅支持手机号或邮箱", code=4705, status_code=400)


def _normalize_source_page(value: str | None) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return "pages/me/help-feedback/index"
    return normalized[:64]


def _normalize_feedback_images(images: list[dict] | None) -> list[dict]:
    normalized_items: list[dict] = []
    for item in list(images or []):
        path = str(item.get("path") or "").strip()
        if not path.startswith("/static/uploads/feedback/"):
            raise BusinessException(message="反馈截图路径无效，请重新上传", code=4706, status_code=400)

        name = str(item.get("name") or "").strip() or None
        if name and len(name) > 128:
            name = name[:128]

        raw_size = item.get("size")
        size = int(raw_size) if isinstance(raw_size, int) and raw_size >= 0 else None
        normalized_items.append(
            {
                "path": path[:255],
                "name": name,
                "size": size,
            }
        )
    return normalized_items[:3]


def _build_ticket_no() -> str:
    return f"FB{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}{token_hex(2).upper()}"


@router.post("/assets/upload", summary="上传反馈截图")
async def upload_feedback_image(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise BusinessException(message="反馈截图仅支持 JPG/PNG/WEBP/GIF", code=4701, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=4702, status_code=400)
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise BusinessException(message="反馈截图大小不能超过10MB", code=4703, status_code=400)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = IMAGE_CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".jpg")

    FEEDBACK_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = FEEDBACK_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f"/static/uploads/feedback/{file_name}"
    public_url = _to_public_file_url(relative_url, request)
    display_name = (file.filename or file_name).strip() or file_name
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            "name": display_name,
            "path": relative_url,
            "url": public_url,
            "size": len(file_bytes),
            "mime_type": content_type or "application/octet-stream",
        },
        message="上传成功",
    )


@router.post("", summary="提交帮助与反馈")
def submit_help_feedback(
    payload: HelpFeedbackSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    normalized_description = payload.description.strip()
    if len(normalized_description) < 5:
        raise BusinessException(message="问题描述至少填写5个字", code=4707, status_code=400)

    row = UserFeedback(
        ticket_no=_build_ticket_no(),
        user_pk=int(user_id),
        feedback_type=payload.feedback_type,
        description=normalized_description,
        contact=_normalize_contact(payload.contact),
        images_json=json.dumps(
            _normalize_feedback_images([item.model_dump() for item in payload.images]),
            ensure_ascii=False,
        ),
        source_page=_normalize_source_page(payload.source_page),
        status="pending",
    )

    try:
        db.add(row)
        db.commit()
        db.refresh(row)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to save help feedback: %s", exc)
        raise BusinessException(message="反馈提交失败，请稍后重试", code=4708, status_code=500) from exc

    data = HelpFeedbackSubmitData(
        id=int(row.id),
        ticket_no=str(row.ticket_no),
        status=str(row.status),
        created_at=row.created_at.isoformat() if row.created_at else None,
    )
    return success_response(data=data.model_dump(mode="json"), message="反馈已提交")
