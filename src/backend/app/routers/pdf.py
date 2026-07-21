"""REQ-08 — Patient Medical Record Export (PDF endpoint).

Endpoint:
  GET /api/patients/me/export-pdf?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

Patient only (AUTHZ-11). Streams PDF bytes. Date params are optional.
Returns 503 if WeasyPrint is unavailable (Windows GTK3 missing).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Patient, User
from app.services.pdf_export import (
    WEASYPRINT_AVAILABLE,
    generate_pdf,
    get_appointments_for_pdf,
    render_pdf_template,
)

router = APIRouter(tags=["pdf-export"])


@router.get("/patients/me/export-pdf")
def export_pdf(
    start_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Patient")),
):
    if not WEASYPRINT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF export temporarily unavailable — WeasyPrint requires GTK3 runtime",
        )

    # Validate date params
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date must be YYYY-MM-DD format")
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date must be YYYY-MM-DD format")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must not be after end_date")

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if patient is None:
        raise HTTPException(status_code=403, detail="Patient profile not found")

    appointments, lab_results = get_appointments_for_pdf(db, patient.patient_id, start_date, end_date)
    html_content = render_pdf_template(
        patient=patient,
        patient_user=current_user,
        appointments=appointments,
        lab_results=lab_results,
        start_date=start_date,
        end_date=end_date,
    )

    pdf_bytes = generate_pdf(html_content)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"GVH_MedicalRecord_{patient.patient_id}_{today}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
