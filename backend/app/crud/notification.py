from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_pk: int,
    title: str,
    content: str,
    notification_type: str = "system",
    link_type: Optional[str] = None,
    link_id: Optional[str] = None,
) -> Notification:
    """创建通知"""
    notification = Notification(
        user_pk=user_pk,
        type=notification_type,
        title=title,
        content=content,
        link_type=link_type,
        link_id=link_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications_by_user(
    db: Session,
    user_pk: int,
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    offset: int = 0,
    limit: int = 20,
) -> list[Notification]:
    """获取用户的通知列表"""
    query = select(Notification).where(Notification.user_pk == user_pk)

    if notification_type is not None:
        query = query.where(Notification.type == notification_type)

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    query = query.order_by(desc(Notification.created_at)).offset(offset).limit(limit)

    result = db.execute(query)
    return list(result.scalars().all())


def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
    """通过ID获取通知"""
    result = db.execute(select(Notification).where(Notification.id == notification_id))
    return result.scalar_one_or_none()


def mark_notification_as_read(db: Session, notification_id: int) -> bool:
    """标记通知为已读"""
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id)
        .values(is_read=True, read_at=datetime.utcnow())
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0


def mark_all_notifications_as_read(
    db: Session,
    user_pk: int,
    notification_type: Optional[str] = None,
) -> int:
    """标记用户所有通知为已读"""
    filters = [Notification.user_pk == user_pk, Notification.is_read == False]
    if notification_type:
        filters.append(Notification.type == notification_type)
    stmt = update(Notification).where(*filters).values(is_read=True, read_at=datetime.utcnow())
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def get_unread_notification_count(db: Session, user_pk: int) -> int:
    """获取用户未读通知数量"""
    result = db.execute(
        select(Notification)
        .where(Notification.user_pk == user_pk, Notification.is_read == False)
    )
    return len(list(result.scalars().all()))


def delete_notification(db: Session, notification_id: int) -> bool:
    """删除通知"""
    notification = get_notification_by_id(db, notification_id)
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False
