"""Email sending service using smtplib."""
from __future__ import annotations
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Tuple


def send_email(
    config: dict,
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    html_body: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Send an email using SMTP settings from config.
    Returns (success, error_message).
    """
    host = config.get("smtp_host", "").strip()
    port = int(config.get("smtp_port", 587))
    user = config.get("smtp_user", "").strip()
    password = config.get("smtp_password", "")
    use_tls = config.get("smtp_use_tls", True)

    if not host:
        return False, "Δεν έχει οριστεί SMTP server. Ρυθμίστε τον στις Παραμέτρους > Email."

    msg = MIMEMultipart("alternative" if html_body else "mixed")
    msg["From"] = user
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attachments
    for path_str in (attachments or []):
        path = Path(path_str)
        if path.exists():
            part = MIMEBase("application", "octet-stream")
            with open(path, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
            msg.attach(part)

    all_recipients = to + (cc or [])

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                if user and password:
                    server.login(user, password)
                server.sendmail(user, all_recipients, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if user and password:
                    server.login(user, password)
                server.sendmail(user, all_recipients, msg.as_string())
        return True, ""
    except smtplib.SMTPAuthenticationError:
        return False, "Λάθος username/password SMTP."
    except smtplib.SMTPConnectError:
        return False, f"Αδυναμία σύνδεσης στον {host}:{port}."
    except Exception as ex:
        return False, str(ex)


def test_smtp(config: dict) -> Tuple[bool, str]:
    """Test SMTP connectivity without sending an email."""
    host = config.get("smtp_host", "").strip()
    port = int(config.get("smtp_port", 587))
    user = config.get("smtp_user", "").strip()
    password = config.get("smtp_password", "")
    use_tls = config.get("smtp_use_tls", True)

    if not host:
        return False, "Δεν έχει οριστεί SMTP server."

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=context)
                if user and password:
                    server.login(user, password)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if user and password:
                    server.login(user, password)
        return True, ""
    except Exception as ex:
        return False, str(ex)
