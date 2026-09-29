"""Send account mail through a configurable SMTP provider."""
import smtplib
import ssl
from email.message import EmailMessage
from fastapi import HTTPException
from config import get_settings


def send_account_email(recipient: str, subject: str, text: str) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    try:
        smtp_type = smtplib.SMTP_SSL if settings.smtp_ssl else smtplib.SMTP
        kwargs = {"context": ssl.create_default_context()} if settings.smtp_ssl else {}
        with smtp_type(settings.smtp_host, settings.smtp_port, timeout=10, **kwargs) as smtp:
            if settings.smtp_starttls and not settings.smtp_ssl:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise HTTPException(503, "Email delivery is unavailable. Please try again later.") from None
