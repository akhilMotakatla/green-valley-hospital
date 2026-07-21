"""SQLAlchemy 2.x models mirroring db/schema.sql exactly (table/column names,
FKs, defaults, and CHECK-style enums via Python enums are enforced at the
application layer since SQLite CHECK constraints aren't expressed via ORM
column types here — the DDL comments in db/schema.sql remain the source of
truth for constraints).

Two schema extensions beyond the original db/schema.sql entity list, both
flagged in docs/api-spec.md §6 and §8 rather than silently added:
  - `vitals` table (STF-4: Staff records patient vitals).
  - `site_content` table (Admin-edited Home/About copy, optional persistence
    alternative to a hardcoded config — chosen here since it's quick).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        # v1.2: BillingSpecialist added as sixth role (BILL-ROLE-1).
        CheckConstraint(
            "role IN ('Admin','Doctor','Patient','Staff','Lab','BillingSpecialist')",
            name="ck_users_role",
        ),
        CheckConstraint("is_active IN (0,1)", name="ck_users_is_active"),
        Index("idx_users_role", "role"),
    )


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("is_active IN (0,1)", name="ck_departments_is_active"),
    )


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    date_of_birth: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String, nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped[User] = relationship("User")


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False
    )
    specialty: Mapped[str] = mapped_column(String, nullable=False)
    qualifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consultation_hours: Mapped[str | None] = mapped_column(String, nullable=True)
    # Nullable filesystem path to the doctor's public profile photo.
    # Set via Admin/Doctor profile edit (plain text path input).
    # Served as a static asset by the frontend dev server / Vite build (VI-IMG-4).
    # Added in v1.1 (Section 6 visual requirements); see docs/api-spec.md §2 and §7.
    profile_photo_path: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("years_experience >= 0", name="ck_doctors_years_experience"),
        Index("idx_doctors_department", "department_id"),
    )

    user: Mapped[User] = relationship("User")
    department: Mapped[Department] = relationship("Department")


class StaffMember(Base):
    __tablename__ = "staff_members"

    staff_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped[User] = relationship("User")
    department: Mapped[Department | None] = relationship("Department")


class LabTechnician(Base):
    __tablename__ = "lab_technicians"

    lab_user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    user: Mapped[User] = relationship("User")


class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    scheduled_at: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Scheduled")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Scheduled','Completed','Cancelled','NoShow')", name="ck_appointments_status"
        ),
        Index("idx_appointments_patient", "patient_id"),
        Index("idx_appointments_doctor", "doctor_id"),
        Index("idx_appointments_status", "status"),
        Index("idx_appointments_scheduled_at", "scheduled_at"),   # Section 8.2.1
        Index("idx_appointments_created_at", "created_at"),       # Section 8.2.1
        # Partial unique index preventing doctor double-booking (AC-APT-2).
        Index(
            "uq_appointments_doctor_slot",
            "doctor_id",
            "scheduled_at",
            unique=True,
            sqlite_where=text("status IN ('Scheduled', 'Completed')"),
        ),
    )

    patient: Mapped[Patient] = relationship("Patient")
    doctor: Mapped[Doctor] = relationship("Doctor")


class VisitNote(Base):
    __tablename__ = "visit_notes"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_visit_notes_patient", "patient_id"),
        Index("idx_visit_notes_doctor", "doctor_id"),
        Index("idx_visit_notes_appointment", "appointment_id"),
        Index("idx_visit_notes_created_at", "created_at"),  # Section 8.2.1
    )


class Prescription(Base):
    __tablename__ = "prescriptions"

    prescription_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    medicines_json: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_prescriptions_patient", "patient_id"),
        Index("idx_prescriptions_doctor", "doctor_id"),
        Index("idx_prescriptions_appointment", "appointment_id"),
        Index("idx_prescriptions_created_at", "created_at"),  # Section 8.2.1
    )


class LabOrder(Base):
    __tablename__ = "lab_orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    lab_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lab_technicians.lab_user_id", ondelete="SET NULL"), nullable=True
    )
    test_type: Mapped[str] = mapped_column(String, nullable=False)
    test_subtype: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("test_type IN ('Lab','XRay','Scan')", name="ck_lab_orders_test_type"),
        CheckConstraint("status IN ('Pending','InProgress','Completed')", name="ck_lab_orders_status"),
        Index("idx_lab_orders_patient", "patient_id"),
        Index("idx_lab_orders_doctor", "doctor_id"),
        Index("idx_lab_orders_lab_user", "lab_user_id"),
        Index("idx_lab_orders_status", "status"),
        Index("idx_lab_orders_created_at", "created_at"),  # Section 8.2.1
    )


class LabResult(Base):
    __tablename__ = "lab_results"

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lab_orders.order_id", ondelete="CASCADE"), nullable=False
    )
    result_data: Mapped[str] = mapped_column(Text, nullable=False)
    file_attachment_path: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    recorded_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    is_finalized: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finalized_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_lab_results_version"),
        CheckConstraint("is_finalized IN (0,1)", name="ck_lab_results_is_finalized"),
        UniqueConstraint("order_id", "version", name="uq_lab_results_order_version"),
        Index("idx_lab_results_order", "order_id"),
        Index("idx_lab_results_created_at", "created_at"),  # Section 8.2.1
    )


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True
    )
    line_items_json: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Pending")
    # v1.2 (Section 8.4.2): boolean flag for insurance claim filing. 0 = no claim, 1 = claim filed.
    has_insurance_claim: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Batch 2 (OI-7): set server-side when status transitions to 'Paid'; used by revenue analytics.
    paid_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("total_amount_cents >= 0", name="ck_invoices_total_amount_cents"),
        CheckConstraint("status IN ('Pending','Paid','Waived')", name="ck_invoices_status"),
        CheckConstraint("has_insurance_claim IN (0,1)", name="ck_invoices_has_insurance_claim"),
        Index("idx_invoices_patient", "patient_id"),
        Index("idx_invoices_appointment", "appointment_id"),
        Index("idx_invoices_status", "status"),
        Index("idx_invoices_created_at", "created_at"),
        Index("idx_invoices_has_insurance_claim", "has_insurance_claim"),
    )


class BlogArticle(Base):
    __tablename__ = "blog_articles"

    article_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="Draft")
    cover_image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    published_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("status IN ('Draft','Published')", name="ck_blog_articles_status"),
        Index("idx_blog_articles_status", "status"),
        Index("idx_blog_articles_slug", "slug"),
        Index("idx_blog_articles_published_at", "published_at"),  # Section 8.2.1
    )


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="New")
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("status IN ('New','Reviewed','Resolved')", name="ck_contact_messages_status"),
        Index("idx_contact_messages_status", "status"),
        Index("idx_contact_messages_created_at", "created_at"),  # Section 8.2.1
    )


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_audit_log_actor", "actor_user_id"),
        Index("idx_audit_log_target", "target_user_id"),
    )


# ============================================================
# Schema extensions (flagged in docs/api-spec.md §6, §7, §8)
# ============================================================


class Vitals(Base):
    """Patient vitals recorded by Staff — resolves pre-existing STF-4 schema gap.
    Schema aligned with Batch 2 db/schema.sql (REQ-04) which introduced separate
    systolic_bp / diastolic_bp columns and the vital_id PK name.
    """

    __tablename__ = "vitals"

    vital_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True
    )
    recorded_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pulse_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_vitals_patient", "patient_id"),
        Index("idx_vitals_appointment", "appointment_id"),
        Index("idx_vitals_recorded_at", "recorded_at"),
    )


class SiteContent(Base):
    """Optional key-value store for Admin-edited Home/About copy
    (docs/api-spec.md §8 — chosen over a hardcoded config file since it's
    a quick addition and gives Admin real persistence for PATCH endpoints).
    """

    __tablename__ = "site_content"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)


# ============================================================
# Section 8 additions (v1.2 — BillingSpecialist role, email notifications)
# ============================================================


class BillingSpecialist(Base):
    """1:1 with users where role = 'BillingSpecialist'.
    Added in v1.2 (BILL-ROLE-3 / docs/api-spec.md §9).
    employee_id is an optional internal HR reference (nullable).
    """

    __tablename__ = "billing_specialists"

    billing_specialist_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    employee_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    user: Mapped[User] = relationship("User")


class EmailNotification(Base):
    """Records every invoice-status-change notification and manual resend.
    Delivery is a local file written to uploads/email_log/; this row is the
    audit record.  Added in v1.2 (Section 8.3 / docs/api-spec.md §9).
    """

    __tablename__ = "email_notifications"

    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[str] = mapped_column(String, nullable=False)
    trigger_event: Mapped[str] = mapped_column(String, nullable=False)
    related_invoice_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("invoices.invoice_id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "trigger_event IN ('invoice_status_change','manual_resend')",
            name="ck_email_notifications_trigger_event",
        ),
        CheckConstraint(
            "status IN ('Queued','Sent','Failed')",
            name="ck_email_notifications_status",
        ),
        Index("idx_email_notifications_recipient", "recipient_user_id"),
        Index("idx_email_notifications_sent_at", "sent_at"),
    )

    recipient: Mapped[User] = relationship("User")


# ============================================================
# Batch 2 models (2026-07-20 — REQ-01 through REQ-12)
# db/schema.sql Batch 2 block is the canonical DDL source.
# ============================================================


class DoctorAvailabilitySchedule(Base):
    """REQ-01: Weekly recurring availability windows per doctor per day-of-week."""
    __tablename__ = "doctor_availability_schedules"

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[str] = mapped_column(String, nullable=False)    # HH:MM
    end_time: Mapped[str] = mapped_column(String, nullable=False)      # HH:MM
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_das_dow"),
        CheckConstraint("is_active IN (0,1)", name="ck_das_is_active"),
        UniqueConstraint("doctor_id", "day_of_week", "start_time", name="uq_das_doctor_dow_start"),
        Index("idx_avail_schedules_doctor", "doctor_id"),
    )

    doctor: Mapped[Doctor] = relationship("Doctor")


class DoctorSlotConfig(Base):
    """REQ-01: Slot duration configuration — one row per doctor (default 30 min)."""
    __tablename__ = "doctor_slot_configs"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint(
            "slot_duration_minutes IN (10,15,20,30,45,60)", name="ck_dsc_slot_duration"
        ),
    )

    doctor: Mapped[Doctor] = relationship("Doctor")


class DoctorAvailabilityBlock(Base):
    """REQ-01: One-off date blocks overriding weekly schedule.
    start_time=NULL + end_time=NULL = full-day block.
    """
    __tablename__ = "doctor_availability_blocks"

    block_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False
    )
    block_date: Mapped[str] = mapped_column(String, nullable=False)     # YYYY-MM-DD
    start_time: Mapped[str | None] = mapped_column(String, nullable=True)   # HH:MM or NULL
    end_time: Mapped[str | None] = mapped_column(String, nullable=True)     # HH:MM or NULL
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_avail_blocks_doctor", "doctor_id"),
        Index("idx_avail_blocks_date", "block_date"),
    )

    doctor: Mapped[Doctor] = relationship("Doctor")


class Notification(Base):
    """REQ-02: In-app notification inbox per user."""
    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("is_read IN (0,1)", name="ck_notifications_is_read"),
        Index("idx_notifications_recipient_read", "recipient_user_id", "is_read"),
        Index("idx_notifications_created_at", "created_at"),
    )

    recipient: Mapped[User] = relationship("User")


class NotificationSchedule(Base):
    """REQ-02: Deferred notification triggers (poll-on-login pattern, OI-2)."""
    __tablename__ = "notification_schedules"

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=True
    )
    survey_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # soft FK to satisfaction_surveys
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    trigger_at: Mapped[str] = mapped_column(String, nullable=False)   # ISO 8601 UTC
    is_fired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('appointment_reminder','survey_available')",
            name="ck_ns_trigger_type",
        ),
        CheckConstraint("is_fired IN (0,1)", name="ck_ns_is_fired"),
        Index("idx_notif_schedules_poll", "trigger_at", "is_fired"),
    )


class IntakeForm(Base):
    """REQ-03: Pre-visit intake forms. Auto-created (empty) on appointment booking."""
    __tablename__ = "intake_forms"

    intake_form_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptom_duration: Mapped[str | None] = mapped_column(String, nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_medications: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_scale: Mapped[int | None] = mapped_column(Integer, nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("pain_scale BETWEEN 1 AND 10", name="ck_intake_pain_scale"),
        Index("idx_intake_forms_appointment", "appointment_id"),
        Index("idx_intake_forms_patient", "patient_id"),
    )


class WaitlistEntry(Base):
    """REQ-09: Per-doctor-per-date waitlist entries (OI-12)."""
    __tablename__ = "waitlist_entries"

    entry_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False
    )
    preferred_date: Mapped[str] = mapped_column(String, nullable=False)    # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String, nullable=False, default="Waiting")
    notified_at: Mapped[str | None] = mapped_column(String, nullable=True)
    confirmation_deadline: Mapped[str | None] = mapped_column(String, nullable=True)
    held_slot_time: Mapped[str | None] = mapped_column(String, nullable=True)  # HH:MM
    removed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Waiting','Notified','Confirmed','Expired','Removed')",
            name="ck_we_status",
        ),
        Index("idx_waitlist_doctor_date_queue", "doctor_id", "preferred_date", "status", "created_at"),
        Index("idx_waitlist_patient", "patient_id"),
    )

    patient: Mapped[Patient] = relationship("Patient")
    doctor: Mapped[Doctor] = relationship("Doctor")


class SystemConfig(Base):
    """System-wide key-value configuration store."""
    __tablename__ = "system_config"

    config_key: Mapped[str] = mapped_column(String, primary_key=True)
    config_value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)


class DischargeSummary(Base):
    """REQ-10: Discharge summaries. 1:1 with completed appointments."""
    __tablename__ = "discharge_summaries"

    summary_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="RESTRICT"),
        nullable=False, unique=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    key_findings: Mapped[str] = mapped_column(Text, nullable=False)
    patient_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    medication_reminders: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_discharge_patient", "patient_id"),
        Index("idx_discharge_doctor", "doctor_id"),
    )


class SatisfactionSurvey(Base):
    """REQ-11: Post-visit satisfaction surveys. 1:1 with completed appointments."""
    __tablename__ = "satisfaction_surveys"

    survey_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="RESTRICT"),
        nullable=False, unique=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    trigger_after: Mapped[str] = mapped_column(String, nullable=False)   # ISO 8601
    expires_at: Mapped[str] = mapped_column(String, nullable=False)      # ISO 8601
    notification_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_at: Mapped[str | None] = mapped_column(String, nullable=True)
    doctor_star_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_star_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_comment_removed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("notification_sent IN (0,1)", name="ck_ss_notification_sent"),
        CheckConstraint("is_comment_removed IN (0,1)", name="ck_ss_comment_removed"),
        Index("idx_surveys_patient", "patient_id"),
        Index("idx_surveys_doctor", "doctor_id"),
        Index("idx_surveys_poll", "patient_id", "notification_sent", "submitted_at"),
    )


class CorporatePackage(Base):
    """REQ-12: B2B health package tiers."""
    __tablename__ = "corporate_packages"

    package_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tier_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    included_services_json: Mapped[str] = mapped_column(Text, nullable=False)
    price_range_display: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("is_active IN (0,1)", name="ck_cp_is_active"),
        Index("idx_corp_packages_active", "is_active", "tier_order"),
    )


class CorporateInquiry(Base):
    """REQ-12: Corporate inquiry pipeline."""
    __tablename__ = "corporate_inquiries"

    inquiry_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    contact_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    package_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("corporate_packages.package_id", ondelete="SET NULL"), nullable=True
    )
    preferred_schedule: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="New")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deal_value_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint(
            "status IN ('New','Contacted','ProposalSent','ClosedWon','ClosedLost')",
            name="ck_ci_status",
        ),
        Index("idx_corp_inquiries_status", "status"),
        Index("idx_corp_inquiries_created_at", "created_at"),
    )


class DepartmentSymptomTag(Base):
    """REQ-07: Department symptom/condition tags for public search."""
    __tablename__ = "department_symptom_tags"

    tag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False
    )
    tag_text: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        Index("idx_symptom_tags_department", "department_id"),
        Index("idx_symptom_tags_text", "tag_text"),
    )

    department: Mapped[Department] = relationship("Department")


class Referral(Base):
    """REQ-05: Inter-department referrals."""
    __tablename__ = "referrals"

    referral_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referring_doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="RESTRICT"), nullable=False
    )
    receiving_department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id", ondelete="RESTRICT"), nullable=False
    )
    receiving_doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("doctors.doctor_id", ondelete="SET NULL"), nullable=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Pending")
    receiving_doctor_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    referred_appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    __table_args__ = (
        CheckConstraint("urgency IN ('Routine','Urgent')", name="ck_ref_urgency"),
        CheckConstraint(
            "status IN ('Pending','Accepted','Declined','AppointmentBooked','Completed')",
            name="ck_ref_status",
        ),
        Index("idx_referrals_patient", "patient_id"),
        Index("idx_referrals_referring", "referring_doctor_id"),
        Index("idx_referrals_recv_dept", "receiving_department_id"),
        Index("idx_referrals_status", "status"),
        Index("idx_referrals_dept_queue", "receiving_department_id", "status", "urgency", "created_at"),
    )
