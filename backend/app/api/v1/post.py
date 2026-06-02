from datetime import UTC, datetime
from pathlib import Path as FsPath
from secrets import token_hex

from fastapi import APIRouter, Depends, File, Path, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.asset_urls import normalize_persisted_asset_url, sanitize_public_asset_url
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_business_user_id, get_user_by_id
from app.models.resource_post import ResourcePost, ResourcePostLike
from app.models.user import User
from app.post import (
    create_resource_post,
    delete_resource_post,
    get_resource_post_detail,
    increase_resource_post_view,
    list_my_resource_posts,
    list_resource_filter_options,
    list_resource_posts,
    list_user_resource_posts,
    save_resource_post_feedback,
    save_resource_post_impressions,
    set_resource_post_like,
    set_resource_post_pin,
    set_resource_post_status,
    update_resource_post,
)
from app.review import submit_post_review
from app.schemas.post import (
    ResourcePostCreateRequest,
    ResourcePostImpressionsBatchRequest,
    ResourcePostPinPayload,
    ResourcePostRecoFeedbackRequest,
    ResourcePostStatusPayload,
)

router = APIRouter(prefix="/post", tags=["Post"])

STATIC_DIR = FsPath(__file__).resolve().parents[3] / "static"
POST_UPLOAD_DIR = STATIC_DIR / "uploads" / "post-images"

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
IMAGE_CONTENT_TYPE_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
IMAGE_SUFFIX_CONTENT_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)
    return user


def _to_public_file_url(file_url: str, request: Request | None) -> str:
    normalized = sanitize_public_asset_url(file_url)
    if not normalized:
        return normalized
    if normalized.startswith(("http://", "https://")):
        return normalized
    if normalized.startswith("/static/") and request is not None:
        return f"{str(request.base_url).rstrip('/')}{normalized}"
    return normalized


def _normalize_post_images(images: list[str], request: Request) -> list[str]:
    normalized_items: list[str] = []
    for item in list(images or []):
        normalized_items.append(
            normalize_persisted_asset_url(
                item,
                request=request,
                field_label="资源图片",
            )[:255]
        )
    return normalized_items[:9]


def _infer_image_content_type(
    *,
    content_type: str,
    file_name: str,
    file_bytes: bytes,
) -> str:
    normalized_type = str(content_type or "").lower().strip()
    if normalized_type in ALLOWED_IMAGE_CONTENT_TYPES:
        return normalized_type

    file_header = file_bytes[:16]
    if file_header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if file_header[:6] in {b"GIF87a", b"GIF89a"}:
        return "image/gif"
    if len(file_header) >= 12 and file_header[:4] == b"RIFF" and file_header[8:12] == b"WEBP":
        return "image/webp"

    suffix = FsPath(file_name or "").suffix.lower()
    return IMAGE_SUFFIX_CONTENT_TYPE_MAP.get(suffix, normalized_type)


def _publicize_post_payload(payload: dict, request: Request | None) -> dict:
    data = dict(payload or {})
    images = data.get("images") if isinstance(data.get("images"), list) else []
    data["images"] = [_to_public_file_url(str(item), request) for item in images]

    author = data.get("author") if isinstance(data.get("author"), dict) else {}
    data["author"] = {
        **author,
        "avatar_url": _to_public_file_url(str(author.get("avatar_url") or ""), request),
    }
    return data


@router.get("/ping", summary="资源模块健康检查")
def post_ping():
    return success_response(message="post module ready")


@router.get("/filters", summary="获取资源筛选项")
def get_post_filters(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = list_resource_filter_options(db=db)
    return success_response(data=payload)


@router.post("/impressions/batch", summary="上报资源推荐曝光")
def report_post_impressions_batch(
    payload: ResourcePostImpressionsBatchRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    recorded = save_resource_post_impressions(
        db=db,
        viewer_user_pk=user_id,
        post_codes=payload.post_codes,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
    )
    return success_response(
        data={"recorded": recorded},
        message="impressions recorded",
    )


@router.post("/feedback", summary="上报资源推荐行为反馈")
def report_post_reco_feedback(
    payload: ResourcePostRecoFeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    saved = save_resource_post_feedback(
        db=db,
        viewer_user_pk=user_id,
        post_code=payload.post_code,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
        event_type=payload.event_type,
        ext=payload.ext,
    )
    return success_response(
        data={"saved": bool(saved)},
        message="feedback recorded" if saved else "feedback ignored",
    )


@router.get("/feed", summary="获取资源列表")
def get_post_feed(
    request: Request,
    mode: str | None = Query(default=None),
    sort: str = Query(default="latest"),
    keyword: str | None = Query(default=None),
    industry_label: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    exclude_post_codes: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    normalized_excluded_post_codes = [
        str(item or "").strip()
        for item in str(exclude_post_codes or "").split(",")
        if str(item or "").strip()
    ]
    payload = list_resource_posts(
        db=db,
        viewer_user_pk=user_id,
        mode=mode,
        keyword=keyword,
        industry_label=industry_label,
        sort_key=sort,
        request_id=request_id,
        exclude_post_codes=normalized_excluded_post_codes,
        cursor=cursor,
        limit=limit,
    )
    payload["items"] = [_publicize_post_payload(item, request=request) for item in payload.get("items", [])]
    return success_response(data=payload)


@router.get("/mine", summary="获取我的资源发布")
def get_my_post_feed(
    request: Request,
    status: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = list_my_resource_posts(
        db=db,
        viewer_user_pk=user_id,
        status=status,
        cursor=cursor,
        limit=limit,
    )
    payload["items"] = [_publicize_post_payload(item, request=request) for item in payload.get("items", [])]
    return success_response(data=payload)


@router.get("/user/{target_user_id}/feed", summary="获取指定用户资源动态")
def get_user_post_feed(
    request: Request,
    target_user_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = str(target_user_id or "").strip()
    if len(normalized_target_user_id) != 8:
        raise BusinessException(message="目标用户ID格式无效", code=4233, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None or not bool(target_user.is_active):
        raise BusinessException(message="目标用户不存在", code=4042, status_code=404)

    payload = list_user_resource_posts(
        db=db,
        viewer_user_pk=user_id,
        target_user_pk=int(target_user.id),
        cursor=cursor,
        limit=limit,
    )
    payload["items"] = [_publicize_post_payload(item, request=request) for item in payload.get("items", [])]
    return success_response(data=payload)


def _parse_offset_cursor(cursor: str | None) -> int:
    try:
        return max(int(str(cursor or "").strip() or "0"), 0)
    except (TypeError, ValueError):
        return 0


def _serialize_interested_post(post: ResourcePost, author: User, like: ResourcePostLike, request: Request) -> dict:
    payload = {
        "post_code": str(post.post_code or "").strip(),
        "mode": str(post.mode or "cooperate"),
        "industry_label": str(post.industry_label or "").strip(),
        "title": str(post.title or "").strip(),
        "description": str(post.description or "").strip(),
        "images": [],
        "view_count": int(post.view_count or 0),
        "like_count": int(post.like_count or 0),
        "comment_count": int(post.comment_count or 0),
        "status": str(post.status or "active"),
        "liked": True,
        "interested": True,
        "is_interested": True,
        "time_text": "最近收藏",
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "interested_at": like.created_at.isoformat() if like.created_at else None,
        "author": {
            "user_id": str(author.user_id or "").strip(),
            "nickname": str(author.nickname or "").strip() or "未命名用户",
            "avatar_url": str(author.avatar_url or "").strip() or "/static/logo.png",
            "company_name": str(author.company_name or "").strip(),
            "job_title": str(author.job_title or "").strip(),
            "role": str(author.industry_label or "").strip(),
            "is_verified": bool(author.is_verified),
        },
    }
    try:
        import json

        images = json.loads(post.images_json or "[]")
        payload["images"] = images if isinstance(images, list) else []
    except Exception:
        payload["images"] = []
    return _publicize_post_payload(payload, request=request)


@router.get("/interests", summary="List interested resource posts")
def get_post_interests(
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    offset = _parse_offset_cursor(cursor)
    safe_limit = min(max(int(limit or 20), 1), 50)
    rows = db.execute(
        select(ResourcePostLike, ResourcePost, User)
        .join(ResourcePost, ResourcePost.id == ResourcePostLike.post_pk)
        .join(User, User.id == ResourcePost.author_user_pk)
        .where(
            ResourcePostLike.user_pk == int(user_id),
            ResourcePost.status == "active",
        )
        .order_by(ResourcePostLike.created_at.desc(), ResourcePostLike.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()
    page_rows = rows[:safe_limit]
    has_more = len(rows) > safe_limit
    return success_response(
        data={
            "items": [
                _serialize_interested_post(post=post, author=author, like=like, request=request)
                for like, post, author in page_rows
            ],
            "next_cursor": str(offset + len(page_rows)) if has_more else "",
            "has_more": has_more,
        }
    )


@router.post("", summary="发布资源")
def create_post(
    request: Request,
    payload: ResourcePostCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    normalized_images = _normalize_post_images(payload.images, request)
    review_result = submit_post_review(
        db=db,
        author=user,
        action_type="create",
        payload={
            "mode": payload.mode,
            "title": payload.title,
            "description": payload.description,
            "industry_label": payload.industry_label,
            "images": normalized_images,
        },
    )
    if review_result["review_required"]:
        return success_response(
            data={
                "_review": review_result["review"],
                "draft": {
                    "mode": payload.mode,
                    "title": payload.title,
                    "description": payload.description,
                    "industry_label": payload.industry_label,
                    "images": normalized_images,
                    "sync_circle_codes": payload.sync_circle_codes,
                },
            },
            message="资源内容已提交审核",
        )

    created = create_resource_post(
        db=db,
        author=user,
        mode=payload.mode,
        title=payload.title,
        description=payload.description,
        industry_label=payload.industry_label,
        images=normalized_images,
        sync_circle_codes=payload.sync_circle_codes,
        event_date=payload.event_date,
        event_time=payload.event_time,
        duration=payload.duration,
        capacity=payload.capacity,
        location=payload.location,
        address=payload.address,
        payment_type=payload.payment_type,
        price=payload.price,
        contact=payload.contact,
        detail_content=payload.detail_content,
    )
    created["_review"] = {
        "review_required": False,
        "review_status": None,
    }
    return success_response(
        data=_publicize_post_payload(created, request=request),
        message="发布成功",
    )


@router.put("/{post_code}", summary="编辑资源")
def update_post(
    request: Request,
    payload: ResourcePostCreateRequest,
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    normalized_images = _normalize_post_images(payload.images, request)
    review_result = submit_post_review(
        db=db,
        author=user,
        action_type="update",
        target_post_code=post_code,
        payload={
            "mode": payload.mode,
            "title": payload.title,
            "description": payload.description,
            "industry_label": payload.industry_label,
            "images": normalized_images,
        },
    )
    if review_result["review_required"]:
        return success_response(
            data={
                "post_code": str(post_code or "").strip(),
                "_review": review_result["review"],
                "draft": {
                    "mode": payload.mode,
                    "title": payload.title,
                    "description": payload.description,
                    "industry_label": payload.industry_label,
                    "images": normalized_images,
                    "sync_circle_codes": payload.sync_circle_codes,
                },
            },
            message="资源修改已提交审核",
        )

    updated = update_resource_post(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
        mode=payload.mode,
        title=payload.title,
        description=payload.description,
        industry_label=payload.industry_label,
        images=normalized_images,
        sync_circle_codes=payload.sync_circle_codes,
    )
    updated["_review"] = {
        "review_required": False,
        "review_status": None,
    }
    return success_response(
        data=_publicize_post_payload(updated, request=request),
        message="更新成功",
    )


@router.get("/{post_code}", summary="获取资源详情")
def get_post_detail(
    request: Request,
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = get_resource_post_detail(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
    )
    return success_response(data=_publicize_post_payload(payload, request=request))


@router.post("/{post_code}/view", summary="资源浏览计数+1")
def post_view(
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = increase_resource_post_view(
        db=db,
        post_code=post_code,
        viewer_user_pk=user_id,
    )
    return success_response(data=payload)


@router.post("/{post_code}/like", summary="点赞资源")
def post_like(
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = set_resource_post_like(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
        liked=True,
    )
    return success_response(data=payload, message="已点赞")


@router.delete("/{post_code}/like", summary="取消点赞资源")
def delete_post_like(
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = set_resource_post_like(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
        liked=False,
    )
    return success_response(data=payload, message="已取消点赞")


@router.post("/{post_code}/interest/toggle", summary="Toggle resource interest status")
def toggle_post_interest(
    post_code: str = Path(..., min_length=4),
    desired: bool | None = Query(default=None, description="Desired interest state"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    normalized_code = str(post_code or "").strip()
    post = db.execute(
        select(ResourcePost).where(ResourcePost.post_code == normalized_code)
    ).scalar_one_or_none()
    if post is None or str(post.status or "active") == "deleted":
        raise BusinessException(message="资源不存在", code=4045, status_code=404)

    existing_like = db.execute(
        select(ResourcePostLike.id).where(
            ResourcePostLike.post_pk == int(post.id),
            ResourcePostLike.user_pk == int(user_id),
        )
    ).scalar_one_or_none()
    next_interested = bool(desired) if isinstance(desired, bool) else existing_like is None
    payload = set_resource_post_like(
        db=db,
        viewer_user_pk=user_id,
        post_code=normalized_code,
        liked=next_interested,
    )
    payload["interested"] = next_interested
    payload["is_interested"] = next_interested
    return success_response(
        data=payload,
        message="已标记感兴趣" if next_interested else "已取消感兴趣",
    )


@router.post("/{post_code}/status", summary="上架/下架资源")
def update_post_status(
    request: Request,
    payload: ResourcePostStatusPayload,
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    updated = set_resource_post_status(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
        status=payload.status,
    )
    return success_response(
        data=_publicize_post_payload(updated, request=request),
        message="状态更新成功",
    )


@router.post("/{post_code}/pin", summary="置顶/取消置顶资源")
def update_post_pin(
    request: Request,
    payload: ResourcePostPinPayload,
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    updated = set_resource_post_pin(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
        pinned=payload.pinned,
    )
    return success_response(
        data=_publicize_post_payload(updated, request=request),
        message="置顶状态更新成功",
    )


@router.delete("/{post_code}", summary="删除资源")
def delete_post(
    post_code: str = Path(..., min_length=4),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = delete_resource_post(
        db=db,
        viewer_user_pk=user_id,
        post_code=post_code,
    )
    return success_response(data=payload, message="删除成功")


@router.post("/assets/upload", summary="上传资源图片")
async def upload_post_image(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=5464, status_code=400)
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise BusinessException(message="资源图片大小不能超过10MB", code=5465, status_code=400)

    content_type = _infer_image_content_type(
        content_type=file.content_type or "",
        file_name=file.filename or "",
        file_bytes=file_bytes,
    )
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise BusinessException(message="资源图片仅支持 JPG/PNG/WEBP/GIF", code=5463, status_code=400)

    suffix = FsPath(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = IMAGE_CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".jpg")

    POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = POST_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f"/static/uploads/post-images/{file_name}"
    public_url = _to_public_file_url(relative_url, request)
    return success_response(
        data={
            "name": (file.filename or file_name).strip() or file_name,
            "path": relative_url,
            "url": public_url,
            "size": len(file_bytes),
            "mime_type": content_type or "application/octet-stream",
        },
        message="上传成功",
    )
