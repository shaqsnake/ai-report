"""Email sending with zip attachment support."""

import os
import smtplib
import zipfile
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def create_zip(screenshot_paths: list[str], zip_path: str) -> str:
    """Package screenshot files into a zip archive.

    Returns the zip file path.
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in screenshot_paths:
            zf.write(path, os.path.basename(path))
    return zip_path


def send_email(
    smtp_host: str,
    smtp_port: int,
    use_ssl: bool,
    sender: str,
    auth_code: str,
    recipients: list[str],
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> None:
    """Send an email via SMTP with an optional attachment."""
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender, auth_code)
            server.sendmail(sender, recipients, msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, auth_code)
            server.sendmail(sender, recipients, msg.as_string())


def send_audit_report(
    config: dict,
    user_name: str,
    quarter_label: str,
    screenshot_paths: list[str],
    output_dir: str,
) -> None:
    """High-level convenience: zip screenshots and send via email."""
    email_cfg = config.get("email", {})
    if not email_cfg.get("enabled", False):
        return

    sender = email_cfg.get("sender")
    auth_code = email_cfg.get("auth_code")
    if not sender or not auth_code:
        raise ValueError("SMTP_SENDER and SMTP_AUTH_CODE must be set for email sending")

    zip_path = os.path.join(output_dir, f"{user_name}-{quarter_label}.zip")
    create_zip(screenshot_paths, zip_path)

    subject = email_cfg.get("subject_template", "股票对账报告 - {quarter} - {user}").format(
        quarter=quarter_label, user=user_name
    )
    body = f"{user_name} 的 {quarter_label} 季度股票对账报告，请查收附件。"

    send_email(
        smtp_host=email_cfg["smtp_host"],
        smtp_port=email_cfg["smtp_port"],
        use_ssl=email_cfg.get("use_ssl", True),
        sender=sender,
        auth_code=auth_code,
        recipients=email_cfg["recipients"],
        subject=subject,
        body=body,
        attachment_path=zip_path,
    )
