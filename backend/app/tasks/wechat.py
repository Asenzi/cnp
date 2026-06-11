"""WeChat notification tasks."""

from app.core.celery_app import celery_app
from app.core.logger import logger


@celery_app.task(
    name="app.tasks.wechat.send_template_message",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_template_message(
    self,
    user_id: int,
    template_id: str,
    data: dict,
    page: str | None = None,
) -> dict[str, str]:
    """Send WeChat Mini Program template message.

    Args:
        user_id: Target user ID
        template_id: WeChat template message ID
        data: Template data (key-value pairs)
        page: Optional page path to navigate

    Returns:
        dict with status and message
    """
    try:
        logger.info(f"Sending WeChat template message to user {user_id}")

        # TODO: Implement actual WeChat template message sending
        # 1. Get user's openid from database
        # 2. Call WeChat API to send template message
        # Example:
        # from app.crud import get_user_by_id
        # from app.core.database import SessionLocal
        #
        # db = SessionLocal()
        # try:
        #     user = get_user_by_id(db, user_id)
        #     if not user or not user.openid:
        #         raise ValueError("User openid not found")
        #
        #     # Call WeChat API
        #     wechat_client.send_template_message(
        #         openid=user.openid,
        #         template_id=template_id,
        #         data=data,
        #         page=page
        #     )
        # finally:
        #     db.close()

        return {
            "status": "success",
            "message": f"Template message sent to user {user_id}",
        }
    except Exception as exc:
        logger.error(f"Failed to send template message to user {user_id}: {exc}")
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.wechat.send_verification_result",
    bind=True,
    max_retries=3,
)
def send_verification_result(
    self,
    user_id: int,
    verification_type: str,
    approved: bool,
    reason: str | None = None,
) -> dict[str, str]:
    """Send verification result notification.

    Args:
        user_id: Target user ID
        verification_type: Type of verification (realname/business_card/enterprise)
        approved: Whether approved
        reason: Rejection reason if not approved

    Returns:
        dict with status and message
    """
    try:
        logger.info(
            f"Sending verification result to user {user_id}: "
            f"{verification_type} - {'approved' if approved else 'rejected'}"
        )

        status_text = "审核通过" if approved else "审核未通过"
        result_text = "恭喜！您的认证已通过审核。" if approved else f"很抱歉，您的认证未通过。{reason or ''}"

        # TODO: Replace with actual template message
        template_data = {
            "thing1": {"value": f"{verification_type}认证"},
            "thing2": {"value": status_text},
            "thing3": {"value": result_text[:20]},
        }

        return send_template_message(
            user_id=user_id,
            template_id="VERIFICATION_RESULT_TEMPLATE",
            data=template_data,
            page="/pages/me/auth/index",
        )

    except Exception as exc:
        logger.error(f"Failed to send verification result to user {user_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.wechat.send_friend_request_notification",
)
def send_friend_request_notification(
    from_user_id: int,
    to_user_id: int,
    from_username: str,
    message: str | None = None,
) -> dict[str, str]:
    """Send friend request notification.

    Args:
        from_user_id: Sender user ID
        to_user_id: Receiver user ID
        from_username: Sender username
        message: Optional message

    Returns:
        dict with status and message
    """
    try:
        logger.info(f"Sending friend request notification from {from_user_id} to {to_user_id}")

        template_data = {
            "thing1": {"value": from_username},
            "thing2": {"value": message[:20] if message else "想和你成为好友"},
        }

        return send_template_message(
            user_id=to_user_id,
            template_id="FRIEND_REQUEST_TEMPLATE",
            data=template_data,
            page="/pages/im/friend-requests/index",
        )

    except Exception as exc:
        logger.error(
            f"Failed to send friend request notification "
            f"from {from_user_id} to {to_user_id}: {exc}"
        )
        raise


@celery_app.task(
    name="app.tasks.wechat.send_friend_accepted_notification",
)
def send_friend_accepted_notification(
    from_user_id: int,
    to_user_id: int,
    from_username: str,
) -> dict[str, str]:
    """Send friend request accepted notification.

    Args:
        from_user_id: Who accepted the request
        to_user_id: Original requester
        from_username: Who accepted

    Returns:
        dict with status and message
    """
    try:
        logger.info(f"Sending friend accepted notification from {from_user_id} to {to_user_id}")

        template_data = {
            "thing1": {"value": from_username},
            "thing2": {"value": "已同意你的好友申请"},
        }

        return send_template_message(
            user_id=to_user_id,
            template_id="FRIEND_ACCEPTED_TEMPLATE",
            data=template_data,
            page="/pages/im/chat/index",
        )

    except Exception as exc:
        logger.error(
            f"Failed to send friend accepted notification "
            f"from {from_user_id} to {to_user_id}: {exc}"
        )
        raise


@celery_app.task(
    name="app.tasks.wechat.send_circle_join_result",
)
def send_circle_join_result(
    user_id: int,
    circle_name: str,
    circle_code: str,
    approved: bool,
    reason: str | None = None,
) -> dict[str, str]:
    """Send circle join request result notification.

    Args:
        user_id: Target user ID
        circle_name: Circle name
        circle_code: Circle code
        approved: Whether approved
        reason: Rejection reason if not approved

    Returns:
        dict with status and message
    """
    try:
        logger.info(
            f"Sending circle join result to user {user_id}: "
            f"{circle_name} - {'approved' if approved else 'rejected'}"
        )

        status_text = "申请通过" if approved else "申请未通过"
        result_text = "欢迎加入圈子！" if approved else f"{reason or '暂时无法通过您的申请'}"

        template_data = {
            "thing1": {"value": circle_name[:20]},
            "thing2": {"value": status_text},
            "thing3": {"value": result_text[:20]},
        }

        page = f"/pages/circles/circle/index?code={circle_code}" if approved else "/pages/circles/index"

        return send_template_message(
            user_id=user_id,
            template_id="CIRCLE_JOIN_RESULT_TEMPLATE",
            data=template_data,
            page=page,
        )

    except Exception as exc:
        logger.error(f"Failed to send circle join result to user {user_id}: {exc}")
        raise
