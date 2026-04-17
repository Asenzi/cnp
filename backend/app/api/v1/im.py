import json
from datetime import UTC, datetime
from pathlib import Path as FsPath
from secrets import token_hex

from fastapi import (
    APIRouter,
    Depends,
    File,
    Path,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.core.security import decode_access_token
from app.crud import get_user_by_id
from app.models.user import User
from app.im import (
    accept_friend_request,
    create_friend_request,
    get_im_overview,
    ignore_friend_request,
    im_realtime_hub,
    list_conversation_messages,
    list_conversations,
    list_friend_requests,
    list_system_notices,
    mark_conversation_read,
    revoke_conversation_message,
    send_conversation_message,
)
from app.schemas.im import FriendRequestCreateRequest, MessageSendRequest

router = APIRouter(prefix="/im", tags=["IM"])

STATIC_DIR = FsPath(__file__).resolve().parents[3] / "static"
IM_UPLOAD_DIR = STATIC_DIR / "uploads" / "im"

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

IMAGE_CONTENT_TYPE_EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

FILE_CONTENT_TYPE_EXTENSION_MAP = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/zip": ".zip",
    "application/x-zip-compressed": ".zip",
    "text/plain": ".txt",
}


def _to_public_file_url(file_url: str, request: Request) -> str:
    normalized = str(file_url or "").strip()
    if not normalized:
        return normalized
    if normalized.startswith(("http://", "https://", "wxfile://", "file://")):
        return normalized
    if normalized.startswith("/static/"):
        return f"{str(request.base_url).rstrip('/')}{normalized}"
    return normalized


def _resolve_target_user_by_any_id(db: Session, target_user_id: str):
    normalized = str(target_user_id or "").strip()
    if not normalized:
        raise BusinessException(message="目标用户ID不能为空", code=4411, status_code=400)

    row = db.execute(select(User).where(User.user_id == normalized)).scalar_one_or_none()
    if row is not None:
        return row

    if normalized.isdigit():
        row = get_user_by_id(db=db, user_id=int(normalized))
        if row is not None:
            return row

    raise BusinessException(message="目标用户不存在", code=4042, status_code=404)


def _authenticate_websocket_user(db: Session, token: str):
    if not token:
        raise BusinessException(message="Missing token", code=4401, status_code=401)

    payload = decode_access_token(token)
    if not payload:
        raise BusinessException(message="Invalid token", code=4402, status_code=401)

    subject = payload.get("sub")
    token_version_claim = payload.get("tv")
    try:
        user_pk = int(subject)
    except (TypeError, ValueError) as exc:
        raise BusinessException(message="Invalid token subject", code=4403, status_code=401) from exc

    user = get_user_by_id(db=db, user_id=user_pk)
    if user is None:
        raise BusinessException(message="User not found", code=4041, status_code=401)
    if not bool(user.is_active):
        raise BusinessException(message="User is disabled", code=4404, status_code=403)

    try:
        token_version = int(token_version_claim) if token_version_claim is not None else 0
    except (TypeError, ValueError) as exc:
        raise BusinessException(message="Invalid token version", code=4405, status_code=401) from exc

    if int(user.token_version or 0) != token_version:
        raise BusinessException(message="Token has been invalidated", code=4406, status_code=401)
    return user


@router.get("/ping", summary="IM health check")
def im_ping():
    return success_response(message="im module ok")


@router.get("/overview", summary="IM overview")
def get_overview(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_im_overview(db=db, viewer_user_pk=user_id)
    return success_response(data=payload)


@router.get("/conversations", summary="Conversation list")
def get_conversations(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_conversations(
        db=db,
        viewer_user_pk=user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.get("/conversations/{target_user_id}/messages", summary="Conversation messages")
def get_conversation_messages(
    target_user_id: str = Path(..., min_length=1),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_conversation_messages(
        db=db,
        viewer_user_pk=user_id,
        target_user_id=target_user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.post("/conversations/{target_user_id}/messages", summary="Send message")
async def post_conversation_message(
    payload: MessageSendRequest,
    target_user_id: str = Path(..., min_length=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = send_conversation_message(
        db=db,
        viewer_user_pk=user_id,
        target_user_id=target_user_id,
        content=payload.content,
        content_type=payload.content_type,
    )
    target_pk = int(result.get("receiver_user_pk", 0))
    sender_pk = int(result.get("sender_user_pk", 0))
    receiver_online = await im_realtime_hub.is_online(user_pk=target_pk)

    await im_realtime_hub.send_to_users(
        user_pks=[int(result.get("sender_user_pk", 0)), int(result.get("receiver_user_pk", 0))],
        event="message.new",
        data={"message": result},
    )
    await im_realtime_hub.send_to_user(
        user_pk=sender_pk,
        event="message.delivery",
        data={
            "message_id": str(result.get("id", "")),
            "target_user_id": str(result.get("receiver_user_id", "")),
            "delivered": bool(receiver_online),
        },
    )
    return success_response(data=result, message="发送成功")


@router.post("/conversations/{target_user_id}/messages/{message_id}/revoke", summary="Revoke message")
async def post_revoke_conversation_message(
    target_user_id: str = Path(..., min_length=1),
    message_id: int = Path(..., ge=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = revoke_conversation_message(
        db=db,
        viewer_user_pk=user_id,
        target_user_id=target_user_id,
        message_id=message_id,
    )
    await im_realtime_hub.send_to_users(
        user_pks=[int(result.get("sender_user_pk", 0)), int(result.get("receiver_user_pk", 0))],
        event="message.revoked",
        data={"message": result},
    )
    return success_response(data=result, message="消息已撤回")


@router.post("/conversations/{target_user_id}/read", summary="Mark conversation read")
async def post_mark_conversation_read(
    target_user_id: str = Path(..., min_length=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = mark_conversation_read(
        db=db,
        viewer_user_pk=user_id,
        target_user_id=target_user_id,
    )
    if int(result.get("updated", 0)) <= 0:
        return success_response(data=result, message="已更新已读状态")
    await im_realtime_hub.send_to_user(
        user_pk=int(result.get("target_user_pk", 0)),
        event="conversation.read",
        data=result,
    )
    return success_response(data=result, message="已更新已读状态")


@router.get("/presence/{target_user_id}", summary="Presence status")
async def get_presence_status(
    target_user_id: str = Path(..., min_length=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _ = get_user_by_id(db=db, user_id=user_id)
    target_user = _resolve_target_user_by_any_id(db=db, target_user_id=target_user_id)
    online = await im_realtime_hub.is_online(user_pk=int(target_user.id))
    return success_response(
        data={
            "user_id": str(target_user.user_id or "").strip(),
            "online": bool(online),
        }
    )


@router.websocket("/ws")
async def im_websocket(
    websocket: WebSocket,
    token: str = Query(default=""),
    db: Session = Depends(db_session),
):
    try:
        user = _authenticate_websocket_user(db=db, token=token)
    except BusinessException as exc:
        await websocket.close(code=4401, reason=exc.message)
        return

    await im_realtime_hub.connect(user_pk=int(user.id), websocket=websocket)
    await im_realtime_hub.broadcast(
        event="presence.changed",
        data={
            "user_id": str(user.user_id or "").strip(),
            "online": True,
        },
    )
    await websocket.send_json(
        {
            "event": "ws.ready",
            "data": {
                "user_id": str(user.user_id or "").strip(),
            },
        }
    )

    try:
        while True:
            text = await websocket.receive_text()
            raw = str(text or "").strip()
            if not raw:
                continue

            action = ""
            payload: dict = {}
            try:
                payload = json.loads(raw)
                action = str(payload.get("action") or "").strip().lower()
            except Exception:  # noqa: BLE001
                action = raw.lower()

            if action == "ping":
                await websocket.send_json(
                    {
                        "event": "ws.pong",
                        "data": {
                            "ts": int(datetime.now(UTC).timestamp() * 1000),
                        },
                    }
                )
                continue

            if action == "presence.check":
                target_user_id = str(payload.get("target_user_id") or "").strip()
                if not target_user_id:
                    continue
                try:
                    target_user = _resolve_target_user_by_any_id(db=db, target_user_id=target_user_id)
                    online = await im_realtime_hub.is_online(user_pk=int(target_user.id))
                    await websocket.send_json(
                        {
                            "event": "presence.state",
                            "data": {
                                "user_id": str(target_user.user_id or "").strip(),
                                "online": bool(online),
                            },
                        }
                    )
                except Exception:  # noqa: BLE001
                    continue
    except WebSocketDisconnect:
        pass
    finally:
        await im_realtime_hub.disconnect(user_pk=int(user.id), websocket=websocket)
        still_online = await im_realtime_hub.is_online(user_pk=int(user.id))
        if not still_online:
            await im_realtime_hub.broadcast(
                event="presence.changed",
                data={
                    "user_id": str(user.user_id or "").strip(),
                    "online": False,
                },
            )


@router.get("/friend-requests", summary="Friend requests")
def get_friend_requests(
    tab: str = Query(default="pending"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_friend_requests(
        db=db,
        viewer_user_pk=user_id,
        tab=tab,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.post("/friend-requests", summary="Create friend request")
def post_friend_request(
    payload: FriendRequestCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    result = create_friend_request(
        db=db,
        viewer_user_pk=user_id,
        target_business_user_id=payload.target_user_id,
        message=payload.message,
    )
    return success_response(
        data=result,
        message="已发送好友申请" if not result.get("duplicate") else "你已发送过好友申请",
    )


@router.post("/friend-requests/{request_id}/accept", summary="Accept friend request")
def post_accept_friend_request(
    request_id: int = Path(..., ge=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = accept_friend_request(
        db=db,
        viewer_user_pk=user_id,
        request_id=request_id,
    )
    return success_response(data=payload, message="已接受好友申请")


@router.post("/friend-requests/{request_id}/ignore", summary="Ignore friend request")
def post_ignore_friend_request(
    request_id: int = Path(..., ge=1),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = ignore_friend_request(
        db=db,
        viewer_user_pk=user_id,
        request_id=request_id,
    )
    return success_response(data=payload, message="已忽略好友申请")


@router.get("/system-notices", summary="System notices")
def get_system_notices(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_system_notices(
        db=db,
        viewer_user_pk=user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.post("/assets/upload", summary="Upload IM asset file")
async def post_im_asset_upload(
    request: Request,
    kind: str = Query(default="image"),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    safe_kind = str(kind or "image").strip().lower()
    if safe_kind not in {"image", "file"}:
        raise BusinessException(message="上传类型不支持", code=4451, status_code=400)

    content_type = (file.content_type or "").lower().strip()
    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=4452, status_code=400)

    if safe_kind == "image":
        if content_type not in IMAGE_CONTENT_TYPE_EXTENSION_MAP:
            raise BusinessException(message="仅支持 JPG/PNG/WEBP/GIF 图片", code=4453, status_code=400)
        if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise BusinessException(message="图片大小不能超过 10MB", code=4454, status_code=400)
        suffix = IMAGE_CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".jpg")
    else:
        if content_type not in FILE_CONTENT_TYPE_EXTENSION_MAP:
            raise BusinessException(message="仅支持 PDF/DOC/DOCX/XLS/XLSX/ZIP/TXT", code=4455, status_code=400)
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise BusinessException(message="文件大小不能超过 20MB", code=4456, status_code=400)
        suffix = FILE_CONTENT_TYPE_EXTENSION_MAP.get(content_type, ".bin")

    provided_suffix = FsPath(file.filename or "").suffix.lower()
    if provided_suffix and len(provided_suffix) <= 10:
        suffix = provided_suffix

    save_dir = IM_UPLOAD_DIR / safe_kind
    save_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = save_dir / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f"/static/uploads/im/{safe_kind}/{file_name}"
    display_name = (file.filename or file_name).strip() or file_name
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            "kind": safe_kind,
            "name": display_name,
            "size": len(file_bytes),
            "mime_type": content_type or "application/octet-stream",
            "path": relative_url,
            "url": _to_public_file_url(relative_url, request),
        },
        message="上传成功",
    )
