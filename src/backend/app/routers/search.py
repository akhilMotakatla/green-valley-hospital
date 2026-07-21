"""REQ-07 — Public Symptom / Condition Search.

Endpoints:
  GET  /api/public/search?q=...                           — public search
  GET  /api/admin/departments/{department_id}/tags        — list tags
  POST /api/admin/departments/{department_id}/tags        — add tag
  PUT  /api/admin/departments/{department_id}/tags/{tag_id} — update tag
  DELETE /api/admin/departments/{department_id}/tags/{tag_id} — remove tag

No auth required for the public search endpoint.
Admin-only for tag management.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Department, DepartmentSymptomTag, Doctor, User
from app.utils import now_iso

router = APIRouter(tags=["search"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TagCreate(BaseModel):
    tag_text: str


class TagUpdate(BaseModel):
    tag_text: str


class TagOut(BaseModel):
    tag_id: int
    department_id: int
    tag_text: str
    created_at: str


# ---------------------------------------------------------------------------
# GET /api/public/search?q=...
# ---------------------------------------------------------------------------

@router.get("/public/search")
def public_search(
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    q_str = q.strip()[:200]
    if len(q_str) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    like = f"%{q_str}%"

    # Search departments: name match (rank 1), description match (rank 2), tag match (rank 3)
    # Deduplicate by department_id, keeping best rank
    dept_results: dict[int, dict] = {}

    # Rank 1: name match
    for dept in db.query(Department).filter(
        Department.is_active == 1,
        Department.name.ilike(like),
    ).all():
        if dept.department_id not in dept_results:
            dept_results[dept.department_id] = {
                "department_id": dept.department_id,
                "name": dept.name,
                "description": dept.description,
                "match_type": "name",
                "rank": 1,
            }

    # Rank 2: description match
    for dept in db.query(Department).filter(
        Department.is_active == 1,
        Department.description.ilike(like),
    ).all():
        if dept.department_id not in dept_results:
            dept_results[dept.department_id] = {
                "department_id": dept.department_id,
                "name": dept.name,
                "description": dept.description,
                "match_type": "description",
                "rank": 2,
            }

    # Rank 3: symptom tag match
    matched_tags = (
        db.query(DepartmentSymptomTag)
        .filter(DepartmentSymptomTag.tag_text.ilike(like))
        .all()
    )
    for tag in matched_tags:
        if tag.department_id not in dept_results:
            dept = db.get(Department, tag.department_id)
            if dept and dept.is_active:
                dept_results[tag.department_id] = {
                    "department_id": dept.department_id,
                    "name": dept.name,
                    "description": dept.description,
                    "match_type": "symptom_tag",
                    "matched_tag": tag.tag_text,
                    "rank": 3,
                }

    # Sort by rank
    departments = sorted(dept_results.values(), key=lambda x: x["rank"])

    # Search doctors: specialty or bio match (active accounts only)
    doctor_results: list[dict] = []
    doctors = (
        db.query(Doctor)
        .join(User, Doctor.user_id == User.id)
        .filter(
            User.is_active == 1,
        )
        .all()
    )
    for doc in doctors:
        specialty_match = doc.specialty and q_str.lower() in doc.specialty.lower()
        bio_match = doc.bio and q_str.lower() in doc.bio.lower()
        if specialty_match or bio_match:
            doc_user = db.get(User, doc.user_id)
            dept = db.get(Department, doc.department_id)
            doctor_results.append({
                "doctor_id": doc.doctor_id,
                "full_name": doc_user.full_name if doc_user else None,
                "specialty": doc.specialty,
                "bio": doc.bio,
                "department_name": dept.name if dept else None,
                "profile_photo_path": doc.profile_photo_path,
                "match_type": "specialty" if specialty_match else "bio",
            })

    total = len(departments) + len(doctor_results)
    return {
        "query": q_str,
        "departments": departments,
        "doctors": doctor_results,
        "total": total,
    }


# ---------------------------------------------------------------------------
# GET /api/admin/departments/{department_id}/tags
# ---------------------------------------------------------------------------

@router.get("/admin/departments/{department_id}/tags", response_model=list[TagOut])
def list_tags(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    dept = db.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")

    tags = (
        db.query(DepartmentSymptomTag)
        .filter(DepartmentSymptomTag.department_id == department_id)
        .order_by(DepartmentSymptomTag.tag_text)
        .all()
    )
    return [
        TagOut(
            tag_id=t.tag_id,
            department_id=t.department_id,
            tag_text=t.tag_text,
            created_at=t.created_at,
        )
        for t in tags
    ]


# ---------------------------------------------------------------------------
# POST /api/admin/departments/{department_id}/tags
# ---------------------------------------------------------------------------

@router.post("/admin/departments/{department_id}/tags", response_model=TagOut, status_code=201)
def add_tag(
    department_id: int,
    body: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    dept = db.get(Department, department_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="Department not found")

    tag_text = body.tag_text.strip()
    if not tag_text:
        raise HTTPException(status_code=400, detail="tag_text cannot be empty")
    if len(tag_text) > 100:
        raise HTTPException(status_code=400, detail="tag_text exceeds 100 character limit")

    # 50-tag limit per department
    count = (
        db.query(DepartmentSymptomTag)
        .filter(DepartmentSymptomTag.department_id == department_id)
        .count()
    )
    if count >= 50:
        raise HTTPException(
            status_code=400,
            detail="Department has reached the maximum of 50 tags",
        )

    # Case-insensitive uniqueness check
    existing = (
        db.query(DepartmentSymptomTag)
        .filter(
            DepartmentSymptomTag.department_id == department_id,
            DepartmentSymptomTag.tag_text.ilike(tag_text),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="A tag with this text already exists for this department",
        )

    tag = DepartmentSymptomTag(
        department_id=department_id,
        tag_text=tag_text,
        created_at=now_iso(),
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return TagOut(
        tag_id=tag.tag_id,
        department_id=tag.department_id,
        tag_text=tag.tag_text,
        created_at=tag.created_at,
    )


# ---------------------------------------------------------------------------
# PUT /api/admin/departments/{department_id}/tags/{tag_id}
# ---------------------------------------------------------------------------

@router.put("/admin/departments/{department_id}/tags/{tag_id}", response_model=TagOut)
def update_tag(
    department_id: int,
    tag_id: int,
    body: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    tag = db.get(DepartmentSymptomTag, tag_id)
    if tag is None or tag.department_id != department_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    new_text = body.tag_text.strip()
    if not new_text:
        raise HTTPException(status_code=400, detail="tag_text cannot be empty")
    if len(new_text) > 100:
        raise HTTPException(status_code=400, detail="tag_text exceeds 100 character limit")

    # Case-insensitive conflict check (excluding self)
    conflict = (
        db.query(DepartmentSymptomTag)
        .filter(
            DepartmentSymptomTag.department_id == department_id,
            DepartmentSymptomTag.tag_text.ilike(new_text),
            DepartmentSymptomTag.tag_id != tag_id,
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="A tag with this text already exists for this department",
        )

    tag.tag_text = new_text
    db.commit()
    db.refresh(tag)
    return TagOut(
        tag_id=tag.tag_id,
        department_id=tag.department_id,
        tag_text=tag.tag_text,
        created_at=tag.created_at,
    )


# ---------------------------------------------------------------------------
# DELETE /api/admin/departments/{department_id}/tags/{tag_id}
# ---------------------------------------------------------------------------

@router.delete("/admin/departments/{department_id}/tags/{tag_id}", status_code=204)
def delete_tag(
    department_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    tag = db.get(DepartmentSymptomTag, tag_id)
    if tag is None or tag.department_id != department_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()
