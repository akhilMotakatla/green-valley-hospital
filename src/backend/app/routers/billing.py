"""Billing Specialist portal — Section 9 endpoints.

Base path: /api/billing
Required role: BillingSpecialist on every endpoint unless an override is noted
(notification log also accepts Admin per Section 9.6).

Scope boundaries enforced by require_billing_specialist at router level:
  - BILL-DENY-1..6: /doctor/*, /patients/{id}/records, /lab/*, /admin/*
    all require roles that exclude BillingSpecialist — no special handling
    needed here; those routers' own require_role checks produce 403.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_billing_specialist, require_role
from app.models import (
    Appointment,
    BillingSpecialist,
    Department,
    Doctor,
    EmailNotification,
    Invoice,
    Patient,
    User,
)
from app.schemas import BillingInvoiceCreateRequest, BillingInvoicePatchRequest
from app.services.email_sink import send_invoice_notification
from app.utils import dumps, loads, now_iso, paginate, total_pages

router = APIRouter(
    prefix="/billing",
    tags=["billing"],
    dependencies=[Depends(require_billing_specialist)],
)


# ---------------------------------------------------------------------------
# 9.2  Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard")
def billing_dashboard(db: Session = Depends(get_db)):
    """Aggregate stats for the billing portal home screen (AC-DASH-TILES).

    Four queries, one response:
      outstanding_invoices  = count of Pending invoices
      awaiting_claims       = count of Pending invoices with has_insurance_claim = 1
      collected_this_month_cents = sum of total_amount_cents for Paid invoices in current UTC month
      total_patients_billed = distinct patient_ids across all invoices
    """
    now = datetime.now(timezone.utc)
    # Start of current UTC month as ISO string prefix for LIKE filtering.
    month_prefix = now.strftime("%Y-%m")

    outstanding_invoices: int = (
        db.query(func.count(Invoice.invoice_id))
        .filter(Invoice.status == "Pending")
        .scalar() or 0
    )
    awaiting_claims: int = (
        db.query(func.count(Invoice.invoice_id))
        .filter(Invoice.status == "Pending", Invoice.has_insurance_claim == 1)
        .scalar() or 0
    )
    collected_this_month_cents: int = (
        db.query(func.coalesce(func.sum(Invoice.total_amount_cents), 0))
        .filter(Invoice.status == "Paid", Invoice.created_at.like(f"{month_prefix}%"))
        .scalar() or 0
    )
    total_patients_billed: int = (
        db.query(func.count(func.distinct(Invoice.patient_id)))
        .scalar() or 0
    )

    return {
        "outstanding_invoices": outstanding_invoices,
        "awaiting_claims": awaiting_claims,
        "collected_this_month_cents": collected_this_month_cents,
        "total_patients_billed": total_patients_billed,
    }


# ---------------------------------------------------------------------------
# 9.3  Invoices
# ---------------------------------------------------------------------------


def _resolve_invoice(db: Session, inv: Invoice) -> dict:
    """Build the full invoice detail dict (includes joined patient/doctor names)."""
    patient = db.get(Patient, inv.patient_id)
    patient_name = patient.user.full_name if patient else None

    appointment_date = None
    doctor_name = None
    department_name = None
    if inv.appointment_id is not None:
        apt = db.get(Appointment, inv.appointment_id)
        if apt is not None:
            appointment_date = apt.scheduled_at
            doc = db.get(Doctor, apt.doctor_id)
            if doc is not None:
                doctor_name = doc.user.full_name
                dept = db.get(Department, doc.department_id)
                department_name = dept.name if dept else None

    return {
        "invoice_id": inv.invoice_id,
        "patient_id": inv.patient_id,
        "patient_name": patient_name,
        "appointment_id": inv.appointment_id,
        "appointment_date": appointment_date,
        "doctor_name": doctor_name,
        "department_name": department_name,
        "line_items": loads(inv.line_items_json) or [],
        "total_amount_cents": inv.total_amount_cents,
        "status": inv.status,
        "has_insurance_claim": inv.has_insurance_claim,
        "created_by_user_id": inv.created_by_user_id,
        "created_at": inv.created_at,
        "paid_at": inv.paid_at,
    }


@router.get("/invoices")
def list_invoices(
    status_: str | None = Query(None, alias="status"),
    has_insurance_claim: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """GET /api/billing/invoices — paginated invoice ledger.

    Filters:
      status            optional status filter (Pending / Paid / Waived)
      has_insurance_claim  0 or 1; if 1 returns only claim-filed invoices
      search            case-insensitive LIKE on patient full_name OR exact
                        invoice_id match if search term is a pure integer
                        (AC-LEDGER-SEARCH)
    """
    query = db.query(Invoice).join(Patient, Patient.patient_id == Invoice.patient_id).join(
        User, User.id == Patient.user_id
    )

    if status_:
        query = query.filter(Invoice.status == status_)
    if has_insurance_claim is not None and has_insurance_claim == 1:
        query = query.filter(Invoice.has_insurance_claim == 1)
    if search:
        like_term = f"%{search}%"
        # If the search term is a pure integer, also match exact invoice_id.
        if search.lstrip("-").isdigit():
            query = query.filter(
                or_(
                    User.full_name.ilike(like_term),
                    Invoice.invoice_id == int(search),
                )
            )
        else:
            query = query.filter(User.full_name.ilike(like_term))

    items, total = paginate(query.order_by(Invoice.created_at.desc()), page, page_size)

    result = []
    for inv in items:
        patient = db.get(Patient, inv.patient_id)
        patient_name = patient.user.full_name if patient else None
        appointment_date = None
        if inv.appointment_id is not None:
            apt = db.get(Appointment, inv.appointment_id)
            if apt:
                appointment_date = apt.scheduled_at
        result.append(
            {
                "invoice_id": inv.invoice_id,
                "patient_id": inv.patient_id,
                "patient_name": patient_name,
                "appointment_id": inv.appointment_id,
                "appointment_date": appointment_date,
                "total_amount_cents": inv.total_amount_cents,
                "status": inv.status,
                "has_insurance_claim": inv.has_insurance_claim,
                "created_at": inv.created_at,
            }
        )

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return _resolve_invoice(db, inv)


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: BillingInvoiceCreateRequest,
    current_user: User = Depends(require_billing_specialist),
    db: Session = Depends(get_db),
):
    if db.get(Patient, payload.patient_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid patient_id"
        )
    if payload.appointment_id is not None and db.get(Appointment, payload.appointment_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid appointment_id"
        )

    inv = Invoice(
        patient_id=payload.patient_id,
        appointment_id=payload.appointment_id,
        line_items_json=dumps([li.model_dump() for li in payload.line_items]),
        total_amount_cents=payload.total_amount_cents,
        status="Pending",
        has_insurance_claim=payload.has_insurance_claim,
        created_by_user_id=current_user.id,
    )
    db.add(inv)
    db.flush()  # get invoice_id before commit

    # Trigger notification on create — get patient details for the email.
    patient = db.get(Patient, payload.patient_id)
    if patient is not None:
        send_invoice_notification(
            db,
            patient_id=payload.patient_id,
            invoice_id=inv.invoice_id,
            patient_name=patient.user.full_name,
            patient_email=patient.user.email,
            recipient_user_id=patient.user_id,
            line_items=[li.model_dump() for li in payload.line_items],
            total_cents=payload.total_amount_cents,
            status="Pending",
            trigger_event="invoice_status_change",
        )

    db.commit()
    db.refresh(inv)
    return _resolve_invoice(db, inv)


@router.patch("/invoices/{invoice_id}")
def update_invoice(
    invoice_id: int,
    payload: BillingInvoicePatchRequest,
    db: Session = Depends(get_db),
):
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    old_status = inv.status
    status_changed = False

    if payload.status is not None and payload.status != inv.status:
        inv.status = payload.status
        status_changed = True
        # OI-7: record the exact UTC timestamp when an invoice is paid
        if payload.status == "Paid":
            inv.paid_at = datetime.now(timezone.utc).isoformat()
    if payload.has_insurance_claim is not None:
        inv.has_insurance_claim = payload.has_insurance_claim
    if payload.line_items is not None:
        inv.line_items_json = dumps([li.model_dump() for li in payload.line_items])
    if payload.total_amount_cents is not None:
        inv.total_amount_cents = payload.total_amount_cents

    # Trigger email notification if status changed (NOTIFY-1..3).
    if status_changed:
        patient = db.get(Patient, inv.patient_id)
        if patient is not None:
            send_invoice_notification(
                db,
                patient_id=inv.patient_id,
                invoice_id=inv.invoice_id,
                patient_name=patient.user.full_name,
                patient_email=patient.user.email,
                recipient_user_id=patient.user_id,
                line_items=loads(inv.line_items_json) or [],
                total_cents=inv.total_amount_cents,
                status=inv.status,
                trigger_event="invoice_status_change",
            )

    db.commit()
    db.refresh(inv)
    return _resolve_invoice(db, inv)


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    if inv.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only Pending invoices may be deleted",
        )
    db.delete(inv)
    db.commit()
    return None


@router.post("/invoices/{invoice_id}/resend-notification", status_code=status.HTTP_201_CREATED)
def resend_notification(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """Manual resend — writes a new email_notifications row with trigger_event='manual_resend'
    (BILL-8 / Section 9.3).
    """
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    patient = db.get(Patient, inv.patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    result = send_invoice_notification(
        db,
        patient_id=inv.patient_id,
        invoice_id=inv.invoice_id,
        patient_name=patient.user.full_name,
        patient_email=patient.user.email,
        recipient_user_id=patient.user_id,
        line_items=loads(inv.line_items_json) or [],
        total_cents=inv.total_amount_cents,
        status=inv.status,
        trigger_event="manual_resend",
    )
    db.commit()

    return result


# ---------------------------------------------------------------------------
# 9.4  Read-Only Patient List (AUTHZ-9 — restricted fields)
# ---------------------------------------------------------------------------


@router.get("/patients")
def list_patients(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Fields returned are strictly limited per AUTHZ-9:
    patient_id, full_name, date_of_birth, phone, email only.
    address, gender, emergency contacts are excluded.
    """
    query = db.query(Patient).join(User, User.id == Patient.user_id)
    if search:
        query = query.filter(User.full_name.ilike(f"%{search}%"))

    items, total = paginate(query, page, page_size)
    return {
        "items": [
            {
                "patient_id": p.patient_id,
                "full_name": p.user.full_name,
                "date_of_birth": p.date_of_birth,
                "phone": p.user.phone,
                "email": p.user.email,
            }
            for p in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# 9.5  Read-Only Appointment List (AUTHZ-8 — no clinical data)
# ---------------------------------------------------------------------------


@router.get("/appointments")
def list_appointments_billing(
    patient_id: int | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Fields returned are strictly limited per AUTHZ-8 — no reason/diagnosis/
    clinical content exposed.  Only: appointment_id, patient_id, patient_name,
    scheduled_at, status, doctor_name, department_name.
    """
    query = db.query(Appointment)
    if patient_id is not None:
        query = query.filter(Appointment.patient_id == patient_id)
    if status_:
        query = query.filter(Appointment.status == status_)

    items, total = paginate(query.order_by(Appointment.scheduled_at.desc()), page, page_size)

    result = []
    for a in items:
        patient = db.get(Patient, a.patient_id)
        doctor = db.get(Doctor, a.doctor_id)
        dept = db.get(Department, doctor.department_id) if doctor else None
        result.append(
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "patient_name": patient.user.full_name if patient else None,
                "scheduled_at": a.scheduled_at,
                "status": a.status,
                "doctor_name": doctor.user.full_name if doctor else None,
                "department_name": dept.name if dept else None,
            }
        )

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


# ---------------------------------------------------------------------------
# 9.6  Email Notification Log
# ---------------------------------------------------------------------------

# NOTE: These two endpoints also accept Admin (Section 9.6), so they use
# require_role("BillingSpecialist", "Admin") instead of the router-level
# require_billing_specialist dependency.  We achieve this by adding an
# explicit dependency that overrides the router-level one.  FastAPI runs
# BOTH dependencies but the endpoint-level one has no effect since the
# router-level one already ran.  To properly override we need to either
# remove the router-level default or add the endpoint as a second router.
# Simplest correct approach: register these on a *sub-router* that has no
# role dependency, and add explicit role checks inside, then include it
# separately.  But that complicates the module.
#
# Chosen approach: the router-level dependency only passes for BillingSpecialist.
# For the Admin case, we add a separate check that catches Admin too —
# done via an inline dependency that accepts EITHER role.

def _require_billing_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("BillingSpecialist", "Admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this action"
        )
    return current_user


# Build a secondary router WITHOUT the BillingSpecialist-only restriction for
# the two notification endpoints that accept Admin as well (Section 9.6).
_notif_router = APIRouter(prefix="/billing", tags=["billing"])


@_notif_router.get("/notifications")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_require_billing_or_admin),
    db: Session = Depends(get_db),
):
    """Paginated notification log — body_html excluded from list items (Section 8.3.5)."""
    query = db.query(EmailNotification).order_by(EmailNotification.sent_at.desc())
    items, total = paginate(query, page, page_size)

    result = []
    for n in items:
        recipient = db.get(User, n.recipient_user_id)
        result.append(
            {
                "notification_id": n.notification_id,
                "recipient_user_id": n.recipient_user_id,
                "recipient_name": recipient.full_name if recipient else None,
                "subject": n.subject,
                "sent_at": n.sent_at,
                "trigger_event": n.trigger_event,
                "related_invoice_id": n.related_invoice_id,
                "status": n.status,
            }
        )

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@_notif_router.get("/notifications/{notification_id}")
def get_notification(
    notification_id: int,
    current_user: User = Depends(_require_billing_or_admin),
    db: Session = Depends(get_db),
):
    """Full notification detail including body_html."""
    n = db.get(EmailNotification, notification_id)
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    recipient = db.get(User, n.recipient_user_id)
    return {
        "notification_id": n.notification_id,
        "recipient_user_id": n.recipient_user_id,
        "recipient_name": recipient.full_name if recipient else None,
        "subject": n.subject,
        "body_html": n.body_html,
        "sent_at": n.sent_at,
        "trigger_event": n.trigger_event,
        "related_invoice_id": n.related_invoice_id,
        "status": n.status,
    }
