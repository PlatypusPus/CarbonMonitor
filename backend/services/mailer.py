"""Send account mail through a configurable SMTP provider."""
import smtplib
import ssl
from email.message import EmailMessage
from html import escape
from pathlib import Path
from fastapi import HTTPException
from config import get_settings

HERO = Path(__file__).resolve().parent.parent / "assets" / "email-hero.jpg"

# Colors mirror frontend/tailwind.config.js.
_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title></head>
<body style="margin:0;padding:0;background:#F4F7F5;">
<div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7F5;"><tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:1px solid #DCE5DF;border-radius:14px;overflow:hidden;font-family:'Public Sans',Segoe UI,Helvetica,Arial,sans-serif;">
<tr><td style="background:#204B36;padding:24px 32px;font-size:20px;color:#FFFFFF;letter-spacing:-0.3px;"><b>Carbon</b>Trace</td></tr>
<tr><td style="background:#204B36;padding:0 32px 28px;"><img src="cid:hero" width="496" alt="Solar panels on a facility surrounded by trees" style="display:block;width:100%;max-width:496px;height:auto;border-radius:10px;border:0;"></td></tr>
<tr><td style="padding:36px 32px 8px;">
<h1 style="margin:0 0 12px;font-size:26px;line-height:1.25;color:#20372C;font-weight:600;letter-spacing:-0.5px;">{title}</h1>
<p style="margin:0 0 28px;font-size:15px;line-height:1.65;color:#52675B;">{intro}</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="border-radius:8px;background:#236F4B;">
<a href="{url}" style="display:inline-block;padding:14px 28px;font-size:15px;font-weight:600;color:#FFFFFF;text-decoration:none;border-radius:8px;">{button}</a></td></tr></table>
<p style="margin:28px 0 0;font-size:13px;line-height:1.6;color:#65766B;">{note}</p>
</td></tr>
<tr><td style="padding:20px 32px 32px;">
<p style="margin:0;padding-top:20px;border-top:1px solid #DCE5DF;font-size:12px;line-height:1.6;color:#65766B;">Button not working? Paste this link into your browser:<br><a href="{url}" style="color:#236F4B;word-break:break-all;">{url}</a></p>
</td></tr></table>
<p style="margin:20px 0 0;font-size:12px;color:#65766B;font-family:Segoe UI,Helvetica,Arial,sans-serif;">CarbonTrace · Scope 1 and 2 accounting for facility teams</p>
</td></tr></table></body></html>"""


def account_email_html(*, title: str, intro: str, button: str, url: str, note: str) -> str:
    v = {k: escape(s) for k, s in dict(title=title, intro=intro, button=button, url=url, note=note).items()}
    return _HTML.format(preheader=v["intro"], **v)


def send_account_email(recipient: str, subject: str, text: str, html: str | None = None) -> None:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")
        message.get_payload()[1].add_related(HERO.read_bytes(), "image", "jpeg", cid="<hero>")
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
