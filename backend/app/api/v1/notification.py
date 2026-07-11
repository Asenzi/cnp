from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.profile_display import public_avatar_url
from app.core.response import success_response
from app.crud import notification as notification_crud, get_user_by_id, get_user_by_business_user_id
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_public_avatar_url(avatar_url: str | None, request: Request) -> str:
    normalized = str(avatar_url or "https://cos.cnptec.site/static/logo.png").strip()
    if normalized.startswith(("http://", "https://")):
        return normalized
    if normalized.startswith("/static/"):
        return f"{str(request.base_url).rstrip('/')}{normalized}"
    return normalized


def enrich_notification_with_avatar(db: Session, notification, request: Request):
    """为通知添加相关用户的头像信息"""
    avatar_url = None
    related_user_id = None

    if notification.actor_user_pk:
        related_user = get_user_by_id(db=db, user_id=int(notification.actor_user_pk))
        if related_user:
            avatar_url = _to_public_avatar_url(public_avatar_url(related_user), request)
            related_user_id = related_user.user_id
    elif notification.link_type == "user" and notification.link_id:
        # 人脉收藏通知，link_id 是用户ID
        related_user = get_user_by_business_user_id(db=db, business_user_id=notification.link_id)
        if related_user:
            avatar_url = _to_public_avatar_url(public_avatar_url(related_user), request)
            related_user_id = related_user.user_id

    # 将 notification 转换为字典并添加额外字段
    notification_dict = {
        "id": notification.id,
        "user_pk": notification.user_pk,
        "type": notification.type,
        "title": notification.title,
        "content": notification.content,
        "link_type": notification.link_type,
        "link_id": notification.link_id,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
        "created_at": notification.created_at,
        "updated_at": notification.updated_at,
        "actor_user_pk": notification.actor_user_pk,
        "avatar_url": avatar_url,
        "related_user_id": related_user_id,
    }

    return NotificationResponse(**notification_dict)


@router.get("/system")
def get_system_notifications(
    request: Request,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取系统通知列表"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notifications = notification_crud.get_notifications_by_user(
        db=db,
        user_pk=user.id,
        notification_type="system",
        is_read=is_read,
        offset=offset,
        limit=limit,
    )

    payload = NotificationListResponse(
        items=[enrich_notification_with_avatar(db, n, request) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )
    return success_response(data=payload.model_dump(mode="json"))


@router.get("/circle")
def get_circle_notifications(
    request: Request,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取圈子通知列表"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notifications = notification_crud.get_notifications_by_user(
        db=db,
        user_pk=user.id,
        notification_type="circle",
        is_read=is_read,
        offset=offset,
        limit=limit,
    )

    payload = NotificationListResponse(
        items=[enrich_notification_with_avatar(db, n, request) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )
    return success_response(data=payload.model_dump(mode="json"))


@router.get("/network")
def get_network_notifications(
    request: Request,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取人脉关注通知列表"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notifications = notification_crud.get_notifications_by_user(
        db=db,
        user_pk=user.id,
        notification_type="network",
        is_read=is_read,
        offset=offset,
        limit=limit,
    )

    payload = NotificationListResponse(
        items=[enrich_notification_with_avatar(db, n, request) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )
    return success_response(data=payload.model_dump(mode="json"))


@router.get("/collection")
def get_collection_notifications(
    request: Request,
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取人脉、资源和圈子收藏通知列表"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notifications = notification_crud.get_notifications_by_user(
        db=db,
        user_pk=user.id,
        notification_type="collection",
        is_read=is_read,
        offset=offset,
        limit=limit,
    )

    payload = NotificationListResponse(
        items=[enrich_notification_with_avatar(db, n, request) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )
    return success_response(data=payload.model_dump(mode="json"))


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取未读通知数量"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    count = notification_crud.get_unread_notification_count(db=db, user_pk=user.id)
    return success_response(data=UnreadCountResponse(count=count).model_dump())


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """标记通知为已读"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    notification = notification_crud.get_notification_by_id(db=db, notification_id=notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在",
        )

    if notification.user_pk != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此通知",
        )

    success = notification_crud.mark_notification_as_read(db=db, notification_id=notification_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="标记已读失败",
        )

    return success_response(data={"read": True}, message="标记成功")


@router.post("/read-all")
def mark_all_notifications_read(
    notification_type: Optional[str] = Query(
        None,
        description="仅标记指定通知类型；不传则标记全部",
    ),
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """标记所有通知为已读"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    normalized_type = str(notification_type or "").strip() or None
    if normalized_type not in {None, "collection", "system", "network", "circle"}:
        raise HTTPException(status_code=400, detail="不支持的通知类型")
    count = notification_crud.mark_all_notifications_as_read(
        db=db,
        user_pk=user.id,
        notification_type=normalized_type,
    )
    return success_response(data={"count": int(count)}, message=f"已标记 {count} 条通知为已读")
