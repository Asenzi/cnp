"""Email notification tasks."""

from app.core.celery_app import celery_app
from app.core.logger import logger


@celery_app.task(name="app.tasks.email.send_verification_email")
def send_verification_email(email: str, verification_code: str) -> dict[str, str]:
    """Send verification email (example task).

    Args:
        email: User email address
        verification_code: Verification code to send

    Returns:
        dict with status and message
    """
    try:
        # TODO: Implement actual email sending logic
        logger.info(f"Sending verification email to {email} with code {verification_code}")

        # Simulate email sending
        # In production, use services like:
        # - SMTP (smtplib)
        # - AWS SES
        # - SendGrid
        # - Mailgun

        return {
            "status": "success",
            "message": f"Email sent to {email}",
        }
    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {exc}")
        raise


@celery_app.task(name="app.tasks.email.send_welcome_email")
def send_welcome_email(email: str, username: str) -> dict[str, str]:
    """Send welcome email to new user.

    Args:
        email: User email address
        username: User's display name

    Returns:
        dict with status and message
    """
    try:
        logger.info(f"Sending welcome email to {email} (username: {username})")

        # TODO: Implement actual email sending logic

        return {
            "status": "success",
            "message": f"Welcome email sent to {email}",
        }
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {email}: {exc}")
        raise
