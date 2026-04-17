from datetime import UTC, datetime
from pathlib import Path as FsPath
from secrets import token_hex

from fastapi import APIRouter, Depends, File, Path, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_business_user_id, get_user_by_id
from app.post import (
    create_resource_post,
    delete_resource_post,
    get_resource_post_detail,
    increase_resource_post_view,
    list_my_resource_posts,
    list_resource_filter_options,
    list_resource_posts,
    list_user_resource_posts,
    set_resource_post_like,
    set_resource_post_pin,
    set_resource_post_status,
    update_resource_post,
)
from app.review import submit_post_review
from app.schemas.post import (
    ResourcePostCreateRequest,
    ResourcePostPinPayload,
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


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)
    return user


def _to_public_file_url(file_url: str, request: Request | None) -> str:
    normalized = str(file_url or "").strip()
    if not normalized:
        return normalized
    if normalized.startswith(("http://", "https://", "wxfile://", "file://")):
        return normalized
    if normalized.startswith("/static/") and request is not None:
        return f"{str(request.base_url).rstrip('/')}{normalized}"
    return normalized


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


@router.post("", summary="发布资源")
def create_post(
    request: Request,
    payload: ResourcePostCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    review_result = submit_post_review(
        db=db,
        author=user,
        action_type="create",
        payload={
            "mode": payload.mode,
            "title": payload.title,
            "description": payload.description,
            "industry_label": payload.industry_label,
            "images": payload.images,
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
                    "images": payload.images,
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
        images=payload.images,
        sync_circle_codes=payload.sync_circle_codes,
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
            "images": payload.images,
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
                    "images": payload.images,
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
        images=payload.images,
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

    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise BusinessException(message="资源图片仅支持 JPG/PNG/WEBP/GIF", code=5463, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=5464, status_code=400)
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise BusinessException(message="资源图片大小不能超过10MB", code=5465, status_code=400)

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
