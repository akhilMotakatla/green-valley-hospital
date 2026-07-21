"""REQ-12 — Corporate Health Check Packages (B2B).

Public endpoints (no auth):
  GET  /api/public/corporate/packages    — active packages
  POST /api/public/corporate/inquiries   — submit inquiry

Admin endpoints:
  GET    /api/admin/corporate/packages
  POST   /api/admin/corporate/packages
  PUT    /api/admin/corporate/packages/{package_id}
  DELETE /api/admin/corporate/packages/{package_id}   — soft-deactivate
  GET    /api/admin/corporate/inquiries               — paginated with pipeline total
  GET    /api/admin/corporate/inquiries/{inquiry_id}
  PATCH  /api/admin/corporate/inquiries/{inquiry_id}
  GET    /api/admin/corporate/pipeline-summary
"""
from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import CorporateInquiry, CorporatePackage, User
from app.utils import now_iso, paginate, total_pages

router = APIRouter(tags=["corporate"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PackageCreate(BaseModel):
    name: str
    tier_order: int
    description: str
    included_services: list[str]
    price_range_display: str
    is_active: bool = True


class PackageUpdate(BaseModel):
    name: str | None = None
    tier_order: int | None = None
    description: str | None = None
    included_services: list[str] | None = None
    price_range_display: str | None = None
    is_active: bool | None = None


class InquiryCreate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: str | None = None
    estimated_headcount: int | None = None
    package_id: int | None = None
    preferred_schedule: str | None = None


class InquiryPatch(BaseModel):
    status: str | None = None
    notes: str | None = None
    deal_value_cents: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _package_out(p: CorporatePackage, include_active: bool = False) -> dict:
    services = json.loads(p.included_services_json) if p.included_services_json else []
    result: dict = {
        "package_id": p.package_id,
        "name": p.name,
        "tier_order": p.tier_order,
        "description": p.description,
        "included_services": services,
        "price_range_display": p.price_range_display,
        "created_at": p.created_at,
    }
    if include_active:
        result["is_active"] = bool(p.is_active)
    return result


def _inquiry_out(i: CorporateInquiry, db: Session) -> dict:
    package = db.get(CorporatePackage, i.package_id) if i.package_id else None
    return {
        "inquiry_id": i.inquiry_id,
        "company_name": i.company_name,
        "contact_name": i.contact_name,
        "email": i.email,
        "phone": i.phone,
        "headcount": i.headcount,
        "package_id": i.package_id,
        "package_name": package.name if package else None,
        "preferred_schedule": i.preferred_schedule,
        "status": i.status,
        "notes": i.notes,
        "deal_value_cents": i.deal_value_cents,
        "created_at": i.created_at,
        "updated_at": i.updated_at,
    }


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.get("/public/corporate/packages")
def list_public_packages(db: Session = Depends(get_db)):
    packages = (
        db.query(CorporatePackage)
        .filter(CorporatePackage.is_active == 1)
        .order_by(CorporatePackage.tier_order.asc())
        .all()
    )
    return {"items": [_package_out(p) for p in packages]}


@router.post("/public/corporate/inquiries", status_code=201)
def submit_inquiry(
    body: InquiryCreate,
    db: Session = Depends(get_db),
):
    # Required field validation
    if not body.company_name or not body.company_name.strip():
        raise HTTPException(status_code=400, detail="company_name is required")
    if not body.contact_name or not body.contact_name.strip():
        raise HTTPException(status_code=400, detail="contact_name is required")
    if not body.email or not body.email.strip():
        raise HTTPException(status_code=400, detail="email is required")

    # Email format validation
    if not _EMAIL_RE.match(body.email.strip()):
        raise HTTPException(status_code=422, detail="Invalid email format")

    if body.estimated_headcount is not None and body.estimated_headcount < 1:
        raise HTTPException(status_code=400, detail="estimated_headcount must be >= 1")

    # Validate package exists if provided
    if body.package_id is not None:
        pkg = db.get(CorporatePackage, body.package_id)
        if pkg is None:
            raise HTTPException(status_code=404, detail="Package not found")

    inquiry = CorporateInquiry(
        company_name=body.company_name.strip(),
        contact_name=body.contact_name.strip(),
        email=body.email.strip(),
        phone=body.phone,
        headcount=body.estimated_headcount,
        package_id=body.package_id,
        preferred_schedule=body.preferred_schedule,
        status="New",
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return {
        "inquiry_id": inquiry.inquiry_id,
        "message": "Thank you! We'll be in touch shortly.",
    }


# ---------------------------------------------------------------------------
# Admin: packages
# ---------------------------------------------------------------------------

@router.get("/admin/corporate/packages")
def admin_list_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    packages = (
        db.query(CorporatePackage)
        .order_by(CorporatePackage.tier_order.asc())
        .all()
    )
    return {"items": [_package_out(p, include_active=True) for p in packages]}


@router.post("/admin/corporate/packages", status_code=201)
def admin_create_package(
    body: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    pkg = CorporatePackage(
        name=body.name,
        tier_order=body.tier_order,
        description=body.description,
        included_services_json=json.dumps(body.included_services),
        price_range_display=body.price_range_display,
        is_active=1 if body.is_active else 0,
        created_at=now_iso(),
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return _package_out(pkg, include_active=True)


@router.put("/admin/corporate/packages/{package_id}")
def admin_update_package(
    package_id: int,
    body: PackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    pkg = db.get(CorporatePackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    if body.name is not None:
        pkg.name = body.name
    if body.tier_order is not None:
        pkg.tier_order = body.tier_order
    if body.description is not None:
        pkg.description = body.description
    if body.included_services is not None:
        pkg.included_services_json = json.dumps(body.included_services)
    if body.price_range_display is not None:
        pkg.price_range_display = body.price_range_display
    if body.is_active is not None:
        pkg.is_active = 1 if body.is_active else 0

    db.commit()
    db.refresh(pkg)
    return _package_out(pkg, include_active=True)


@router.delete("/admin/corporate/packages/{package_id}")
def admin_deactivate_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    pkg = db.get(CorporatePackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    pkg.is_active = 0
    db.commit()
    return {"package_id": pkg.package_id, "is_active": False}


# ---------------------------------------------------------------------------
# Admin: inquiries
# ---------------------------------------------------------------------------

@router.get("/admin/corporate/inquiries")
def admin_list_inquiries(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    q = db.query(CorporateInquiry)
    if status:
        q = q.filter(CorporateInquiry.status == status)
    q = q.order_by(CorporateInquiry.created_at.desc())
    items, total = paginate(q, page, page_size)

    # Pipeline total: sum of deal_value_cents where status = 'ClosedWon'
    pipeline_total = (
        db.query(func.sum(CorporateInquiry.deal_value_cents))
        .filter(CorporateInquiry.status == "ClosedWon")
        .scalar()
        or 0
    )

    return {
        "items": [_inquiry_out(i, db) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
        "pipeline_total_cents": pipeline_total,
    }


@router.get("/admin/corporate/inquiries/{inquiry_id}")
def admin_get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    inquiry = db.get(CorporateInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return _inquiry_out(inquiry, db)


@router.patch("/admin/corporate/inquiries/{inquiry_id}")
def admin_patch_inquiry(
    inquiry_id: int,
    body: InquiryPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    VALID_STATUSES = ("New", "Contacted", "ProposalSent", "ClosedWon", "ClosedLost")
    inquiry = db.get(CorporateInquiry, inquiry_id)
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        inquiry.status = body.status
    if body.notes is not None:
        inquiry.notes = body.notes
    if body.deal_value_cents is not None:
        if body.deal_value_cents < 0:
            raise HTTPException(status_code=400, detail="deal_value_cents cannot be negative")
        inquiry.deal_value_cents = body.deal_value_cents

    inquiry.updated_at = now_iso()
    db.commit()
    db.refresh(inquiry)
    return _inquiry_out(inquiry, db)


# ---------------------------------------------------------------------------
# Admin: pipeline summary
# ---------------------------------------------------------------------------

@router.get("/admin/corporate/pipeline-summary")
def admin_pipeline_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    total_closed_won = (
        db.query(func.sum(CorporateInquiry.deal_value_cents))
        .filter(CorporateInquiry.status == "ClosedWon")
        .scalar()
        or 0
    )

    # Count by status
    counts = (
        db.query(CorporateInquiry.status, func.count(CorporateInquiry.inquiry_id))
        .group_by(CorporateInquiry.status)
        .all()
    )
    count_by_status = {row[0]: row[1] for row in counts}

    return {
        "total_closed_won_value": total_closed_won,
        "count_by_status": count_by_status,
    }
