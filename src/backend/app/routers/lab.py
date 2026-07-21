from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import LAB_RESULTS_DIR, PROJECT_ROOT
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Doctor, LabOrder, LabResult, LabTechnician, Patient, User
from app.schemas import LabOrderStatusRequest
from app.utils import now_iso, paginate, save_upload, total_pages

router = APIRouter(prefix="/lab", tags=["lab"], dependencies=[Depends(require_role("Lab"))])


@router.get("/orders")
def list_orders(
    test_type: str | None = None,
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(LabOrder)
    if test_type:
        query = query.filter(LabOrder.test_type == test_type)
    if status_:
        query = query.filter(LabOrder.status == status_)
    items, total = paginate(query.order_by(LabOrder.created_at.desc()), page, page_size)

    result = []
    for o in items:
        patient = db.get(Patient, o.patient_id)
        doctor = db.get(Doctor, o.doctor_id)
        result.append(
            {
                "order_id": o.order_id,
                # LAB-5 / AUTHZ-4: minimal patient fields only, never full history.
                "patient_name": patient.user.full_name if patient else None,
                "patient_dob": patient.date_of_birth if patient else None,
                "ordering_doctor_name": doctor.user.full_name if doctor else None,
                "test_type": o.test_type,
                "test_subtype": o.test_subtype,
                "status": o.status,
                "notes": o.notes,
                "created_at": o.created_at,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, payload: LabOrderStatusRequest, db: Session = Depends(get_db)):
    order = db.get(LabOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    order.status = payload.status
    db.commit()
    return {"order_id": order.order_id, "status": order.status}


@router.post("/orders/{order_id}/results", status_code=status.HTTP_201_CREATED)
async def create_result(
    order_id: int,
    result_data: str = Form(...),
    file: UploadFile | None = File(None),
    current_user: User = Depends(require_role("Lab")),
    db: Session = Depends(get_db),
):
    order = db.get(LabOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")

    existing = db.query(LabResult).filter(LabResult.order_id == order_id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A result already exists for this order; use the amend endpoint")

    file_path = None
    if file is not None:
        filename = f"1_{file.filename}"
        file_path = await save_upload(file, LAB_RESULTS_DIR / str(order_id), filename, kind="lab")

    result = LabResult(
        order_id=order_id,
        result_data=result_data,
        file_attachment_path=file_path,
        version=1,
        recorded_by_user_id=current_user.id,
        is_finalized=1,
        finalized_at=now_iso(),
    )
    db.add(result)
    order.status = "Completed"
    db.commit()
    db.refresh(result)

    return {
        "result_id": result.result_id,
        "order_id": result.order_id,
        "result_data": result.result_data,
        "file_attachment_path": result.file_attachment_path,
        "version": result.version,
        "is_finalized": bool(result.is_finalized),
        "finalized_at": result.finalized_at,
    }


@router.post("/orders/{order_id}/results/amend", status_code=status.HTTP_201_CREATED)
async def amend_result(
    order_id: int,
    result_data: str = Form(...),
    file: UploadFile | None = File(None),
    current_user: User = Depends(require_role("Lab")),
    db: Session = Depends(get_db),
):
    order = db.get(LabOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")

    prior = db.query(LabResult).filter(LabResult.order_id == order_id, LabResult.is_finalized == 1).order_by(LabResult.version.desc()).first()
    if prior is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No prior finalized result exists for this order to amend")

    next_version = prior.version + 1

    file_path = None
    if file is not None:
        filename = f"{next_version}_{file.filename}"
        file_path = await save_upload(file, LAB_RESULTS_DIR / str(order_id), filename, kind="lab")

    result = LabResult(
        order_id=order_id,
        result_data=result_data,
        file_attachment_path=file_path,
        version=next_version,
        recorded_by_user_id=current_user.id,
        is_finalized=1,
        finalized_at=now_iso(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "result_id": result.result_id,
        "order_id": result.order_id,
        "result_data": result.result_data,
        "file_attachment_path": result.file_attachment_path,
        "version": result.version,
        "is_finalized": bool(result.is_finalized),
        "finalized_at": result.finalized_at,
    }


@router.get("/orders/{order_id}/results")
def get_order_results(order_id: int, db: Session = Depends(get_db)):
    order = db.get(LabOrder, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found")
    results = db.query(LabResult).filter(LabResult.order_id == order_id).order_by(LabResult.version).all()
    return {
        "order_id": order.order_id,
        "results": [
            {
                "result_id": r.result_id,
                "result_data": r.result_data,
                "file_attachment_path": r.file_attachment_path,
                "version": r.version,
                "is_finalized": bool(r.is_finalized),
                "finalized_at": r.finalized_at,
            }
            for r in results
        ],
    }


# Note: registered without the router-level Lab-only dependency override —
# this endpoint is reachable by Doctor/Patient/Admin/Lab per its own
# ownership check, so it's mounted on a sub-router without the blanket
# require_role("Lab") dependency.
file_router = APIRouter(prefix="/lab", tags=["lab"])


@file_router.get("/results/{result_id}/file")
def download_result_file(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = db.get(LabResult, result_id)
    if result is None or not result.file_attachment_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    order = db.get(LabOrder, result.order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    authorized = False
    if current_user.role == "Admin":
        authorized = True
    elif current_user.role == "Lab":
        authorized = True
    elif current_user.role == "Doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        authorized = doctor is not None and doctor.doctor_id == order.doctor_id
    elif current_user.role == "Patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        authorized = patient is not None and patient.patient_id == order.patient_id

    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")

    full_path = PROJECT_ROOT / result.file_attachment_path
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    return FileResponse(str(full_path))
