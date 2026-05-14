import logging

from django.core.mail import send_mail
from rest_framework.response import Response
from django.conf import settings

logger = logging.getLogger(__name__)


def api_response(status, message, data=None, http_status=200):
    return Response({
        "status": status,
        "message": message,
        "data": data
    }, status=http_status)


def send_welcome_email(user_email, full_name):
    subject = "Welcome to Server App!"
    message = f"Hi {full_name},\n\nThank you for signing up. Your virtual wallet has been created.\n\nBest,\nServer Team"
    try:
        logger.info("Sending welcome email to %s", user_email)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
    except Exception as exc:
        logger.warning("Failed to send welcome email to %s: %s", user_email, exc)


def send_reset_email(user_email, token):
    subject = "Password Reset Request"
    message = (
        "We received a request to reset your password.\n\n"
        f"Reset token: {token}\n\n"
        "This token is single-use only. If you did not request this, you can ignore this email."
    )
    try:
        logger.info("Sending password reset email to %s", user_email)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
    except Exception as exc:
        logger.warning("Failed to send reset email to %s: %s", user_email, exc)
