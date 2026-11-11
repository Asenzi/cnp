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

    from sqlalchemy import select
    from app.models.notification import Notification
    query = select(Notification).where(Notification.user_pk == user.id, Notification.type.notin_(["activity", "collection", "network"]))
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    notifications = db.scalars(query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit)).all()

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


from pydantic import BaseModel
from typing import Literal

class ActivityReport(BaseModel):
    target_type: Literal["user", "resource", "circle"]
    target_id: str
    action: Literal["view", "share"]


@router.post("/activity")
def report_activity(payload: ActivityReport, db: Session = Depends(db_session), current_user_id: int = Depends(get_current_user_id)):
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.models.notification import Notification
    from app.models.circle import Circle
    from app.models.resource_post import ResourcePost
    from app.core.profile_display import public_nickname
    actor = get_user_by_id(db=db, user_id=current_user_id)
    if actor is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    target_id = payload.target_id.strip()
    if not target_id or len(target_id) > 100:
        raise HTTPException(status_code=400, detail="目标编号无效")
    if payload.target_type == "user":
        target = get_user_by_business_user_id(db=db, business_user_id=target_id)
        owner_pk = target.id if target and target.is_active else None
        target_label = "人脉"
    elif payload.target_type == "resource":
        target = db.scalar(select(ResourcePost).where(ResourcePost.post_code == target_id, ResourcePost.status == "active"))
        owner_pk = target.author_user_pk if target else None
        target_label = "资源"
    else:
        target = db.scalar(select(Circle).where(Circle.circle_code == target_id, Circle.status == "active"))
        owner_pk = target.owner_user_pk if target else None
        target_label = "圈子"
    if owner_pk is None:
        raise HTTPException(status_code=404, detail="内容不存在")
    if owner_pk == actor.id:
        return success_response(data={"recorded": False})
    action_label = "查看了" if payload.action == "view" else "发起分享了"
    title = f"{target_label}{'浏览' if payload.action == 'view' else '分享'}通知"
    duplicate = db.scalar(select(Notification.id).where(Notification.user_pk == owner_pk, Notification.actor_user_pk == actor.id, Notification.type == "activity", Notification.title == title, Notification.link_type == payload.target_type, Notification.link_id == target_id, Notification.created_at >= datetime.utcnow() - timedelta(minutes=30)).limit(1))
    if duplicate:
        return success_response(data={"recorded": False})
    db.add(Notification(user_pk=owner_pk, actor_user_pk=actor.id, type="activity", title=title, content=f"{public_nickname(actor)}{action_label}你的{target_label}", link_type=payload.target_type, link_id=target_id))
    db.commit()
    return success_response(data={"recorded": True})


@router.get("/activity")
def get_activity_notifications(request: Request, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(db_session), current_user_id: int = Depends(get_current_user_id)):
    from sqlalchemy import select
    from app.models.notification import Notification
    rows = db.scalars(select(Notification).where(Notification.user_pk == current_user_id, Notification.type.in_(["activity", "collection", "network"])).order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit)).all()
    return success_response(data={"items": [enrich_notification_with_avatar(db, n, request).model_dump(mode="json") for n in rows], "offset": offset, "limit": limit})


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
    if normalized_type not in {None, "collection", "system", "network", "circle", "activity"}:
        raise HTTPException(status_code=400, detail="不支持的通知类型")
    if normalized_type == "activity":
        count = sum(notification_crud.mark_all_notifications_as_read(db=db, user_pk=user.id, notification_type=kind) for kind in ("activity", "collection", "network"))
        return success_response(data={"count": count}, message="标记成功")
    if normalized_type == "system":
        from datetime import datetime
        from sqlalchemy import update
        from app.models.notification import Notification
        result = db.execute(update(Notification).where(Notification.user_pk == user.id, Notification.is_read.is_(False), Notification.type.notin_(["activity", "collection", "network"])).values(is_read=True, read_at=datetime.utcnow()))
        db.commit()
        return success_response(data={"count": int(result.rowcount)}, message="标记成功")
    count = notification_crud.mark_all_notifications_as_read(
        db=db,
        user_pk=user.id,
        notification_type=normalized_type,
    )
    return success_response(data={"count": int(count)}, message=f"已标记 {count} 条通知为已读")
