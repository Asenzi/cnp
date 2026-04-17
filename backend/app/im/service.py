import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.network_reco_feedback import NetworkRecoFeedback
from app.models.network_reco_impression import NetworkRecoImpression
from app.models.system_notice import SystemNotice
from app.models.user import User
from app.models.user_connection import UserConnection
from app.models.user_friend_request import UserFriendRequest
from app.models.user_message import UserMessage

SUPPORTED_REQUEST_TABS = {"pending", "sent"}
PENDING_STATUS = "pending"
ALLOWED_MESSAGE_CONTENT_TYPES = {"text", "image", "file", "location", "card"}
RECALL_WINDOW_SECONDS = 120


def _encode_cursor(offset: int) -> str | None:
    if offset <= 0:
        return None
    payload = json.dumps({"offset": int(offset)}, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
        return max(int(payload.get("offset", 0)), 0)
    except Exception:  # noqa: BLE001
        return 0


def _format_time_text(raw_time: datetime | None) -> str:
    if not raw_time:
        return ""

    now = datetime.now(UTC).replace(tzinfo=None)
    target = raw_time.replace(tzinfo=None) if raw_time.tzinfo else raw_time
    delta = now - target
    total_seconds = max(int(delta.total_seconds()), 0)
    total_days = total_seconds // (24 * 3600)

    if total_days <= 0:
        return target.strftime("%H:%M")
    if total_days == 1:
        return "昨天"
    if total_days <= 6:
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[target.weekday()]
    return target.strftime("%m-%d")


def _build_conversation_preview(content: str, content_type: str) -> str:
    normalized_content_type = str(content_type or "text").strip().lower()
    text = str(content or "").strip()

    if normalized_content_type == "image":
        return "[图片]"
    if normalized_content_type == "card":
        return "[名片]"
    if normalized_content_type == "file":
        return "[文件]"
    if normalized_content_type == "location":
        return "[位置]"
    if normalized_content_type == "recalled":
        return "[已撤回]"
    if text.startswith("CARD:"):
        return "[名片]"
    if text.startswith("FILE:"):
        return "[文件]"
    if text.startswith("LOCATION:"):
        return "[位置]"
    return text or "暂无消息"


def _ensure_user(db: Session, user_pk: int) -> User:
    user = db.execute(select(User).where(User.id == int(user_pk))).scalar_one_or_none()
    if user is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)
    return user


def _resolve_target_user(db: Session, *, target_user_id: str) -> User:
    normalized = str(target_user_id or "").strip()
    if not normalized:
        raise BusinessException(message="目标用户ID不能为空", code=4411, status_code=400)

    by_business_id = db.execute(select(User).where(User.user_id == normalized)).scalar_one_or_none()
    if by_business_id is not None:
        return by_business_id

    if normalized.isdigit():
        by_pk = db.execute(select(User).where(User.id == int(normalized))).scalar_one_or_none()
        if by_pk is not None:
            return by_pk

    raise BusinessException(message="目标用户不存在", code=4042, status_code=404)


def get_im_overview(db: Session, *, viewer_user_pk: int) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)

    pending_total = (
        db.execute(
            select(func.count())
            .select_from(UserFriendRequest)
            .where(
                UserFriendRequest.target_user_pk == viewer.id,
                UserFriendRequest.status == PENDING_STATUS,
            )
        ).scalar_one()
        or 0
    )

    latest_pending_row = db.execute(
        select(User.nickname)
        .join(UserFriendRequest, User.id == UserFriendRequest.requester_user_pk)
        .where(
            UserFriendRequest.target_user_pk == viewer.id,
            UserFriendRequest.status == PENDING_STATUS,
        )
        .order_by(UserFriendRequest.created_at.desc(), UserFriendRequest.id.desc())
        .limit(1)
    ).first()
    latest_pending_name = str(latest_pending_row[0]).strip() if latest_pending_row else ""
    latest_pending_text = f"{latest_pending_name}申请添加你为好友" if latest_pending_name else "暂无新的好友申请"

    notice_where = or_(
        SystemNotice.target_user_pk == viewer.id,
        SystemNotice.target_user_pk.is_(None),
    )
    system_unread_count = (
        db.execute(
            select(func.count())
            .select_from(SystemNotice)
            .where(
                notice_where,
                SystemNotice.is_read.is_(False),
            )
        ).scalar_one()
        or 0
    )

    latest_notice_row = db.execute(
        select(SystemNotice.content)
        .where(notice_where)
        .order_by(SystemNotice.created_at.desc(), SystemNotice.id.desc())
        .limit(1)
    ).first()
    latest_notice_text = str(latest_notice_row[0]).strip() if latest_notice_row else "暂无系统通知"

    return {
        "friend_apply": {
            "unread_count": int(pending_total),
            "latest_text": latest_pending_text,
        },
        "system_notice": {
            "unread_count": int(system_unread_count),
            "latest_text": latest_notice_text,
        },
    }


def list_conversations(
    db: Session,
    *,
    viewer_user_pk: int,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    peer_user_pk_expr = case(
        (UserMessage.sender_user_pk == viewer.id, UserMessage.receiver_user_pk),
        else_=UserMessage.sender_user_pk,
    )

    conversation_subquery = (
        select(
            peer_user_pk_expr.label("peer_user_pk"),
            func.max(UserMessage.created_at).label("last_created_at"),
            func.max(UserMessage.id).label("last_message_id"),
        )
        .where(
            or_(
                UserMessage.sender_user_pk == viewer.id,
                UserMessage.receiver_user_pk == viewer.id,
            )
        )
        .group_by(peer_user_pk_expr)
        .subquery()
    )

    total = db.execute(select(func.count()).select_from(conversation_subquery)).scalar_one() or 0

    rows = db.execute(
        select(
            conversation_subquery.c.peer_user_pk,
            conversation_subquery.c.last_created_at,
            conversation_subquery.c.last_message_id,
        )
        .order_by(
            conversation_subquery.c.last_created_at.desc(),
            conversation_subquery.c.last_message_id.desc(),
        )
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    peer_user_pks = [int(row.peer_user_pk) for row in rows if row.peer_user_pk]
    target_users = db.execute(select(User).where(User.id.in_(peer_user_pks))).scalars().all() if peer_user_pks else []
    user_map = {int(item.id): item for item in target_users}

    items: list[dict[str, Any]] = []
    for row in rows:
        peer_user_pk = int(row.peer_user_pk)
        target_user = user_map.get(peer_user_pk)

        latest_message = db.execute(
            select(UserMessage)
            .where(
                or_(
                    and_(
                        UserMessage.sender_user_pk == viewer.id,
                        UserMessage.receiver_user_pk == peer_user_pk,
                    ),
                    and_(
                        UserMessage.sender_user_pk == peer_user_pk,
                        UserMessage.receiver_user_pk == viewer.id,
                    ),
                )
            )
            .order_by(UserMessage.created_at.desc(), UserMessage.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        unread_count = (
            db.execute(
                select(func.count())
                .select_from(UserMessage)
                .where(
                    UserMessage.sender_user_pk == peer_user_pk,
                    UserMessage.receiver_user_pk == viewer.id,
                    UserMessage.is_read.is_(False),
                )
            ).scalar_one()
            or 0
        )

        display_name = str(target_user.nickname or "").strip() if target_user else ""
        industry_label = str(target_user.industry_label or "").strip() if target_user else ""
        business_user_id = str(target_user.user_id or "").strip() if target_user else ""
        avatar_url = str(target_user.avatar_url or "").strip() if target_user else ""

        items.append(
            {
                "id": str(peer_user_pk),
                "target_user_id": business_user_id,
                "name": display_name or "未命名联系人",
                "company": industry_label or "好友",
                "last_message": _build_conversation_preview(
                    content=str(latest_message.content or "").strip() if latest_message else "",
                    content_type=str(latest_message.content_type or "text").strip() if latest_message else "text",
                ),
                "time_text": _format_time_text(latest_message.created_at if latest_message else row.last_created_at),
                "unread_count": int(unread_count),
                "avatar_url": avatar_url or "/static/logo.png",
            }
        )

    return {
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def list_conversation_messages(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_id: str,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    target_user = _resolve_target_user(db=db, target_user_id=target_user_id)

    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    pair_where = or_(
        and_(
            UserMessage.sender_user_pk == viewer.id,
            UserMessage.receiver_user_pk == target_user.id,
        ),
        and_(
            UserMessage.sender_user_pk == target_user.id,
            UserMessage.receiver_user_pk == viewer.id,
        ),
    )

    total = db.execute(select(func.count()).select_from(UserMessage).where(pair_where)).scalar_one() or 0

    rows_desc = db.execute(
        select(UserMessage)
        .where(pair_where)
        .order_by(UserMessage.created_at.desc(), UserMessage.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    ).scalars().all()

    has_more = len(rows_desc) > safe_limit
    rows_desc = rows_desc[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None
    rows = list(reversed(rows_desc))

    items = [
        {
            "id": str(item.id),
            "sender_user_pk": int(item.sender_user_pk),
            "receiver_user_pk": int(item.receiver_user_pk),
            "sender_user_id": str(viewer.user_id if item.sender_user_pk == viewer.id else target_user.user_id),
            "receiver_user_id": str(viewer.user_id if item.receiver_user_pk == viewer.id else target_user.user_id),
            "content": str(item.content or "").strip(),
            "content_type": str(item.content_type or "text").strip() or "text",
            "is_read": bool(item.is_read),
            "time_text": _format_time_text(item.created_at),
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "is_self": bool(item.sender_user_pk == viewer.id),
        }
        for item in rows
    ]

    return {
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
        "peer": {
            "user_id": str(target_user.user_id or "").strip(),
            "name": str(target_user.nickname or "").strip() or "未命名联系人",
            "avatar_url": str(target_user.avatar_url or "").strip() or "/static/logo.png",
        },
        "viewer_user_id": str(viewer.user_id or "").strip(),
    }


def _assert_can_chat(db: Session, *, viewer_user_pk: int, target_user_pk: int) -> None:
    connected = (
        db.execute(
            select(func.count())
            .select_from(UserConnection)
            .where(
                or_(
                    and_(
                        UserConnection.user_pk == viewer_user_pk,
                        UserConnection.target_user_pk == target_user_pk,
                        UserConnection.is_active.is_(True),
                    ),
                    and_(
                        UserConnection.user_pk == target_user_pk,
                        UserConnection.target_user_pk == viewer_user_pk,
                        UserConnection.is_active.is_(True),
                    ),
                )
            )
        ).scalar_one()
        or 0
    )
    if connected <= 0:
        raise BusinessException(message="你们还不是好友，暂无法私信", code=4414, status_code=400)


def _track_chat_start_feedback(db: Session, *, viewer_user_pk: int, target_user_pk: int) -> None:
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    latest_impression = db.execute(
        select(NetworkRecoImpression)
        .where(
            NetworkRecoImpression.viewer_user_pk == viewer_user_pk,
            NetworkRecoImpression.target_user_pk == target_user_pk,
            NetworkRecoImpression.created_at >= since,
        )
        .order_by(NetworkRecoImpression.created_at.desc(), NetworkRecoImpression.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest_impression is None:
        return

    existing_feedback = db.execute(
        select(NetworkRecoFeedback.id)
        .where(
            NetworkRecoFeedback.viewer_user_pk == viewer_user_pk,
            NetworkRecoFeedback.target_user_pk == target_user_pk,
            NetworkRecoFeedback.event_type == "chat_start",
            NetworkRecoFeedback.created_at >= since,
        )
        .limit(1)
    ).scalar_one_or_none()
    if existing_feedback is not None:
        return

    db.add(
        NetworkRecoFeedback(
            viewer_user_pk=viewer_user_pk,
            target_user_pk=target_user_pk,
            event_type="chat_start",
            scene=str(latest_impression.scene or "discover"),
            tab_key=str(latest_impression.tab_key or "recommend"),
            request_id=latest_impression.request_id,
            ext_json=json.dumps({"source": "im_first_message"}, ensure_ascii=False),
        )
    )
    db.commit()


def send_conversation_message(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_id: str,
    content: str,
    content_type: str = "text",
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    target_user = _resolve_target_user(db=db, target_user_id=target_user_id)
    if int(viewer.id) == int(target_user.id):
        raise BusinessException(message="不能给自己发消息", code=4415, status_code=400)

    _assert_can_chat(db=db, viewer_user_pk=viewer.id, target_user_pk=target_user.id)

    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise BusinessException(message="消息内容不能为空", code=4416, status_code=400)

    normalized_content_type = str(content_type or "text").strip().lower()
    if normalized_content_type not in ALLOWED_MESSAGE_CONTENT_TYPES:
        normalized_content_type = "text"

    existing_message_count = (
        db.execute(
            select(func.count())
            .select_from(UserMessage)
            .where(
                or_(
                    and_(
                        UserMessage.sender_user_pk == viewer.id,
                        UserMessage.receiver_user_pk == target_user.id,
                    ),
                    and_(
                        UserMessage.sender_user_pk == target_user.id,
                        UserMessage.receiver_user_pk == viewer.id,
                    ),
                )
            )
        ).scalar_one()
        or 0
    )

    row = UserMessage(
        sender_user_pk=viewer.id,
        receiver_user_pk=target_user.id,
        content=normalized_content,
        content_type=normalized_content_type,
        is_read=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    if int(existing_message_count) <= 0:
        try:
            _track_chat_start_feedback(db=db, viewer_user_pk=int(viewer.id), target_user_pk=int(target_user.id))
        except Exception:  # noqa: BLE001
            db.rollback()

    return {
        "id": str(row.id),
        "sender_user_pk": int(viewer.id),
        "receiver_user_pk": int(target_user.id),
        "sender_user_id": str(viewer.user_id or "").strip(),
        "receiver_user_id": str(target_user.user_id or "").strip(),
        "content": row.content,
        "content_type": row.content_type,
        "is_read": bool(row.is_read),
        "time_text": _format_time_text(row.created_at),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "is_self": True,
    }


def mark_conversation_read(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_id: str,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    target_user = _resolve_target_user(db=db, target_user_id=target_user_id)

    read_message_ids = db.execute(
        select(UserMessage.id)
        .where(
            UserMessage.sender_user_pk == target_user.id,
            UserMessage.receiver_user_pk == viewer.id,
            UserMessage.is_read.is_(False),
        )
        .order_by(UserMessage.id.asc())
    ).scalars().all()

    stmt = (
        update(UserMessage)
        .where(
            UserMessage.sender_user_pk == target_user.id,
            UserMessage.receiver_user_pk == viewer.id,
            UserMessage.is_read.is_(False),
        )
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.commit()

    return {
        "updated": int(result.rowcount or 0),
        "read_message_ids": [str(item) for item in read_message_ids],
        "viewer_user_pk": int(viewer.id),
        "target_user_pk": int(target_user.id),
        "viewer_user_id": str(viewer.user_id or "").strip(),
        "target_user_id": str(target_user.user_id or "").strip(),
    }


def revoke_conversation_message(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_id: str,
    message_id: int,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    target_user = _resolve_target_user(db=db, target_user_id=target_user_id)
    if message_id <= 0:
        raise BusinessException(message="消息ID无效", code=4417, status_code=400)

    row = db.execute(select(UserMessage).where(UserMessage.id == int(message_id))).scalar_one_or_none()
    if row is None:
        raise BusinessException(message="消息不存在", code=4404, status_code=404)

    pair_ok = (
        (int(row.sender_user_pk) == int(viewer.id) and int(row.receiver_user_pk) == int(target_user.id))
        or (int(row.sender_user_pk) == int(target_user.id) and int(row.receiver_user_pk) == int(viewer.id))
    )
    if not pair_ok:
        raise BusinessException(message="消息不在当前会话内", code=4418, status_code=400)

    if int(row.sender_user_pk) != int(viewer.id):
        raise BusinessException(message="仅支持撤回自己发送的消息", code=4419, status_code=403)

    if str(row.content_type or "").strip().lower() == "recalled":
        return {
            "id": str(row.id),
            "sender_user_pk": int(row.sender_user_pk),
            "receiver_user_pk": int(row.receiver_user_pk),
            "sender_user_id": str(viewer.user_id or "").strip(),
            "receiver_user_id": str(target_user.user_id or "").strip(),
            "content": "[已撤回]",
            "content_type": "recalled",
            "is_read": bool(row.is_read),
            "time_text": _format_time_text(row.created_at),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "is_self": True,
            "already_recalled": True,
        }

    created_at = row.created_at.replace(tzinfo=None) if row.created_at else None
    if created_at is None:
        raise BusinessException(message="消息时间异常，无法撤回", code=4420, status_code=400)

    now = datetime.now(UTC).replace(tzinfo=None)
    elapsed = max(int((now - created_at).total_seconds()), 0)
    if elapsed > RECALL_WINDOW_SECONDS:
        raise BusinessException(message="仅支持2分钟内撤回消息", code=4421, status_code=400)

    row.content = "[已撤回]"
    row.content_type = "recalled"
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": str(row.id),
        "sender_user_pk": int(row.sender_user_pk),
        "receiver_user_pk": int(row.receiver_user_pk),
        "sender_user_id": str(viewer.user_id or "").strip(),
        "receiver_user_id": str(target_user.user_id or "").strip(),
        "content": str(row.content or ""),
        "content_type": str(row.content_type or "recalled"),
        "is_read": bool(row.is_read),
        "time_text": _format_time_text(row.created_at),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "is_self": True,
        "already_recalled": False,
    }


def list_friend_requests(
    db: Session,
    *,
    viewer_user_pk: int,
    tab: str,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    safe_tab = tab if tab in SUPPORTED_REQUEST_TABS else "pending"
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    if safe_tab == "pending":
        query_where = (
            UserFriendRequest.target_user_pk == viewer.id,
            UserFriendRequest.status == PENDING_STATUS,
        )
        join_condition = User.id == UserFriendRequest.requester_user_pk
    else:
        query_where = (UserFriendRequest.requester_user_pk == viewer.id,)
        join_condition = User.id == UserFriendRequest.target_user_pk

    total = db.execute(select(func.count()).select_from(UserFriendRequest).where(*query_where)).scalar_one() or 0

    rows = db.execute(
        select(UserFriendRequest, User)
        .outerjoin(User, join_condition)
        .where(*query_where)
        .order_by(UserFriendRequest.created_at.desc(), UserFriendRequest.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    items: list[dict[str, Any]] = []
    for idx, (request_row, related_user) in enumerate(rows):
        nickname = str(related_user.nickname or "").strip() if related_user else ""
        role_text = str(related_user.industry_label or "").strip() if related_user else ""
        avatar_url = str(related_user.avatar_url or "").strip() if related_user else ""
        business_user_id = str(related_user.user_id or "").strip() if related_user else ""

        request_message = str(request_row.request_message or "").strip()
        if not request_message:
            if safe_tab == "pending":
                request_message = "对你的资料感兴趣，希望加个好友深入交流。"
            else:
                status_text = str(request_row.status or "")
                if status_text == "accepted":
                    request_message = "对方已通过你的好友申请。"
                elif status_text == "ignored":
                    request_message = "对方暂未通过你的好友申请。"
                else:
                    request_message = "你发起了好友申请，等待对方处理。"

        items.append(
            {
                "id": str(request_row.id),
                "user_id": business_user_id,
                "name": nickname or "未命名用户",
                "role": role_text or "职场人士",
                "message": request_message,
                "time_text": _format_time_text(request_row.created_at),
                "avatar_url": avatar_url or "/static/logo.png",
                "unread": bool(safe_tab == "pending" and idx < 2),
                "can_operate": bool(safe_tab == "pending" and str(request_row.status) == PENDING_STATUS),
                "status": str(request_row.status or PENDING_STATUS),
            }
        )

    return {
        "tab": safe_tab,
        "items": items,
        "total": int(total),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }


def _ensure_connection(db: Session, *, source_user: User, target_user: User) -> None:
    row = db.execute(
        select(UserConnection)
        .where(
            UserConnection.user_pk == source_user.id,
            UserConnection.target_user_pk == target_user.id,
        )
        .order_by(UserConnection.id.desc())
        .limit(1)
    ).scalars().first()

    if row is None:
        row = UserConnection(
            user_pk=source_user.id,
            target_user_pk=target_user.id,
            target_name=target_user.nickname,
            is_active=True,
        )
    else:
        row.is_active = True
        row.target_name = target_user.nickname
    db.add(row)


def create_friend_request(
    db: Session,
    *,
    viewer_user_pk: int,
    target_business_user_id: str,
    message: str | None,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    target_user = _resolve_target_user(db=db, target_user_id=target_business_user_id)
    if int(target_user.id) == int(viewer.id):
        raise BusinessException(message="不能向自己发送好友申请", code=4412, status_code=400)

    already_connected = (
        db.execute(
            select(func.count())
            .select_from(UserConnection)
            .where(
                UserConnection.user_pk == viewer.id,
                UserConnection.target_user_pk == target_user.id,
                UserConnection.is_active.is_(True),
            )
        ).scalar_one()
        or 0
    )
    if already_connected > 0:
        raise BusinessException(message="你们已经是好友", code=4413, status_code=400)

    existing_pending = db.execute(
        select(UserFriendRequest)
        .where(
            UserFriendRequest.requester_user_pk == viewer.id,
            UserFriendRequest.target_user_pk == target_user.id,
            UserFriendRequest.status == PENDING_STATUS,
        )
        .order_by(UserFriendRequest.id.desc())
        .limit(1)
    ).scalars().first()
    if existing_pending is not None:
        return {
            "request_id": str(existing_pending.id),
            "status": str(existing_pending.status),
            "target_user_id": str(target_user.user_id or "").strip(),
            "duplicate": True,
        }

    normalized_message = str(message or "").strip()
    request_row = UserFriendRequest(
        requester_user_pk=viewer.id,
        target_user_pk=target_user.id,
        request_message=normalized_message or None,
        status=PENDING_STATUS,
    )
    db.add(request_row)
    db.commit()
    db.refresh(request_row)

    return {
        "request_id": str(request_row.id),
        "status": str(request_row.status),
        "target_user_id": str(target_user.user_id or "").strip(),
        "duplicate": False,
    }


def accept_friend_request(db: Session, *, viewer_user_pk: int, request_id: int) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)

    request_row = db.execute(select(UserFriendRequest).where(UserFriendRequest.id == int(request_id))).scalar_one_or_none()
    if request_row is None:
        raise BusinessException(message="好友申请不存在", code=4404, status_code=404)
    if request_row.target_user_pk != viewer.id:
        raise BusinessException(message="无权限处理该申请", code=4405, status_code=403)
    if str(request_row.status or "") != PENDING_STATUS:
        raise BusinessException(message="申请已处理", code=4406, status_code=400)

    requester = _ensure_user(db=db, user_pk=int(request_row.requester_user_pk))
    _ensure_connection(db=db, source_user=requester, target_user=viewer)
    _ensure_connection(db=db, source_user=viewer, target_user=requester)

    request_row.status = "accepted"
    request_row.handled_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(request_row)

    welcome_message = UserMessage(
        sender_user_pk=viewer.id,
        receiver_user_pk=requester.id,
        content="我已通过你的好友申请，期待交流。",
        content_type="text",
        is_read=False,
    )
    db.add(welcome_message)

    db.commit()
    return {
        "request_id": str(request_row.id),
        "status": "accepted",
        "target_user_id": str(requester.user_id or "").strip(),
    }


def ignore_friend_request(db: Session, *, viewer_user_pk: int, request_id: int) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)

    request_row = db.execute(select(UserFriendRequest).where(UserFriendRequest.id == int(request_id))).scalar_one_or_none()
    if request_row is None:
        raise BusinessException(message="好友申请不存在", code=4404, status_code=404)
    if request_row.target_user_pk != viewer.id:
        raise BusinessException(message="无权限处理该申请", code=4405, status_code=403)
    if str(request_row.status or "") != PENDING_STATUS:
        raise BusinessException(message="申请已处理", code=4406, status_code=400)

    request_row.status = "ignored"
    request_row.handled_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(request_row)
    db.commit()

    return {
        "request_id": str(request_row.id),
        "status": "ignored",
    }


def list_system_notices(
    db: Session,
    *,
    viewer_user_pk: int,
    cursor: str | None,
    limit: int,
) -> dict[str, Any]:
    viewer = _ensure_user(db=db, user_pk=viewer_user_pk)
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)

    query_where = or_(
        SystemNotice.target_user_pk == viewer.id,
        SystemNotice.target_user_pk.is_(None),
    )

    total = db.execute(select(func.count()).select_from(SystemNotice).where(query_where)).scalar_one() or 0

    rows = db.execute(
        select(SystemNotice)
        .where(query_where)
        .order_by(SystemNotice.created_at.desc(), SystemNotice.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    ).scalars().all()

    has_more = len(rows) > safe_limit
    rows = rows[:safe_limit]
    next_cursor = _encode_cursor(offset + safe_limit) if has_more else None

    unread_count = (
        db.execute(
            select(func.count())
            .select_from(SystemNotice)
            .where(
                query_where,
                SystemNotice.is_read.is_(False),
            )
        ).scalar_one()
        or 0
    )

    items = [
        {
            "id": str(item.id),
            "title": str(item.title or "").strip() or "系统通知",
            "content": str(item.content or "").strip(),
            "is_unread": bool(not item.is_read),
            "time_text": _format_time_text(item.created_at),
        }
        for item in rows
    ]

    return {
        "items": items,
        "total": int(total),
        "unread_count": int(unread_count),
        "has_more": bool(has_more),
        "next_cursor": next_cursor or "",
    }
