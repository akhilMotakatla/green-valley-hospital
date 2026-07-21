from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BlogArticle, ContactMessage, Department, Doctor, SiteContent, User
from app.services.notification_service import create_notifications
from app.utils import loads, paginate, total_pages
from sqlalchemy import asc

router = APIRouter(prefix="/public", tags=["public"])


DEFAULT_HOME = {
    "tagline": "Compassionate Care, Advanced Medicine.",
    "highlights": [
        "24/7 Emergency Care",
        "Board-certified specialists across 10+ departments",
        "Modern diagnostic and lab facilities",
    ],
}

DEFAULT_ABOUT = {
    "mission": "To provide accessible, high-quality healthcare to every member of our community.",
    "history": "Green Valley Hospital has served the region for over two decades.",
    "facilities": "Emergency department, inpatient wards, diagnostic labs, outpatient clinics.",
    "accreditations": "Nationally accredited healthcare facility.",
}


def _get_site_content(db: Session, key: str, default: dict) -> dict:
    row = db.get(SiteContent, key)
    if row is None:
        return default
    return loads(row.value_json)


@router.get("/home")
def get_home(db: Session = Depends(get_db)):
    content = _get_site_content(db, "home", DEFAULT_HOME)
    # Featured departments: show up to 9 (three full rows of 3 in the home page
    # grid) so the "Our Departments" section reads as full once more departments
    # are seeded, rather than capping at the historical 4.
    departments = db.query(Department).filter(Department.is_active == 1).limit(9).all()

    # Build featured_departments with first_doctor per department (VI-HOME-5 / api-spec.md §2).
    # first_doctor = lowest doctor_id active doctor in that department, or null.
    featured_departments = []
    for d in departments:
        first_doc = (
            db.query(Doctor)
            .join(User, User.id == Doctor.user_id)
            .filter(Doctor.department_id == d.department_id, User.is_active == 1)
            .order_by(asc(Doctor.doctor_id))
            .first()
        )
        first_doctor = None
        if first_doc is not None:
            first_doctor = {
                "doctor_id": first_doc.doctor_id,
                "full_name": first_doc.user.full_name,
                "specialty": first_doc.specialty,
                "profile_photo_path": first_doc.profile_photo_path,
            }
        featured_departments.append({
            "department_id": d.department_id,
            "name": d.name,
            "description": d.description,
            "first_doctor": first_doctor,
        })

    # recent_articles: up to 3 most recently published articles (VI-HOME-7 / api-spec.md §2).
    recent_qs = (
        db.query(BlogArticle)
        .filter(BlogArticle.status == "Published")
        .order_by(BlogArticle.published_at.desc())
        .limit(3)
        .all()
    )
    recent_articles = [
        {
            "article_id": a.article_id,
            "title": a.title,
            "slug": a.slug,
            "summary": a.summary,
            "author_name": _author_name(db, a.author_user_id),
            "published_at": a.published_at,
            "cover_image_path": a.cover_image_path,
        }
        for a in recent_qs
    ]

    return {
        "tagline": content.get("tagline"),
        "highlights": content.get("highlights", []),
        "featured_departments": featured_departments,
        "recent_articles": recent_articles,
    }


@router.get("/about")
def get_about(db: Session = Depends(get_db)):
    return _get_site_content(db, "about", DEFAULT_ABOUT)


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).filter(Department.is_active == 1).all()
    return {"items": [{"department_id": d.department_id, "name": d.name, "description": d.description} for d in departments]}


@router.get("/departments/{department_id}/doctors")
def list_department_doctors(
    department_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    query = (
        db.query(Doctor)
        .join(User, User.id == Doctor.user_id)
        .filter(Doctor.department_id == department_id, User.is_active == 1)
    )
    # v1.2 (Section 8.2.2): paginated response per convention envelope.
    # Response shape from v1.1 (VI-DDOC-1): {department: {...}, items: [...]}
    # retained; pagination fields added at top level alongside 'department'.
    items, total = paginate(query, page, page_size)
    return {
        "department": {
            "department_id": department.department_id,
            "name": department.name,
            "description": department.description,
        },
        "items": [
            {
                "doctor_id": d.doctor_id,
                "full_name": d.user.full_name,
                "specialty": d.specialty,
                "qualifications": d.qualifications,
                "years_experience": d.years_experience,
                "profile_photo_path": d.profile_photo_path,
            }
            for d in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


@router.get("/doctors/{doctor_id}")
def get_doctor_public_profile(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return {
        "doctor_id": doctor.doctor_id,
        "full_name": doctor.user.full_name,
        "specialty": doctor.specialty,
        "department": {"department_id": doctor.department.department_id, "name": doctor.department.name},
        "qualifications": doctor.qualifications,
        "bio": doctor.bio,
        "years_experience": doctor.years_experience,
        "consultation_hours": doctor.consultation_hours,
        "profile_photo_path": doctor.profile_photo_path,
    }


@router.get("/contact-info")
def get_contact_info():
    return {
        "address": "123 Green Valley Road, Springfield",
        "general_phone": "+1-555-0100",
        "emergency_phone": "+1-555-0911",
    }


@router.post("/contact-messages", status_code=status.HTTP_201_CREATED)
def submit_contact_message(payload: dict, db: Session = Depends(get_db)):
    # Validate required fields manually so a missing field produces 422 and
    # no row is created (AC-CONTACT-2), matching the api-spec's raw shape.
    required = ["name", "email", "subject", "message"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required field(s): {', '.join(missing)}",
        )

    message = ContactMessage(
        name=payload["name"],
        email=payload["email"],
        phone=payload.get("phone"),
        subject=payload["subject"],
        message=payload["message"],
        status="New",
    )
    db.add(message)
    db.flush()  # get message_id before notification fan-out

    # REQ-02: Fan-out to all active Admin and Staff users (OI-11)
    admin_staff = db.query(User).filter(User.role.in_(["Admin", "Staff"]), User.is_active == 1).all()
    contact_events: list[dict] = [
        {
            "recipient_user_id": u.id,
            "event_type": "contact_form_received",
            "title": "New Contact Message",
            "body": (
                f"New message from {message.name} ({message.email}): {message.subject}"
            ),
            "related_entity_type": "contact_message",
            "related_entity_id": message.message_id,
        }
        for u in admin_staff
    ]
    create_notifications(db, contact_events)

    db.commit()
    db.refresh(message)
    return {"message_id": message.message_id, "status": message.status, "created_at": message.created_at}


@router.get("/blog")
def list_public_blog(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(BlogArticle).filter(BlogArticle.status == "Published").order_by(BlogArticle.published_at.desc())
    items, total = paginate(query, page, page_size)
    return {
        "items": [
            {
                "article_id": a.article_id,
                "title": a.title,
                "slug": a.slug,
                "summary": a.summary,
                "author_name": a.author_user_id and _author_name(db, a.author_user_id),
                "cover_image_path": a.cover_image_path,
                "published_at": a.published_at,
            }
            for a in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages(total, page_size),
    }


def _author_name(db: Session, user_id: int) -> str | None:
    user = db.get(User, user_id)
    return user.full_name if user else None


@router.get("/blog/{slug}")
def get_public_blog_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(BlogArticle).filter(BlogArticle.slug == slug, BlogArticle.status == "Published").first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return {
        "article_id": article.article_id,
        "title": article.title,
        "slug": article.slug,
        "body": article.body,
        "author_name": _author_name(db, article.author_user_id),
        "cover_image_path": article.cover_image_path,
        "published_at": article.published_at,
    }
