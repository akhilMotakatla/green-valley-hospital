"""Pydantic v2 request schemas. Field names match docs/api-spec.md /
db/schema.sql exactly (snake_case, 1:1 pass-through). Response bodies are
built as plain dicts in the routers (also snake_case) to keep the shape
exactly as specified without duplicating every read-model as a schema.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.security import validate_password_policy


# ---------------- Auth ----------------


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    date_of_birth: str

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if not validate_password_policy(v):
            raise ValueError("Password must be at least 8 characters and include a letter and a number")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------------- Admin ----------------


class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    # v1.2: BillingSpecialist added as a valid role for Admin-created accounts (BILL-ROLE-1).
    role: Literal["Doctor", "Staff", "Lab", "Admin", "BillingSpecialist"]
    full_name: str
    phone: str | None = None
    department_id: int | None = None
    specialty: str | None = None
    qualifications: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    consultation_hours: str | None = None
    # BillingSpecialist-specific optional field
    employee_id: str | None = None

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if not validate_password_policy(v):
            raise ValueError("Password must be at least 8 characters and include a letter and a number")
        return v


class AdminUpdateUserRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    department_id: int | None = None
    specialty: str | None = None
    qualifications: str | None = None
    bio: str | None = None
    years_experience: int | None = None
    consultation_hours: str | None = None


class AdminUserStatusRequest(BaseModel):
    is_active: bool


class AdminUserRoleRequest(BaseModel):
    role: Literal["Admin", "Doctor", "Patient", "Staff", "Lab", "BillingSpecialist"]
    department_id: int | None = None


class DepartmentCreateRequest(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentStatusRequest(BaseModel):
    is_active: bool


class BlogCreateRequest(BaseModel):
    title: str
    summary: str | None = None
    body: str


class BlogUpdateRequest(BaseModel):
    title: str | None = None
    summary: str | None = None
    body: str | None = None


class ContactMessageStatusRequest(BaseModel):
    status: Literal["Reviewed", "Resolved"]


class SiteContentHomeRequest(BaseModel):
    tagline: str | None = None
    highlights: list[str] | None = None


class SiteContentAboutRequest(BaseModel):
    mission: str | None = None
    history: str | None = None
    facilities: str | None = None
    accreditations: str | None = None


# ---------------- Doctor ----------------


class DoctorUpdateMeRequest(BaseModel):
    bio: str | None = None
    qualifications: str | None = None
    consultation_hours: str | None = None
    # v1.1 (Section 6 visual requirements) — doctor self-updates their own photo path
    profile_photo_path: str | None = None


class AppointmentStatusRequest(BaseModel):
    status: Literal["Completed", "NoShow", "Cancelled"]


class VisitNoteCreateRequest(BaseModel):
    diagnosis: str | None = None
    notes: str


class Medicine(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str


class PrescriptionCreateRequest(BaseModel):
    medicines: list[Medicine]
    instructions: str | None = None


class LabOrderCreateRequest(BaseModel):
    test_type: Literal["Lab", "XRay", "Scan"]
    test_subtype: str | None = None
    notes: str | None = None
    appointment_id: int | None = None


# ---------------- Patient ----------------


class PatientUpdateMeRequest(BaseModel):
    phone: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    date_of_birth: str | None = None


class BookAppointmentRequest(BaseModel):
    doctor_id: int
    scheduled_at: str
    reason: str | None = None


# ---------------- Staff ----------------


class StaffPatientCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: str
    gender: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class StaffAppointmentCreateRequest(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_at: str
    reason: str | None = None


class StaffAppointmentUpdateRequest(BaseModel):
    scheduled_at: str | None = None
    doctor_id: int | None = None
    status: Literal["Scheduled", "Completed", "Cancelled", "NoShow"] | None = None
    reason: str | None = None


class VitalsCreateRequest(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_pressure: str | None = None
    temperature_c: float | None = None
    pulse_bpm: int | None = None
    recorded_for_appointment_id: int | None = None


# ---------------- Lab ----------------


class LabOrderStatusRequest(BaseModel):
    status: Literal["InProgress", "Completed"]


# ---------------- Billing Specialist (v1.2 / Section 9) ----------------


class LineItem(BaseModel):
    description: str
    amount_cents: int


class BillingInvoiceCreateRequest(BaseModel):
    patient_id: int
    appointment_id: int | None = None
    line_items: list[LineItem]
    total_amount_cents: int
    has_insurance_claim: int = 0


class BillingInvoicePatchRequest(BaseModel):
    status: Literal["Pending", "Paid", "Waived"] | None = None
    has_insurance_claim: int | None = None
    line_items: list[LineItem] | None = None
    total_amount_cents: int | None = None
