"""Email notification sink (file-based delivery).

Section 8.3 — NOTIFY-1..3: invoice status change and manual resend notifications
are written as HTML files to uploads/email_log/ rather than sent via SMTP.
This keeps the implementation self-contained (no external mail server required)
while providing a full audit trail through the email_notifications table.

send_invoice_notification() is non-blocking: exceptions are caught, logged, and
the caller always gets a return value — the invoice DB operation is never rolled
back due to a notification failure (NOTIFY-3).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Badge inline styles per Section 8.3.2 spec.
_STATUS_BADGE_COLORS: dict[str, str] = {
    "Pending": "#f59e0b",
    "Paid": "#10b981",
    "Waived": "#6b7280",
}

_EMAIL_LOG_DIR = os.path.join("uploads", "email_log")


def _build_html(
    patient_name: str,
    invoice_id: int,
    line_items: list[dict],
    total_cents: int,
    status: str,
) -> str:
    """Build the HTML body for the notification email."""
    badge_color = _STATUS_BADGE_COLORS.get(status, "#6b7280")
    total_dollars = f"${total_cents / 100:,.2f}"

    rows_html = "".join(
        f"<tr><td style='padding:8px;border:1px solid #e5e7eb;'>{item.get('description','')}</td>"
        f"<td style='padding:8px;border:1px solid #e5e7eb;text-align:right;'>"
        f"${item.get('amount_cents', 0) / 100:,.2f}</td></tr>"
        for item in line_items
    )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Invoice #{invoice_id} — Green Valley Hospital</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:40px auto;color:#1f2937;">
  <h2 style="color:#1e3a5f;">Green Valley Hospital</h2>
  <h3>Invoice Notification</h3>
  <p>Dear <strong>{patient_name}</strong>,</p>
  <p>This is a notification regarding <strong>Invoice #{invoice_id}</strong>.</p>

  <table style="width:100%;border-collapse:collapse;margin:20px 0;">
    <thead>
      <tr style="background:#f3f4f6;">
        <th style="padding:10px;border:1px solid #e5e7eb;text-align:left;">Description</th>
        <th style="padding:10px;border:1px solid #e5e7eb;text-align:right;">Amount</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr style="background:#f3f4f6;font-weight:bold;">
        <td style="padding:10px;border:1px solid #e5e7eb;">Total</td>
        <td style="padding:10px;border:1px solid #e5e7eb;text-align:right;">{total_dollars}</td>
      </tr>
    </tfoot>
  </table>

  <p>
    Status:
    <span style="display:inline-block;padding:4px 12px;border-radius:12px;
                 background:{badge_color};color:#fff;font-weight:bold;">
      {status}
    </span>
  </p>

  <p style="color:#6b7280;font-size:12px;margin-top:40px;">
    Green Valley Hospital — 123 Green Valley Road, Springfield<br>
    This is an automated notification. Please do not reply to this message.
  </p>
</body>
</html>"""


def send_invoice_notification(
    db: Session,
    *,
    patient_id: int,
    invoice_id: int,
    patient_name: str,
    patient_email: str,
    recipient_user_id: int,
    line_items: list[dict],
    total_cents: int,
    status: str,
    trigger_event: str = "invoice_status_change",
) -> dict:
    """Write the HTML notification file and insert an EmailNotification row.

    Returns a dict with the notification_id, status, and sent_at regardless of
    success or failure (non-blocking per NOTIFY-3).  On file-write failure the
    EmailNotification row is inserted with status='Failed'.
    """
    # Inline import avoids circular dependency with models.
    from app.models import EmailNotification

    now = datetime.now(timezone.utc)
    sent_at = now.isoformat()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp_str}_{patient_id}_invoice_{invoice_id}.html"
    filepath = os.path.join(_EMAIL_LOG_DIR, filename)

    subject = f"Invoice #{invoice_id} Status Update — Green Valley Hospital"
    body_html = _build_html(patient_name, invoice_id, line_items, total_cents, status)

    file_status = "Sent"
    try:
        os.makedirs(_EMAIL_LOG_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(body_html)
    except Exception as exc:  # noqa: BLE001
        logger.error("email_sink: failed to write notification file %s: %s", filepath, exc)
        file_status = "Failed"

    notif: EmailNotification | None = None
    try:
        notif = EmailNotification(
            recipient_user_id=recipient_user_id,
            subject=subject,
            body_html=body_html,
            sent_at=sent_at,
            trigger_event=trigger_event,
            related_invoice_id=invoice_id,
            status=file_status,
        )
        db.add(notif)
        db.flush()  # gets the notification_id before commit; caller does db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("email_sink: failed to insert EmailNotification row: %s", exc)
        db.rollback()
        return {"notification_id": None, "status": "Failed", "sent_at": sent_at}

    return {
        "notification_id": notif.notification_id,
        "status": file_status,
        "sent_at": sent_at,
    }
