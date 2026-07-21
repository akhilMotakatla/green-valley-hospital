"""REQ-06 — Advanced Analytics & Reporting Dashboard (Admin only).

All aggregations are computed server-side via raw SQL aggregate queries (no ORM
query builder) per docs/technical-design.md §4.3.4.  Raw rows are never sent
to the frontend.

Endpoints:
  GET  /api/admin/analytics/appointments       — appointment volume by period
  GET  /api/admin/analytics/no-show-rate       — no-show rate by period
  GET  /api/admin/analytics/revenue            — revenue invoiced vs collected by month
  GET  /api/admin/analytics/department-volume  — appointment count per department
  GET  /api/admin/analytics/patient-acquisition — new patient registrations by month
  GET  /api/admin/analytics/export-csv         — CSV export for any metric
"""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import User

router = APIRouter(tags=["analytics"])

# All analytics endpoints require Admin role.
_admin = Depends(require_role("Admin"))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_date_range() -> tuple[str, str]:
    """Last 30 days, matching the frontend's default preset."""
    today = date.today()
    return (today - timedelta(days=30)).isoformat(), today.isoformat()


def _resolve_dates(from_date: str | None, to_date: str | None) -> tuple[str, str]:
    if not from_date or not to_date:
        return _default_date_range()
    try:
        fd = date.fromisoformat(from_date)
        td = date.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if fd > td:
        raise HTTPException(
            status_code=400,
            detail="from_date must be before or equal to to_date.",
        )
    return from_date, to_date


def _granularity_fmt(granularity: str) -> str:
    """Return the SQLite strftime format string for the requested granularity."""
    if granularity == "day":
        return "%Y-%m-%d"
    if granularity == "week":
        return "%Y-%W"
    return "%Y-%m"  # month (default)


# ---------------------------------------------------------------------------
# Endpoint 1 — GET /api/admin/analytics/appointments
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/appointments")
def get_appointment_analytics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    granularity: str = Query("month"),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """Appointment volume (COUNT) grouped by period with per-status breakdown.

    Returns: {series: [{period, count, completed, cancelled, no_show, scheduled}], total}
    """
    from_date, to_date = _resolve_dates(from_date, to_date)
    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=400,
            detail="granularity must be one of: day, week, month.",
        )

    fmt = _granularity_fmt(granularity)

    rows = db.execute(
        text("""
            SELECT
                strftime(:fmt, scheduled_at) AS period,
                COUNT(*) AS cnt,
                SUM(CASE WHEN status = 'Completed'  THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN status = 'Cancelled'  THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN status = 'NoShow'     THEN 1 ELSE 0 END) AS no_show,
                SUM(CASE WHEN status = 'Scheduled'  THEN 1 ELSE 0 END) AS scheduled
            FROM appointments
            WHERE date(scheduled_at) BETWEEN :fd AND :td
            GROUP BY period
            ORDER BY period ASC
        """),
        {"fmt": fmt, "fd": from_date, "td": to_date},
    ).fetchall()

    series = [
        {
            "period":    r[0],
            "count":     r[1],
            "completed": r[2],
            "cancelled": r[3],
            "no_show":   r[4],
            "scheduled": r[5],
        }
        for r in rows
    ]
    total = sum(r["count"] for r in series)

    return {"series": series, "total": total}


# ---------------------------------------------------------------------------
# Endpoint 2 — GET /api/admin/analytics/no-show-rate
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/no-show-rate")
def get_no_show_rate(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    granularity: str = Query("month"),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """No-show rate by period, excluding Cancelled appointments from the denominator.

    Returns: {series: [{period, total, cancelled, eligible, no_shows, rate}], overall_rate}
    eligible = total - cancelled
    rate = no_shows / eligible, rounded to 4 decimal places (0.0 when eligible is 0).
    """
    from_date, to_date = _resolve_dates(from_date, to_date)
    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=400,
            detail="granularity must be one of: day, week, month.",
        )

    fmt = _granularity_fmt(granularity)

    rows = db.execute(
        text("""
            SELECT
                strftime(:fmt, scheduled_at) AS period,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                SUM(CASE WHEN status = 'NoShow'    THEN 1 ELSE 0 END) AS no_shows
            FROM appointments
            WHERE date(scheduled_at) BETWEEN :fd AND :td
            GROUP BY period
            ORDER BY period ASC
        """),
        {"fmt": fmt, "fd": from_date, "td": to_date},
    ).fetchall()

    series = []
    grand_eligible = 0
    grand_no_shows = 0

    for r in rows:
        total_val    = r[1]
        cancelled    = r[2]
        no_shows_val = r[3]
        eligible     = total_val - cancelled
        rate = round(no_shows_val / eligible, 4) if eligible > 0 else 0.0
        series.append(
            {
                "period":   r[0],
                "total":    total_val,
                "cancelled": cancelled,
                "eligible": eligible,
                "no_shows": no_shows_val,
                "rate":     rate,
            }
        )
        grand_eligible  += eligible
        grand_no_shows  += no_shows_val

    overall_rate = round(grand_no_shows / grand_eligible, 4) if grand_eligible > 0 else 0.0

    return {"series": series, "overall_rate": overall_rate}


# ---------------------------------------------------------------------------
# Endpoint 3 — GET /api/admin/analytics/revenue
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/revenue")
def get_revenue_analytics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """Revenue summary by month.

    invoiced  = SUM(total_amount_cents) for all invoices created in the period,
                grouped by month of created_at.
    collected = SUM(total_amount_cents) for Paid invoices; uses paid_at month
                where paid_at IS NOT NULL (accurate), falls back to created_at
                month for rows where paid_at IS NULL (approximation per OI-7).

    Dollar values (not cents) are returned: cents / 100.0.

    Returns: {series: [{month, invoiced, collected, outstanding}],
              total_invoiced, total_collected, total_outstanding}
    """
    from_date, to_date = _resolve_dates(from_date, to_date)

    # --- Invoiced: all invoices created in the date range ---
    invoiced_rows = db.execute(
        text("""
            SELECT
                strftime('%Y-%m', created_at) AS month,
                SUM(total_amount_cents) AS cents
            FROM invoices
            WHERE date(created_at) BETWEEN :fd AND :td
            GROUP BY month
            ORDER BY month ASC
        """),
        {"fd": from_date, "td": to_date},
    ).fetchall()

    # --- Collected (accurate path): Paid invoices with a paid_at timestamp ---
    col_paid_at_rows = db.execute(
        text("""
            SELECT
                strftime('%Y-%m', paid_at) AS month,
                SUM(total_amount_cents) AS cents
            FROM invoices
            WHERE status = 'Paid'
              AND paid_at IS NOT NULL
              AND date(paid_at) BETWEEN :fd AND :td
            GROUP BY month
            ORDER BY month ASC
        """),
        {"fd": from_date, "td": to_date},
    ).fetchall()

    # --- Collected (fallback): Paid invoices whose paid_at is NULL ---
    col_fallback_rows = db.execute(
        text("""
            SELECT
                strftime('%Y-%m', created_at) AS month,
                SUM(total_amount_cents) AS cents
            FROM invoices
            WHERE status = 'Paid'
              AND paid_at IS NULL
              AND date(created_at) BETWEEN :fd AND :td
            GROUP BY month
            ORDER BY month ASC
        """),
        {"fd": from_date, "td": to_date},
    ).fetchall()

    # Merge into per-month dicts
    invoiced_by: dict[str, int] = {r[0]: int(r[1] or 0) for r in invoiced_rows}

    collected_by: dict[str, int] = {}
    for r in col_paid_at_rows:
        collected_by[r[0]] = collected_by.get(r[0], 0) + int(r[1] or 0)
    for r in col_fallback_rows:
        collected_by[r[0]] = collected_by.get(r[0], 0) + int(r[1] or 0)

    all_months = sorted(set(invoiced_by) | set(collected_by))

    series = []
    for month in all_months:
        inv = invoiced_by.get(month, 0)
        col = collected_by.get(month, 0)
        out = max(0, inv - col)
        series.append(
            {
                "month": month,
                "invoiced": round(inv / 100.0, 2),
                "collected": round(col / 100.0, 2),
                "outstanding": round(out / 100.0, 2),
            }
        )

    total_invoiced = round(sum(r["invoiced"] for r in series), 2)
    total_collected = round(sum(r["collected"] for r in series), 2)
    total_outstanding = round(max(0.0, total_invoiced - total_collected), 2)

    return {
        "series": series,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    }


# ---------------------------------------------------------------------------
# Endpoint 4 — GET /api/admin/analytics/department-volume
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/department-volume")
def get_department_volume(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """Appointment count per department, sorted descending.

    Returns: {departments: [{department_id, name, count}]}
    """
    from_date, to_date = _resolve_dates(from_date, to_date)

    rows = db.execute(
        text("""
            SELECT
                d.department_id,
                d.name,
                COUNT(a.appointment_id) AS cnt
            FROM appointments a
            JOIN doctors doc ON a.doctor_id = doc.doctor_id
            JOIN departments d ON doc.department_id = d.department_id
            WHERE date(a.scheduled_at) BETWEEN :fd AND :td
            GROUP BY d.department_id, d.name
            ORDER BY cnt DESC
        """),
        {"fd": from_date, "td": to_date},
    ).fetchall()

    departments = [
        {"department_id": r[0], "name": r[1], "count": r[2]}
        for r in rows
    ]

    return {"departments": departments}


# ---------------------------------------------------------------------------
# Endpoint 5 — GET /api/admin/analytics/patient-acquisition
# ---------------------------------------------------------------------------

@router.get("/admin/analytics/patient-acquisition")
def get_patient_acquisition(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """New patient registrations grouped by month of users.created_at.

    Returns: {series: [{month, new_patients}], total_new}
    """
    from_date, to_date = _resolve_dates(from_date, to_date)

    rows = db.execute(
        text("""
            SELECT
                strftime('%Y-%m', u.created_at) AS month,
                COUNT(*) AS new_patients
            FROM users u
            WHERE u.role = 'Patient'
              AND date(u.created_at) BETWEEN :fd AND :td
            GROUP BY month
            ORDER BY month ASC
        """),
        {"fd": from_date, "td": to_date},
    ).fetchall()

    series = [{"month": r[0], "new_patients": r[1]} for r in rows]
    total_new = sum(r["new_patients"] for r in series)

    return {"series": series, "total_new": total_new}


# ---------------------------------------------------------------------------
# Endpoint 6 — GET /api/admin/analytics/export-csv
# ---------------------------------------------------------------------------

_VALID_METRICS = frozenset(
    ("appointments", "no_show_rate", "revenue", "department_volume", "patient_acquisition")
)


@router.get("/admin/analytics/export-csv")
def export_csv(
    metric: str = Query(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    granularity: str = Query("month"),
    current_user: User = _admin,
    db: Session = Depends(get_db),
):
    """Export the requested metric as a CSV file.

    metric must be one of: appointments, no_show_rate, revenue,
    department_volume, patient_acquisition.

    Returns: text/csv StreamingResponse with Content-Disposition: attachment.
    """
    if metric not in _VALID_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"metric must be one of: {', '.join(sorted(_VALID_METRICS))}.",
        )

    from_date, to_date = _resolve_dates(from_date, to_date)

    if granularity not in ("day", "week", "month"):
        granularity = "month"

    # ------------------------------------------------------------------
    # Build headers + rows for the requested metric
    # ------------------------------------------------------------------
    if metric == "appointments":
        fmt = _granularity_fmt(granularity)
        rows = db.execute(
            text("""
                SELECT
                    strftime(:fmt, scheduled_at) AS period,
                    COUNT(*) AS cnt,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
                    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'NoShow'    THEN 1 ELSE 0 END) AS no_show,
                    SUM(CASE WHEN status = 'Scheduled' THEN 1 ELSE 0 END) AS scheduled
                FROM appointments
                WHERE date(scheduled_at) BETWEEN :fd AND :td
                GROUP BY period ORDER BY period ASC
            """),
            {"fmt": fmt, "fd": from_date, "td": to_date},
        ).fetchall()
        headers = ["period", "count", "completed", "cancelled", "no_show", "scheduled"]
        csv_rows = [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows]

    elif metric == "no_show_rate":
        fmt = _granularity_fmt(granularity)
        rows = db.execute(
            text("""
                SELECT
                    strftime(:fmt, scheduled_at) AS period,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'NoShow'    THEN 1 ELSE 0 END) AS no_shows
                FROM appointments
                WHERE date(scheduled_at) BETWEEN :fd AND :td
                GROUP BY period ORDER BY period ASC
            """),
            {"fmt": fmt, "fd": from_date, "td": to_date},
        ).fetchall()
        headers = ["period", "total", "cancelled", "eligible", "no_shows", "rate"]
        csv_rows = []
        for r in rows:
            total_val, cancelled, no_shows = r[1], r[2], r[3]
            eligible = total_val - cancelled
            rate = round(no_shows / eligible, 4) if eligible > 0 else 0.0
            csv_rows.append([r[0], total_val, cancelled, eligible, no_shows, rate])

    elif metric == "revenue":
        inv_rows = db.execute(
            text("""
                SELECT strftime('%Y-%m', created_at), SUM(total_amount_cents)
                FROM invoices WHERE date(created_at) BETWEEN :fd AND :td
                GROUP BY 1 ORDER BY 1 ASC
            """),
            {"fd": from_date, "td": to_date},
        ).fetchall()
        col_pa = db.execute(
            text("""
                SELECT strftime('%Y-%m', paid_at), SUM(total_amount_cents)
                FROM invoices WHERE status='Paid' AND paid_at IS NOT NULL
                  AND date(paid_at) BETWEEN :fd AND :td
                GROUP BY 1 ORDER BY 1 ASC
            """),
            {"fd": from_date, "td": to_date},
        ).fetchall()
        col_fb = db.execute(
            text("""
                SELECT strftime('%Y-%m', created_at), SUM(total_amount_cents)
                FROM invoices WHERE status='Paid' AND paid_at IS NULL
                  AND date(created_at) BETWEEN :fd AND :td
                GROUP BY 1 ORDER BY 1 ASC
            """),
            {"fd": from_date, "td": to_date},
        ).fetchall()
        inv_by: dict[str, int] = {r[0]: int(r[1] or 0) for r in inv_rows}
        col_by: dict[str, int] = {}
        for r in col_pa:
            col_by[r[0]] = col_by.get(r[0], 0) + int(r[1] or 0)
        for r in col_fb:
            col_by[r[0]] = col_by.get(r[0], 0) + int(r[1] or 0)
        all_months = sorted(set(inv_by) | set(col_by))
        headers = ["month", "invoiced", "collected", "outstanding"]
        csv_rows = []
        for m in all_months:
            inv = round(inv_by.get(m, 0) / 100.0, 2)
            col = round(col_by.get(m, 0) / 100.0, 2)
            csv_rows.append([m, inv, col, round(max(0.0, inv - col), 2)])

    elif metric == "department_volume":
        rows = db.execute(
            text("""
                SELECT d.department_id, d.name, COUNT(a.appointment_id) AS cnt
                FROM appointments a
                JOIN doctors doc ON a.doctor_id = doc.doctor_id
                JOIN departments d ON doc.department_id = d.department_id
                WHERE date(a.scheduled_at) BETWEEN :fd AND :td
                GROUP BY d.department_id, d.name ORDER BY cnt DESC
            """),
            {"fd": from_date, "td": to_date},
        ).fetchall()
        headers = ["department_id", "name", "count"]
        csv_rows = [[r[0], r[1], r[2]] for r in rows]

    else:  # patient_acquisition
        rows = db.execute(
            text("""
                SELECT strftime('%Y-%m', u.created_at), COUNT(*)
                FROM users u WHERE u.role = 'Patient'
                  AND date(u.created_at) BETWEEN :fd AND :td
                GROUP BY 1 ORDER BY 1 ASC
            """),
            {"fd": from_date, "td": to_date},
        ).fetchall()
        headers = ["month", "new_patients"]
        csv_rows = [[r[0], r[1]] for r in rows]

    # ------------------------------------------------------------------
    # Render to CSV string and stream back
    # ------------------------------------------------------------------
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(csv_rows)
    buf.seek(0)

    filename = f"analytics_{metric}_{from_date}_{to_date}.csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
