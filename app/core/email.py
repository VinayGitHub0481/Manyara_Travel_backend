import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_password_reset_email(
    recipient_email: str,
    otp: str,
) -> None:
    message = EmailMessage()

    message["Subject"] = "Manyara Prive Vacations - Password Reset Verification Code"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient_email

    message.set_content(
        f"""
Hello,

We received a request to reset your Manyara Prive Vacations account password.

Your password reset verification code is:

{otp}

This verification code is valid for 2 minutes.

If you did not request a password reset, please ignore this email.

For security reasons, do not share this code with anyone.

Regards,
Manyara Prive Vacations Team
""".strip()
    )

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
    ) as server:

        if settings.SMTP_USE_TLS:
            server.starttls()

        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )

        server.send_message(message)