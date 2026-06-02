from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.crud import notification as notification_crud, get_user_by_id
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/system", response_model=NotificationListResponse)
def get_system_notifications(
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

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )


@router.get("/circle", response_model=NotificationListResponse)
def get_circle_notifications(
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

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=len(notifications),
        offset=offset,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """获取未读通知数量"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    count = notification_crud.get_unread_notification_count(db=db, user_pk=user.id)
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", response_model=dict)
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

    return {"message": "标记成功"}


@router.post("/read-all", response_model=dict)
def mark_all_notifications_read(
    db: Session = Depends(db_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """标记所有通知为已读"""
    user = get_user_by_id(db=db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    count = notification_crud.mark_all_notifications_as_read(db=db, user_pk=user.id)
    return {"message": f"已标记 {count} 条通知为已读"}
