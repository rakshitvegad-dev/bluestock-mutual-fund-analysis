"""
Bluestock Mutual Fund Analytics
Bonus B5 - Weekly HTML Email Sender
"""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

REPORT_PATH = (
    BASE_DIR
    / "reports"
    / "weekly_performance_report.html"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

SMTP_SERVER = os.getenv(
    "SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "465"
    )
)


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

required = {
    "EMAIL_SENDER": EMAIL_SENDER,
    "EMAIL_RECIPIENT": EMAIL_RECIPIENT,
    "EMAIL_APP_PASSWORD": EMAIL_APP_PASSWORD,
}

missing = [
    key
    for key, value in required.items()
    if not value
]

if missing:

    raise RuntimeError(
        "Missing environment variables: "
        + ", ".join(missing)
    )


if not REPORT_PATH.exists():

    raise FileNotFoundError(
        f"HTML report not found:\n{REPORT_PATH}"
    )


# ============================================================
# READ HTML REPORT
# ============================================================

html_content = REPORT_PATH.read_text(
    encoding="utf-8"
)


# ============================================================
# CREATE EMAIL
# ============================================================

message = EmailMessage()

message["Subject"] = (
    "Bluestock Mutual Fund - Weekly Performance Report"
)

message["From"] = EMAIL_SENDER

message["To"] = EMAIL_RECIPIENT

message.set_content(
    """
Bluestock Mutual Fund Weekly Performance Report

Please view this email in an HTML-compatible email client.
"""
)

message.add_alternative(
    html_content,
    subtype="html"
)


# ============================================================
# SEND EMAIL
# ============================================================

print("=" * 70)
print("BLUESTOCK WEEKLY REPORT EMAIL")
print("=" * 70)

print(
    f"\nSender: {EMAIL_SENDER}"
)

print(
    f"Recipient: {EMAIL_RECIPIENT}"
)

print(
    f"Report: {REPORT_PATH}"
)

print(
    "\nConnecting to SMTP server..."
)


try:

    with smtplib.SMTP_SSL(
        SMTP_SERVER,
        SMTP_PORT
    ) as server:

        server.login(
            EMAIL_SENDER,
            EMAIL_APP_PASSWORD
        )

        server.send_message(
            message
        )

    print(
        "\nEMAIL SENT SUCCESSFULLY"
    )

    print(
        "Weekly performance report delivered."
    )


except smtplib.SMTPAuthenticationError:

    print(
        "\nERROR: SMTP authentication failed."
    )

    print(
        "Check your Gmail App Password."
    )

    raise


except Exception as exc:

    print(
        f"\nERROR sending email: {exc}"
    )

    raise