"""Notification tasks."""

from app.core.celery_app import celery_app
from app.core.logger import logger


@celery_app.task(name="app.tasks.notification.send_push_notification")
def send_push_notification(
    user_id: int,
    title: str,
    message: str,
    data: dict | None = None,
) -> dict[str, str]:
    """Send push notification to user.

    Args:
        user_id: Target user ID
        title: Notification title
        message: Notification message
        data: Optional additional data

    Returns:
        dict with status and message
    """
    try:
        logger.info(
            f"Sending push notification to user {user_id}: {title} - {message}"
        )

        # TODO: Implement actual push notification logic
        # - WeChat Mini Program template message
        # - APNs (Apple Push Notification service)
        # - FCM (Firebase Cloud Messaging)
        # - JPush

        return {
            "status": "success",
            "message": f"Notification sent to user {user_id}",
        }
    except Exception as exc:
        logger.error(f"Failed to send notification to user {user_id}: {exc}")
        raise


@celery_app.task(name="app.tasks.notification.send_system_notification")
def send_system_notification(
    user_ids: list[int],
    title: str,
    message: str,
) -> dict[str, int]:
    """Send system notification to multiple users.

    Args:
        user_ids: List of target user IDs
        title: Notification title
        message: Notification message

    Returns:
        dict with success count and failed count
    """
    success_count = 0
    failed_count = 0

    for user_id in user_ids:
        try:
            logger.info(f"Sending system notification to user {user_id}")

            # TODO: Implement actual notification logic

            success_count += 1
        except Exception as exc:
            logger.error(f"Failed to send notification to user {user_id}: {exc}")
            failed_count += 1

    return {
        "success": success_count,
        "failed": failed_count,
    }
