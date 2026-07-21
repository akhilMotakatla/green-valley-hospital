from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import BLOG_COVERS_DIR
from app.database import get_db
from app.deps import require_role
from app.models import (
    Appointment,
    BillingSpecialist,
    BlogArticle,
    ContactMessage,
    Department,
    Doctor,
    Invoice,
    LabOrder,
    LabTechnician,
    Patient,
    SiteContent,
    StaffMember,
    User,
)
from app.schemas import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserRoleRequest,
    AdminUserStatusRequest,
    BlogUpdateRequest,
    ContactMessageStatusRequest,
    DepartmentCreateRequest,
    DepartmentStatusRequest,
    DepartmentUpdateRequest,
    SiteContentAboutRequest,
    SiteContentHomeRequest,
)
from app.security import hash_password
from app.utils import dumps, now_iso, paginate, save_upload, total_pages, unique_slug, utcnow, write_audit_log

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("Admin"))])


# ---------------- 3.1 User & account management ----------------


@router.get("/users")
def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == (1 if is_active else 0))
    items, total = paginate(query.order_by(User.id), page, page_size)
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "full_name": u.full_name,
                "phone": u.phone,
                "is_active": bool(u.is_active),
                "created_at": u.created_at,
            }
            for u in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: AdminCreateUserRequest, current_user: User = Depends(require_role("Admin")), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already registered")

    if payload.role in ("Doctor", "Staff") and payload.department_id is not None:
        if db.get(Department, payload.department_id) is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid department_id")
    if payload.role == "Doctor" and payload.department_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="department_id is required for Doctor role")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        phone=payload.phone,
        is_active=1,
    )
    db.add(user)
    db.flush()

    profile: dict = {}
    if payload.role == "Doctor":
        doctor = Doctor(
            user_id=user.id,
            department_id=payload.department_id,
            specialty=payload.specialty or "",
            qualifications=payload.qualifications,
            bio=payload.bio,
            years_experience=payload.years_experience or 0,
            consultation_hours=payload.consultation_hours,
        )
        db.add(doctor)
        db.flush()
        profile = {"doctor_id": doctor.doctor_id, "department_id": doctor.department_id, "specialty": doctor.specialty}
    elif payload.role == "Staff":
        staff = StaffMember(user_id=user.id, department_id=payload.department_id)
        db.add(staff)
        db.flush()
        profile = {"staff_id": staff.staff_id, "department_id": staff.department_id}
    elif payload.role == "Lab":
        lab = LabTechnician(user_id=user.id)
        db.add(lab)
        db.flush()
        profile = {"lab_user_id": lab.lab_user_id}
    elif payload.role == "BillingSpecialist":
        # BILL-ROLE-1 / BILL-ROLE-3: auto-create billing_specialists profile row.
        bs = BillingSpecialist(user_id=user.id, employee_id=payload.employee_id)
        db.add(bs)
        db.flush()
        profile = {"billing_specialist_id": bs.billing_specialist_id, "employee_id": bs.employee_id}

    write_audit_log(db, actor_user_id=current_user.id, action="user_created", target_user_id=user.id, details=f"role={payload.role}")
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": bool(user.is_active),
        "created_at": user.created_at,
        **profile,
    }


def _serialize_full_user(db: Session, user: User) -> dict:
    result = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "phone": user.phone,
        "is_active": bool(user.is_active),
        "created_at": user.created_at,
    }
    if user.role == "Patient":
        p = db.query(Patient).filter(Patient.user_id == user.id).first()
        if p:
            result["profile"] = {
                "patient_id": p.patient_id,
                "date_of_birth": p.date_of_birth,
                "gender": p.gender,
                "address": p.address,
                "emergency_contact_name": p.emergency_contact_name,
                "emergency_contact_phone": p.emergency_contact_phone,
            }
    elif user.role == "Doctor":
        d = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if d:
            result["profile"] = {
                "doctor_id": d.doctor_id,
                "department_id": d.department_id,
                "specialty": d.specialty,
                "qualifications": d.qualifications,
                "bio": d.bio,
                "years_experience": d.years_experience,
                "consultation_hours": d.consultation_hours,
            }
    elif user.role == "Staff":
        s = db.query(StaffMember).filter(StaffMember.user_id == user.id).first()
        if s:
            result["profile"] = {"staff_id": s.staff_id, "department_id": s.department_id}
    elif user.role == "Lab":
        l = db.query(LabTechnician).filter(LabTechnician.user_id == user.id).first()
        if l:
            result["profile"] = {"lab_user_id": l.lab_user_id}
    elif user.role == "BillingSpecialist":
        bs = db.query(BillingSpecialist).filter(BillingSpecialist.user_id == user.id).first()
        if bs:
            result["profile"] = {
                "billing_specialist_id": bs.billing_specialist_id,
                "employee_id": bs.employee_id,
            }
    return result


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _serialize_full_user(db, user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: AdminUpdateUserRequest, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone

    if user.role == "Doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
        if doctor:
            if payload.department_id is not None:
                doctor.department_id = payload.department_id
            if payload.specialty is not None:
                doctor.specialty = payload.specialty
            if payload.qualifications is not None:
                doctor.qualifications = payload.qualifications
            if payload.bio is not None:
                doctor.bio = payload.bio
            if payload.years_experience is not None:
                doctor.years_experience = payload.years_experience
            if payload.consultation_hours is not None:
                doctor.consultation_hours = payload.consultation_hours
    elif user.role == "Staff" and payload.department_id is not None:
        staff = db.query(StaffMember).filter(StaffMember.user_id == user.id).first()
        if staff:
            staff.department_id = payload.department_id

    db.commit()
    return _serialize_full_user(db, user)


@router.patch("/users/{user_id}/status")
def update_user_status(user_id: int, payload: AdminUserStatusRequest, current_user: User = Depends(require_role("Admin")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = 1 if payload.is_active else 0
    action = "user_reactivated" if payload.is_active else "user_deactivated"
    write_audit_log(db, actor_user_id=current_user.id, action=action, target_user_id=user.id)
    db.commit()
    return {"id": user.id, "is_active": bool(user.is_active)}


@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, payload: AdminUserRoleRequest, current_user: User = Depends(require_role("Admin")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_role = user.role
    user.role = payload.role

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="role_changed",
        target_user_id=user.id,
        details=f"{old_role} -> {payload.role}",
    )
    db.commit()
    db.refresh(user)
    return _serialize_full_user(db, user)


# ---------------- 3.2 Departments ----------------


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    return {"items": [{"department_id": d.department_id, "name": d.name, "description": d.description, "is_active": bool(d.is_active)} for d in departments]}


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreateRequest, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.name == payload.name).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Department name already exists")
    department = Department(name=payload.name, description=payload.description, is_active=1)
    db.add(department)
    db.commit()
    db.refresh(department)
    return {"department_id": department.department_id, "name": department.name, "description": department.description, "is_active": True}


@router.patch("/departments/{department_id}")
def update_department(department_id: int, payload: DepartmentUpdateRequest, db: Session = Depends(get_db)):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if payload.name is not None:
        department.name = payload.name
    if payload.description is not None:
        department.description = payload.description
    db.commit()
    return {"department_id": department.department_id, "name": department.name, "description": department.description, "is_active": bool(department.is_active)}


@router.patch("/departments/{department_id}/status")
def update_department_status(department_id: int, payload: DepartmentStatusRequest, db: Session = Depends(get_db)):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    department.is_active = 1 if payload.is_active else 0
    db.commit()
    return {"department_id": department.department_id, "is_active": bool(department.is_active)}


# ---------------- 3.3 Appointments (system-wide) ----------------


@router.get("/appointments")
def list_all_appointments(
    department_id: int | None = None,
    doctor_id: int | None = None,
    date_: str | None = Query(None, alias="date"),
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment).join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status_:
        query = query.filter(Appointment.status == status_)
    if date_:
        query = query.filter(Appointment.scheduled_at.like(f"{date_}%"))

    items, total = paginate(query.order_by(Appointment.scheduled_at.desc()), page, page_size)
    result = []
    for a in items:
        patient = db.get(Patient, a.patient_id)
        doctor = db.get(Doctor, a.doctor_id)
        result.append(
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "patient_name": patient.user.full_name if patient else None,
                "doctor_id": a.doctor_id,
                "doctor_name": doctor.user.full_name if doctor else None,
                "department_name": doctor.department.name if doctor else None,
                "scheduled_at": a.scheduled_at,
                "status": a.status,
                "reason": a.reason,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


# ---------------- 3.4 Billing (system-wide) ----------------


@router.get("/invoices")
def list_all_invoices(
    patient_id: int | None = None,
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice)
    if patient_id:
        query = query.filter(Invoice.patient_id == patient_id)
    if status_:
        query = query.filter(Invoice.status == status_)
    items, total = paginate(query.order_by(Invoice.created_at.desc()), page, page_size)
    result = []
    for inv in items:
        patient = db.get(Patient, inv.patient_id)
        result.append(
            {
                "invoice_id": inv.invoice_id,
                "patient_id": inv.patient_id,
                "patient_name": patient.user.full_name if patient else None,
                "appointment_id": inv.appointment_id,
                "total_amount_cents": inv.total_amount_cents,
                "status": inv.status,
                "created_at": inv.created_at,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


# ---------------- 3.5 Blog administration ----------------


def _serialize_article(a: BlogArticle) -> dict:
    return {
        "article_id": a.article_id,
        "title": a.title,
        "slug": a.slug,
        "summary": a.summary,
        "body": a.body,
        "author_user_id": a.author_user_id,
        "status": a.status,
        "cover_image_path": a.cover_image_path,
        "published_at": a.published_at,
        "created_at": a.created_at,
    }


@router.get("/blog")
def list_admin_blog(status_: str | None = Query(None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(BlogArticle)
    if status_:
        query = query.filter(BlogArticle.status == status_)
    items, total = paginate(query.order_by(BlogArticle.created_at.desc()), page, page_size)
    return {"items": [_serialize_article(a) for a in items], "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


@router.post("/blog", status_code=status.HTTP_201_CREATED)
async def create_blog_article(
    title: str = Form(...),
    summary: str | None = Form(None),
    body: str = Form(...),
    cover_image: UploadFile | None = File(None),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    article = BlogArticle(
        title=title,
        slug=unique_slug(db, title),
        summary=summary,
        body=body,
        author_user_id=current_user.id,
        status="Draft",
    )
    db.add(article)
    db.flush()

    if cover_image is not None:
        ext = (cover_image.filename or "").rsplit(".", 1)[-1] if "." in (cover_image.filename or "") else "bin"
        filename = f"{article.article_id}_{cover_image.filename}"
        rel_path = await save_upload(cover_image, BLOG_COVERS_DIR, filename, kind="blog")
        article.cover_image_path = rel_path

    db.commit()
    db.refresh(article)
    return _serialize_article(article)


@router.patch("/blog/{article_id}")
async def update_blog_article(
    article_id: int,
    title: str | None = Form(None),
    summary: str | None = Form(None),
    body: str | None = Form(None),
    cover_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    article = db.get(BlogArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if title is not None:
        article.title = title
    if summary is not None:
        article.summary = summary
    if body is not None:
        article.body = body
    if cover_image is not None:
        filename = f"{article.article_id}_{cover_image.filename}"
        rel_path = await save_upload(cover_image, BLOG_COVERS_DIR, filename, kind="blog")
        article.cover_image_path = rel_path

    db.commit()
    return _serialize_article(article)


@router.patch("/blog/{article_id}/publish")
def publish_blog_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(BlogArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    article.status = "Published"
    article.published_at = now_iso()
    db.commit()
    return {"article_id": article.article_id, "status": article.status, "published_at": article.published_at}


@router.patch("/blog/{article_id}/unpublish")
def unpublish_blog_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(BlogArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    article.status = "Draft"
    article.published_at = None
    db.commit()
    return {"article_id": article.article_id, "status": article.status, "published_at": None}


@router.delete("/blog/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(BlogArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    db.delete(article)
    db.commit()
    return None


# ---------------- 3.6 Contact messages ----------------


@router.get("/contact-messages")
def list_contact_messages(status_: str | None = Query(None, alias="status"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(ContactMessage)
    if status_:
        query = query.filter(ContactMessage.status == status_)
    items, total = paginate(query.order_by(ContactMessage.created_at.desc()), page, page_size)
    return {
        "items": [
            {
                "message_id": m.message_id,
                "name": m.name,
                "email": m.email,
                "phone": m.phone,
                "subject": m.subject,
                "message": m.message,
                "status": m.status,
                "created_at": m.created_at,
            }
            for m in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.patch("/contact-messages/{message_id}/status")
def update_contact_message_status(message_id: int, payload: ContactMessageStatusRequest, db: Session = Depends(get_db)):
    message = db.get(ContactMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    message.status = payload.status
    db.commit()
    return {"message_id": message.message_id, "status": message.status}


# ---------------- 3.7 Dashboard & audit ----------------


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    from app.models import AuditLogEntry  # local import avoids unused-at-top clutter

    patient_count = db.query(Patient).count()
    doctor_count = db.query(Doctor).count()
    today = date.today().isoformat()
    appointments_today = db.query(Appointment).filter(Appointment.scheduled_at.like(f"{today}%")).count()
    pending_lab_orders = db.query(LabOrder).filter(LabOrder.status == "Pending").count()
    return {
        "patient_count": patient_count,
        "doctor_count": doctor_count,
        "appointments_today": appointments_today,
        "pending_lab_orders": pending_lab_orders,
    }


@router.get("/audit-log")
def list_audit_log(
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from app.models import AuditLogEntry

    query = db.query(AuditLogEntry)
    if actor_user_id:
        query = query.filter(AuditLogEntry.actor_user_id == actor_user_id)
    if target_user_id:
        query = query.filter(AuditLogEntry.target_user_id == target_user_id)
    items, total = paginate(query.order_by(AuditLogEntry.created_at.desc()), page, page_size)

    result = []
    for entry in items:
        actor = db.get(User, entry.actor_user_id)
        target = db.get(User, entry.target_user_id) if entry.target_user_id else None
        result.append(
            {
                "log_id": entry.log_id,
                "actor_user_id": entry.actor_user_id,
                "actor_name": actor.full_name if actor else None,
                "action": entry.action,
                "target_user_id": entry.target_user_id,
                "target_name": target.full_name if target else None,
                "details": entry.details,
                "created_at": entry.created_at,
            }
        )
    return {"items": result, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages(total, page_size)}


# ---------------- 3.8 Public site content ----------------


def _set_site_content(db: Session, key: str, default: dict, updates: dict) -> dict:
    row = db.get(SiteContent, key)
    current = default.copy()
    if row is not None:
        from app.utils import loads

        current.update(loads(row.value_json) or {})
    for k, v in updates.items():
        if v is not None:
            current[k] = v

    if row is None:
        row = SiteContent(key=key, value_json=dumps(current), updated_at=now_iso())
        db.add(row)
    else:
        row.value_json = dumps(current)
        row.updated_at = now_iso()
    db.commit()
    return current


@router.patch("/site-content/home")
def update_home_content(payload: SiteContentHomeRequest, db: Session = Depends(get_db)):
    from app.routers.public import DEFAULT_HOME

    return _set_site_content(db, "home", DEFAULT_HOME, payload.model_dump())


@router.patch("/site-content/about")
def update_about_content(payload: SiteContentAboutRequest, db: Session = Depends(get_db)):
    from app.routers.public import DEFAULT_ABOUT

    return _set_site_content(db, "about", DEFAULT_ABOUT, payload.model_dump())
