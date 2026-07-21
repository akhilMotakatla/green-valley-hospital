"""REQ-08 — Patient Medical Record PDF Export.

WeasyPrint is the PDF engine (OI-3 decision). On Windows without GTK3 runtime,
the import fails gracefully — the endpoint returns HTTP 503 in that case.

Functions:
  get_appointments_for_pdf(db, patient_id, start_date, end_date)
      -> tuple[list[dict], list[dict]]   (appointments, lab_results)
  render_pdf_template(patient, patient_user, appointments, lab_results, start_date, end_date)
  generate_pdf(html_content) -> bytes
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    DischargeSummary,
    IntakeForm,
    LabOrder,
    LabResult,
    Patient,
    Prescription,
    User,
    Vitals,
    VisitNote,
)

# WeasyPrint import — fail gracefully on Windows without GTK3
WEASYPRINT_AVAILABLE = False
_weasyprint_error: str = ""
try:
    from weasyprint import HTML as WeasyHTML  # type: ignore
    WEASYPRINT_AVAILABLE = True
except Exception as exc:
    _weasyprint_error = str(exc)


def get_appointments_for_pdf(
    db: Session,
    patient_id: int,
    start_date: str | None,
    end_date: str | None,
) -> tuple[list[dict], list[dict]]:
    """Fetch completed appointments and all finalized lab results for the patient.

    Lab results are collected ONCE here, outside the appointment loop, so they
    are never duplicated across appointment sections in the rendered PDF.
    Returns (appointments, lab_results) — the caller passes these separately to
    render_pdf_template so lab results appear in their own top-level section.
    """
    q = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "Completed",
        )
        .order_by(Appointment.scheduled_at.asc())
    )
    if start_date:
        q = q.filter(Appointment.scheduled_at >= start_date)
    if end_date:
        q = q.filter(Appointment.scheduled_at <= end_date + "T23:59:59")

    appointments = q.all()

    # Collect ALL finalized lab results for this patient exactly once.
    # Apply the same date range (by finalized_at) when provided.
    lab_orders_all = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id == patient_id)
        .all()
    )
    lab_results: list[dict] = []
    for lo in lab_orders_all:
        results_q = (
            db.query(LabResult)
            .filter(
                LabResult.order_id == lo.order_id,
                LabResult.is_finalized == 1,
            )
        )
        if start_date:
            results_q = results_q.filter(LabResult.finalized_at >= start_date)
        if end_date:
            results_q = results_q.filter(LabResult.finalized_at <= end_date + "T23:59:59")
        for lr in results_q.all():
            lab_results.append({
                "test_type": lo.test_type,
                "test_subtype": lo.test_subtype,
                "result_data": lr.result_data,
                "finalized_at": lr.finalized_at,
            })

    result = []
    for appt in appointments:
        from app.models import Doctor
        doctor = db.query(Doctor).filter(Doctor.doctor_id == appt.doctor_id).first()
        doctor_user = db.get(User, doctor.user_id) if doctor else None
        from app.models import Department
        dept = db.get(Department, doctor.department_id) if doctor else None

        visit_notes = (
            db.query(VisitNote)
            .filter(VisitNote.appointment_id == appt.appointment_id)
            .all()
        )
        prescriptions = (
            db.query(Prescription)
            .filter(Prescription.appointment_id == appt.appointment_id)
            .all()
        )
        vitals = (
            db.query(Vitals)
            .filter(Vitals.appointment_id == appt.appointment_id)
            .all()
        )
        intake = (
            db.query(IntakeForm)
            .filter(IntakeForm.appointment_id == appt.appointment_id)
            .first()
        )
        discharge = (
            db.query(DischargeSummary)
            .filter(DischargeSummary.appointment_id == appt.appointment_id)
            .first()
        )

        result.append({
            "appointment_id": appt.appointment_id,
            "scheduled_at": appt.scheduled_at,
            "doctor_name": doctor_user.full_name if doctor_user else "Unknown",
            "department": dept.name if dept else "Unknown",
            "reason": appt.reason,
            "visit_notes": [
                {
                    "diagnosis": vn.diagnosis,
                    "notes": vn.notes,
                    "created_at": vn.created_at,
                }
                for vn in visit_notes
            ],
            "prescriptions": [
                {
                    "medicines": json.loads(p.medicines_json) if p.medicines_json else [],
                    "instructions": p.instructions,
                }
                for p in prescriptions
            ],
            "vitals": [
                {
                    "systolic_bp": v.systolic_bp,
                    "diastolic_bp": v.diastolic_bp,
                    "weight_kg": v.weight_kg,
                    "pulse_bpm": v.pulse_bpm,
                    "temperature_celsius": v.temperature_celsius,
                    "recorded_at": v.recorded_at,
                }
                for v in vitals
            ],
            "intake_chief_complaint": intake.chief_complaint if intake and intake.submitted_at else None,
            "discharge": {
                "key_findings": discharge.key_findings,
                "patient_instructions": discharge.patient_instructions,
                "activity_restrictions": discharge.activity_restrictions,
                "medication_reminders": discharge.medication_reminders,
            } if discharge else None,
        })

    return result, lab_results


def render_pdf_template(
    patient: Patient,
    patient_user: User,
    appointments: list[dict],
    lab_results: list[dict],
    start_date: str | None,
    end_date: str | None,
) -> str:
    """Build the HTML string for the PDF report."""
    export_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    dob = patient.date_of_birth or "N/A"
    date_range_str = ""
    if start_date or end_date:
        date_range_str = f"{start_date or 'All'} to {end_date or 'Present'}"
    else:
        date_range_str = "All records"

    watermark_text = f"Green Valley Hospital | {patient_user.full_name} | ID:{patient.patient_id} | {export_dt}"

    # --- Appointment sections ---
    appt_sections_html = ""
    if not appointments:
        appt_sections_html = "<p style='color:#555;font-style:italic;'>No completed visits found for the selected period.</p>"
    else:
        for appt in appointments:
            notes_html = ""
            for vn in appt["visit_notes"]:
                notes_html += f"<p><strong>Diagnosis:</strong> {vn['diagnosis'] or 'N/A'}</p>"
                notes_html += f"<p><strong>Notes:</strong> {vn['notes']}</p>"

            rx_html = ""
            for rx in appt["prescriptions"]:
                if rx["medicines"]:
                    rx_html += "<table class='data-table'><thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th></tr></thead><tbody>"
                    for med in rx["medicines"]:
                        rx_html += f"<tr><td>{med.get('name','')}</td><td>{med.get('dosage','')}</td><td>{med.get('frequency','')}</td><td>{med.get('duration','')}</td></tr>"
                    rx_html += "</tbody></table>"
                if rx["instructions"]:
                    rx_html += f"<p><em>Instructions: {rx['instructions']}</em></p>"

            vitals_html = ""
            for v in appt["vitals"]:
                parts = []
                if v["systolic_bp"] is not None:
                    parts.append(f"BP: {v['systolic_bp']}/{v['diastolic_bp']} mmHg")
                if v["weight_kg"] is not None:
                    parts.append(f"Weight: {v['weight_kg']} kg")
                if v["pulse_bpm"] is not None:
                    parts.append(f"Pulse: {v['pulse_bpm']} bpm")
                if v["temperature_celsius"] is not None:
                    parts.append(f"Temp: {v['temperature_celsius']} °C")
                vitals_html += "<p>" + " | ".join(parts) + "</p>"

            discharge_html = ""
            if appt["discharge"]:
                d = appt["discharge"]
                discharge_html = f"<p><strong>Key Findings:</strong> {d['key_findings']}</p>"
                if d["patient_instructions"]:
                    discharge_html += f"<p><strong>Instructions:</strong> {d['patient_instructions']}</p>"
                if d["activity_restrictions"]:
                    discharge_html += f"<p><strong>Activity Restrictions:</strong> {d['activity_restrictions']}</p>"
                if d["medication_reminders"]:
                    discharge_html += f"<p><strong>Medication Reminders:</strong> {d['medication_reminders']}</p>"

            intake_html = ""
            if appt["intake_chief_complaint"]:
                intake_html = f"<p><strong>Chief Complaint (Intake):</strong> {appt['intake_chief_complaint']}</p>"

            appt_sections_html += f"""
            <div class="visit-section">
              <h3>{appt['scheduled_at'][:10]} — Dr. {appt['doctor_name']} ({appt['department']})</h3>
              {f"<p><strong>Reason:</strong> {appt['reason']}</p>" if appt['reason'] else ""}
              {intake_html}
              {("<h4>Visit Notes</h4>" + notes_html) if notes_html else ""}
              {("<h4>Prescriptions</h4>" + rx_html) if rx_html else ""}
              {("<h4>Vitals</h4>" + vitals_html) if vitals_html else ""}
              {("<h4>Discharge Summary</h4>" + discharge_html) if discharge_html else ""}
            </div>
            """

    # --- Lab Results section (separate, rendered once after all appointment sections) ---
    lab_section_html = ""
    if lab_results:
        lab_rows = ""
        for lr in lab_results:
            lab_rows += (
                f"<p><strong>{lr['test_type']} — {lr['test_subtype'] or ''}</strong>: "
                f"{lr['result_data']} "
                f"<em>(finalized {lr['finalized_at'] or ''})</em></p>"
            )
        lab_section_html = f"""
        <div class="visit-section">
          <h3>Lab Results</h3>
          {lab_rows}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Medical Record — {patient_user.full_name}</title>
<style>
  body {{
    font-family: 'Arial', sans-serif;
    color: #222;
    background: #fff;
    margin: 0;
    padding: 0;
    font-size: 11pt;
    line-height: 1.5;
  }}
  .watermark {{
    position: fixed;
    top: 45%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-size: 14pt;
    color: rgba(0,0,0,0.10);
    white-space: nowrap;
    pointer-events: none;
    z-index: 0;
  }}
  .cover-page {{
    text-align: center;
    padding: 80px 40px;
    page-break-after: always;
  }}
  .cover-page h1 {{ font-size: 22pt; color: #1a4a2e; margin-bottom: 8px; }}
  .cover-page h2 {{ font-size: 16pt; color: #444; margin-bottom: 32px; }}
  .cover-meta {{ font-size: 11pt; color: #555; margin: 8px 0; }}
  .cover-meta strong {{ color: #222; }}
  .visit-section {{
    padding: 24px 40px;
    page-break-inside: avoid;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 16px;
  }}
  .visit-section h3 {{
    font-size: 13pt;
    color: #1a4a2e;
    margin: 0 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #1a4a2e;
  }}
  .visit-section h4 {{
    font-size: 11pt;
    color: #333;
    margin: 12px 0 6px 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
    margin: 8px 0;
  }}
  .data-table th {{
    background: #f0f0f0;
    text-align: left;
    padding: 4px 8px;
    border: 1px solid #ccc;
  }}
  .data-table td {{
    padding: 4px 8px;
    border: 1px solid #ccc;
  }}
  @page {{
    size: A4;
    margin: 20mm 15mm;
    @bottom-center {{
      content: "Green Valley Hospital | {patient_user.full_name} | ID:{patient.patient_id} | {export_dt}";
      font-size: 8pt;
      color: rgba(0,0,0,0.20);
    }}
  }}
</style>
</head>
<body>
  <div class="watermark">{watermark_text}</div>

  <!-- Cover Page -->
  <div class="cover-page">
    <h1>Green Valley Hospital</h1>
    <h2>Medical Record Export</h2>
    <div class="cover-meta"><strong>Patient Name:</strong> {patient_user.full_name}</div>
    <div class="cover-meta"><strong>Date of Birth:</strong> {dob}</div>
    <div class="cover-meta"><strong>Patient ID:</strong> {patient.patient_id}</div>
    <div class="cover-meta"><strong>Export Date:</strong> {export_dt}</div>
    <div class="cover-meta"><strong>Date Range:</strong> {date_range_str}</div>
    <div class="cover-meta" style="margin-top:32px;font-size:9pt;color:#888;">
      This document contains confidential medical information. Do not distribute.
    </div>
  </div>

  <!-- Visit Sections -->
  <div style="padding: 0 0 40px 0;">
    {appt_sections_html}
  </div>

  <!-- Lab Results (separate section, appears once after all visits) -->
  {lab_section_html}
</body>
</html>"""

    return html


def generate_pdf(html_content: str) -> bytes:
    """Convert HTML to PDF bytes using WeasyPrint."""
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            f"WeasyPrint is not available: {_weasyprint_error}"
        )
    return WeasyHTML(string=html_content).write_pdf()
