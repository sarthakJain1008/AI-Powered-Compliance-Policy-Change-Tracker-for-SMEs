"""Outgoing email helpers.

Currently supports sending password-reset emails via SMTP (plain smtplib so
there are no extra async dependencies).  SMTP errors are caught and logged
rather than propagated so a failed email never breaks the HTTP response.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_reset_html(username: str, reset_link: str) -> str:
    """Return a minimal but clean HTML body for the password-reset email."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Password Reset — {settings.APP_NAME}</title>
</head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:40px 0;">
  <table width="600" cellpadding="0" cellspacing="0"
         style="margin:auto;background:#ffffff;border-radius:8px;overflow:hidden;">
    <tr>
      <td style="background:#1a56db;padding:24px 32px;">
        <h1 style="color:#ffffff;margin:0;font-size:22px;">{settings.APP_NAME}</h1>
      </td>
    </tr>
    <tr>
      <td style="padding:32px;">
        <p style="margin:0 0 16px;">Hi <strong>{username}</strong>,</p>
        <p style="margin:0 0 24px;">
          We received a request to reset your password.  Click the button below
          to choose a new one.  This link expires in
          <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours</strong>.
        </p>
        <a href="{reset_link}"
           style="display:inline-block;padding:12px 28px;background:#1a56db;
                  color:#ffffff;text-decoration:none;border-radius:6px;
                  font-weight:bold;">
          Reset Password
        </a>
        <p style="margin:24px 0 0;font-size:13px;color:#666;">
          If you did not request a password reset, you can safely ignore this
          email — your password will not change.
        </p>
        <hr style="margin:32px 0;border:none;border-top:1px solid #eeeeee;" />
        <p style="font-size:12px;color:#999;margin:0;">
          Or copy and paste this link into your browser:<br />
          <a href="{reset_link}" style="color:#1a56db;">{reset_link}</a>
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_reset_password_email(
    email_to: str,
    token: str,
    username: str,
) -> None:
    """Send a password-reset email to *email_to*.

    Args:
        email_to: Recipient's email address.
        token:    The signed password-reset token (embedded in the link).
        username: Display name shown in the email greeting.

    The function is ``async`` for interface consistency; the underlying SMTP
    call is synchronous but fast enough for this use-case.  SMTP errors are
    swallowed so callers never see an exception from here.
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reset your {settings.APP_NAME} password"
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    msg["To"] = email_to

    # Attach both a plain-text fallback and the rich HTML version
    plain_text = (
        f"Hi {username},\n\n"
        f"Reset your password here (expires in "
        f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours):\n"
        f"{reset_link}\n\n"
        f"If you did not request this, ignore this email.\n"
    )
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(_build_reset_html(username, reset_link), "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()          # Upgrade to TLS before sending credentials
            server.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, msg.as_string())
        logger.info("Password-reset email sent to %s", email_to)
    except smtplib.SMTPException as exc:
        # Log the error but do not raise — the HTTP layer should still return 200
        logger.error("Failed to send password-reset email to %s: %s", email_to, exc)
    except OSError as exc:
        # Network-level errors (e.g. SMTP server unreachable in dev)
        logger.warning("SMTP connection error for %s: %s", email_to, exc)
