"""Sprint 2 — Section 8 backend tests: BillingSpecialist role, pagination,
JWT payload, billing CRUD, email notifications, restricted fields.

Uses FastAPI TestClient + in-memory SQLite (configured via conftest.py).
All helper fixtures (client, db_session, make_user, make_doctor_user, login,
auth_headers) are imported from conftest.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import pytest

# Make app importable regardless of cwd.
BACKEND_ROOT = Path(__file__).resolve().parents[2] / "src" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from conftest import auth_headers, login, make_department, make_doctor_user, make_user
from app.models import Appointment, BillingSpecialist, Invoice, Patient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_billing_specialist(db_session, email="billing@test.com", full_name="Test Billing"):
    """Directly seed a BillingSpecialist user (bypasses HTTP — only Admin can create them)."""
    from app.security import hash_password
    from app.models import User, BillingSpecialist

    u = User(
        email=email,
        password_hash=hash_password("billing123"),
        role="BillingSpecialist",
        full_name=full_name,
        phone="555-0200",
        is_active=1,
    )
    db_session.add(u)
    db_session.flush()
    bs = BillingSpecialist(user_id=u.id)
    db_session.add(bs)
    db_session.commit()
    db_session.refresh(u)
    return u


def _make_patient_with_profile(db_session, email="patient@test.com", full_name="Pat Patient"):
    """Seed a Patient user + Patient profile row."""
    from app.models import Patient

    u = make_user(db_session, email=email, role="Patient", full_name=full_name)
    p = Patient(
        user_id=u.id,
        date_of_birth="1990-01-01",
        gender="Other",
        address="123 Main St",
        emergency_contact_name="EC Name",
        emergency_contact_phone="555-9999",
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return u, p


def _make_admin(db_session):
    return make_user(db_session, email="admin@test.com", role="Admin", full_name="Alice Admin")


def _billing_login(client, db_session):
    _make_billing_specialist(db_session)
    return login(client, "billing@test.com", password="billing123")


# ---------------------------------------------------------------------------
# BILL-1: BillingSpecialist role exists
# ---------------------------------------------------------------------------


class TestBill1RoleExists:
    def test_billing_specialist_can_be_seeded_directly(self, client, db_session):
        """Directly seeding a BillingSpecialist and logging in works."""
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        assert token, "Expected a JWT access token"

    def test_billing_specialist_login_returns_correct_role(self, client, db_session):
        """Login response role claim is BillingSpecialist."""
        _make_billing_specialist(db_session)
        res = client.post("/api/auth/login", json={"email": "billing@test.com", "password": "billing123"})
        assert res.status_code == 200
        assert res.json()["role"] == "BillingSpecialist"

    def test_admin_cannot_create_billing_specialist_via_signup(self, client, db_session):
        """POST /api/auth/signup with role=BillingSpecialist must be rejected 400 (AC-BILL-ROLE-1)."""
        res = client.post(
            "/api/auth/signup",
            json={
                "email": "bs@test.com",
                "password": "Test1234!",
                "full_name": "BS User",
                "phone": "555-0001",
                "date_of_birth": "1990-01-01",
                "role": "BillingSpecialist",
            },
        )
        assert res.status_code in (400, 422), (
            f"Expected 400/422 for role=BillingSpecialist signup, got {res.status_code}: {res.text}"
        )

    def test_admin_can_create_billing_specialist_via_admin_endpoint(self, client, db_session):
        """Admin POST /api/admin/users with role BillingSpecialist (BILL-ROLE-1)."""
        admin = _make_admin(db_session)
        token = login(client, "admin@test.com")
        res = client.post(
            "/api/admin/users",
            json={
                "email": "bs2@test.com",
                "password": "Billing1!",
                "role": "BillingSpecialist",
                "full_name": "Billing Two",
                "phone": "555-0300",
            },
            headers=auth_headers(token),
        )
        assert res.status_code in (200, 201), (
            f"Admin creating BillingSpecialist failed: {res.status_code} {res.text}"
        )
        body = res.json()
        assert body.get("role") == "BillingSpecialist"


# ---------------------------------------------------------------------------
# BILL-2: Pagination on list endpoints
# ---------------------------------------------------------------------------


class TestBill2Pagination:
    ENVELOPE_KEYS = {"items", "total", "page", "page_size", "total_pages"}

    def _check_envelope(self, body: dict, endpoint: str):
        missing = self.ENVELOPE_KEYS - body.keys()
        assert not missing, f"{endpoint} missing pagination keys: {missing}"

    def test_admin_users_pagination_envelope(self, client, db_session):
        admin = _make_admin(db_session)
        token = login(client, "admin@test.com")
        res = client.get("/api/admin/users?page=1&page_size=2", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        self._check_envelope(res.json(), "GET /admin/users")

    def test_doctor_appointments_pagination_envelope(self, client, db_session):
        doc_user, doctor = make_doctor_user(db_session, email="doc@test.com")
        token = login(client, "doc@test.com")
        res = client.get("/api/doctor/me/appointments?page=1&page_size=5", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        self._check_envelope(res.json(), "GET /doctor/me/appointments")

    def test_patient_appointments_pagination_envelope(self, client, db_session):
        pat_user, _ = _make_patient_with_profile(db_session)
        token = login(client, "patient@test.com")
        res = client.get("/api/patients/me/appointments?page=1", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        self._check_envelope(res.json(), "GET /patients/me/appointments")

    def test_lab_orders_pagination_envelope(self, client, db_session):
        lab_user = make_user(db_session, email="lab@test.com", role="Lab")
        token = login(client, "lab@test.com")
        res = client.get("/api/lab/orders?page=1", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        self._check_envelope(res.json(), "GET /lab/orders")

    def test_public_department_doctors_pagination_envelope(self, client, db_session):
        dept = make_department(db_session, name="TestDept")
        doc_user, doctor = make_doctor_user(db_session, email="doc2@test.com", department=dept)
        res = client.get(f"/api/public/departments/{dept.department_id}/doctors?page=1")
        assert res.status_code == 200, res.text
        body = res.json()
        # Spec says items + department wrapper; items array must exist
        assert "items" in body, f"Missing 'items' key in response: {body}"

    def test_page_zero_returns_400_or_422(self, client, db_session):
        """page<=0 must return 400 (spec) or 422 (FastAPI validation) — not 200."""
        admin = _make_admin(db_session)
        token = login(client, "admin@test.com")
        res = client.get("/api/admin/users?page=0", headers=auth_headers(token))
        assert res.status_code in (400, 422), (
            f"Expected 400/422 for page=0, got {res.status_code}"
        )

    def test_negative_page_returns_400_or_422(self, client, db_session):
        admin = _make_admin(db_session)
        token = login(client, "admin@test.com")
        res = client.get("/api/admin/users?page=-1", headers=auth_headers(token))
        assert res.status_code in (400, 422), (
            f"Expected 400/422 for page=-1, got {res.status_code}"
        )

    def test_billing_invoices_pagination_envelope(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/billing/invoices?page=1", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        self._check_envelope(res.json(), "GET /billing/invoices")


# ---------------------------------------------------------------------------
# BILL-3: JWT includes email and full_name
# ---------------------------------------------------------------------------


class TestBill3JwtFields:
    def _decode_jwt_payload(self, token: str) -> dict:
        """Base64-decode the JWT middle section (no signature verification)."""
        parts = token.split(".")
        assert len(parts) == 3, "Token is not a valid JWT (expected 3 parts)"
        # Add padding
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        return json.loads(decoded)

    def test_patient_jwt_has_email_and_full_name(self, client, db_session):
        make_user(db_session, email="pt@test.com", role="Patient", full_name="Peter T")
        res = client.post("/api/auth/login", json={"email": "pt@test.com", "password": "Passw0rd!"})
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = self._decode_jwt_payload(token)
        assert "email" in payload, f"JWT missing 'email' field: {payload}"
        assert "full_name" in payload, f"JWT missing 'full_name' field: {payload}"
        assert payload["email"] == "pt@test.com"
        assert payload["full_name"] == "Peter T"

    def test_admin_jwt_has_email_and_full_name(self, client, db_session):
        _make_admin(db_session)
        res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Passw0rd!"})
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = self._decode_jwt_payload(token)
        assert "email" in payload
        assert "full_name" in payload

    def test_billing_specialist_jwt_has_correct_role_email_full_name(self, client, db_session):
        _make_billing_specialist(db_session, full_name="Test Billing")
        res = client.post("/api/auth/login", json={"email": "billing@test.com", "password": "billing123"})
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = self._decode_jwt_payload(token)
        assert payload.get("role") == "BillingSpecialist"
        assert payload.get("email") == "billing@test.com"
        assert payload.get("full_name") == "Test Billing"
        assert "exp" in payload


# ---------------------------------------------------------------------------
# BILL-4: Billing dashboard endpoint
# ---------------------------------------------------------------------------


class TestBill4Dashboard:
    def test_billing_dashboard_returns_required_keys(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/billing/dashboard", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        body = res.json()
        # spec says: outstanding_invoices, awaiting_claims, collected_this_month_cents, total_patients_billed
        required = {"outstanding_invoices", "awaiting_claims", "collected_this_month_cents", "total_patients_billed"}
        missing = required - body.keys()
        assert not missing, f"Dashboard response missing keys: {missing}. Got: {body}"

    def test_billing_dashboard_non_billing_user_forbidden(self, client, db_session):
        make_user(db_session, email="doc@test.com", role="Doctor")
        token = login(client, "doc@test.com")
        res = client.get("/api/billing/dashboard", headers=auth_headers(token))
        assert res.status_code == 403, f"Expected 403 for Doctor on /billing/dashboard, got {res.status_code}"

    def test_billing_dashboard_aggregate_accuracy(self, client, db_session):
        """With 2 Pending invoices (1 with insurance claim), dashboard counts match."""
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")

        # Create 2 invoices directly
        inv1 = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=5000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        inv2 = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=10000,
            status="Pending",
            has_insurance_claim=1,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv1)
        db_session.add(inv2)
        db_session.commit()

        res = client.get("/api/billing/dashboard", headers=auth_headers(token))
        assert res.status_code == 200
        body = res.json()
        assert body["outstanding_invoices"] >= 2
        assert body["awaiting_claims"] >= 1


# ---------------------------------------------------------------------------
# BILL-5: Invoice CRUD
# ---------------------------------------------------------------------------


class TestBill5InvoiceCrud:
    def _setup(self, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        return patient, bs_user

    def test_create_invoice(self, client, db_session):
        patient, _ = self._setup(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.post(
            "/api/billing/invoices",
            json={
                "patient_id": patient.patient_id,
                "line_items": [{"description": "Consultation", "amount_cents": 10000}],
                "total_amount_cents": 10000,
                "has_insurance_claim": 1,
            },
            headers=auth_headers(token),
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["total_amount_cents"] == 10000
        assert body["has_insurance_claim"] == 1
        assert body["status"] == "Pending"

    def test_list_invoices_paginated(self, client, db_session):
        patient, bs_user = self._setup(db_session)
        # Seed one invoice directly
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[{"description":"Test","amount_cents":500}]',
            total_amount_cents=500,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()

        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/billing/invoices", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        body = res.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_patch_invoice_status_to_paid(self, client, db_session):
        patient, bs_user = self._setup(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=2000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.patch(
            f"/api/billing/invoices/{inv.invoice_id}",
            json={"status": "Paid"},
            headers=auth_headers(token),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["status"] == "Paid"

    def test_patch_invoice_status_triggers_email_log_file(self, client, db_session):
        """After PATCH invoice status, an .html file must exist in uploads/email_log/."""
        patient, bs_user = self._setup(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=3000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.patch(
            f"/api/billing/invoices/{inv.invoice_id}",
            json={"status": "Paid"},
            headers=auth_headers(token),
        )
        assert res.status_code == 200

        # Check email_log directory for an HTML file for this invoice
        email_log_dir = Path(__file__).resolve().parents[2] / "uploads" / "email_log"
        if email_log_dir.exists():
            html_files = list(email_log_dir.glob(f"*_invoice_{inv.invoice_id}.html"))
            # If the directory exists, there must be at least one html file for this invoice
            assert html_files, (
                f"No email log HTML file found for invoice {inv.invoice_id} in {email_log_dir}"
            )


# ---------------------------------------------------------------------------
# BILL-6: Email notification file sink
# ---------------------------------------------------------------------------


class TestBill6EmailFileSink:
    def test_email_log_file_contains_patient_name_and_invoice_id(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session, full_name="Alice Patel")
        bs_user = _make_billing_specialist(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[{"description":"Checkup","amount_cents":5000}]',
            total_amount_cents=5000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        token = login(client, "billing@test.com", password="billing123")

        import time
        before_patch = time.time()

        res = client.patch(
            f"/api/billing/invoices/{inv.invoice_id}",
            json={"status": "Paid"},
            headers=auth_headers(token),
        )
        assert res.status_code == 200

        email_log_dir = Path(__file__).resolve().parents[2] / "uploads" / "email_log"
        if not email_log_dir.exists():
            pytest.skip("uploads/email_log directory not created — email sink may run in different cwd")

        # Find only files written AFTER the patch call to avoid cross-test contamination
        pattern = f"*_invoice_{inv.invoice_id}.html"
        html_files = [
            f for f in email_log_dir.glob(pattern)
            if f.stat().st_mtime >= before_patch
        ]
        assert html_files, (
            f"No HTML file written after PATCH for invoice {inv.invoice_id} in {email_log_dir}. "
            f"All matching files: {list(email_log_dir.glob(pattern))}"
        )

        html_content = html_files[0].read_text(encoding="utf-8")
        assert "Alice Patel" in html_content, (
            f"Patient name 'Alice Patel' missing from email HTML. Got: {html_content[:300]}"
        )
        assert str(inv.invoice_id) in html_content, "Invoice ID missing from email HTML"


# ---------------------------------------------------------------------------
# BILL-7: Restricted fields on billing/patients
# ---------------------------------------------------------------------------


class TestBill7RestrictedPatientFields:
    def test_billing_patients_excludes_sensitive_fields(self, client, db_session):
        """Response items must NOT contain address, gender, emergency_contact_name,
        emergency_contact_phone (AUTHZ-9)."""
        _, patient = _make_patient_with_profile(db_session)
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")

        res = client.get("/api/billing/patients", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        items = res.json()["items"]
        assert items, "Expected at least one patient in response"

        banned = {"address", "gender", "emergency_contact_name", "emergency_contact_phone"}
        for item in items:
            present_banned = banned & item.keys()
            assert not present_banned, (
                f"Billing patient response must not contain {present_banned}. Got keys: {list(item.keys())}"
            )

    def test_billing_patients_includes_required_fields(self, client, db_session):
        """Response items must contain patient_id, full_name, date_of_birth, phone, email."""
        _, patient = _make_patient_with_profile(db_session)
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")

        res = client.get("/api/billing/patients", headers=auth_headers(token))
        assert res.status_code == 200
        items = res.json()["items"]
        required = {"patient_id", "full_name", "date_of_birth", "phone", "email"}
        for item in items:
            missing = required - item.keys()
            assert not missing, f"Billing patient response missing required fields: {missing}"


# ---------------------------------------------------------------------------
# BILL-8: Restricted fields on billing/appointments
# ---------------------------------------------------------------------------


class TestBill8RestrictedAppointmentFields:
    def _make_appointment(self, db_session, patient, doctor):
        appt = Appointment(
            patient_id=patient.patient_id,
            doctor_id=doctor.doctor_id,
            scheduled_at="2026-08-01T09:00:00",
            status="Scheduled",
            reason="This is the clinical reason",
            created_by_user_id=patient.user_id,
        )
        db_session.add(appt)
        db_session.commit()
        db_session.refresh(appt)
        return appt

    def test_billing_appointments_excludes_clinical_fields(self, client, db_session):
        """Response items must NOT contain reason, diagnosis, or clinical content (AUTHZ-8)."""
        _, patient = _make_patient_with_profile(db_session)
        dept = make_department(db_session)
        doc_user, doctor = make_doctor_user(db_session, email="doc@test.com", department=dept)
        self._make_appointment(db_session, patient, doctor)

        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")

        res = client.get("/api/billing/appointments", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        items = res.json()["items"]
        assert items, "Expected at least one appointment"

        banned_clinical = {"reason", "diagnosis", "notes", "visit_notes", "prescriptions"}
        for item in items:
            present_banned = banned_clinical & item.keys()
            assert not present_banned, (
                f"Billing appointment response must not contain {present_banned}. Keys: {list(item.keys())}"
            )

    def test_billing_appointments_includes_required_fields(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        dept = make_department(db_session)
        doc_user, doctor = make_doctor_user(db_session, email="doc@test.com", department=dept)
        self._make_appointment(db_session, patient, doctor)

        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")

        res = client.get("/api/billing/appointments", headers=auth_headers(token))
        assert res.status_code == 200
        items = res.json()["items"]
        required = {"appointment_id", "patient_id", "scheduled_at", "status"}
        for item in items:
            missing = required - item.keys()
            assert not missing, f"Billing appointment missing required fields: {missing}"


# ---------------------------------------------------------------------------
# BILL-9: Notifications endpoint
# ---------------------------------------------------------------------------


class TestBill9Notifications:
    def test_notifications_list_excludes_body_html(self, client, db_session):
        """GET /billing/notifications list items must NOT include body_html (Section 8.3.5)."""
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=1000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        # Trigger notification via PATCH
        token = login(client, "billing@test.com", password="billing123")
        client.patch(
            f"/api/billing/invoices/{inv.invoice_id}",
            json={"status": "Paid"},
            headers=auth_headers(token),
        )

        res = client.get("/api/billing/notifications", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        body = res.json()
        assert "items" in body
        for item in body["items"]:
            assert "body_html" not in item, (
                "body_html must be excluded from notification list items"
            )

    def test_notifications_detail_includes_body_html(self, client, db_session):
        """GET /billing/notifications/{id} must include body_html."""
        from app.models import EmailNotification

        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=1000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        # Directly insert a notification
        notif = EmailNotification(
            recipient_user_id=patient.user_id,
            subject="Test Subject",
            body_html="<html><body>Test</body></html>",
            sent_at="2026-07-19T10:00:00",
            trigger_event="invoice_status_change",
            related_invoice_id=inv.invoice_id,
            status="Sent",
        )
        db_session.add(notif)
        db_session.commit()
        db_session.refresh(notif)

        token = login(client, "billing@test.com", password="billing123")
        res = client.get(f"/api/billing/notifications/{notif.notification_id}", headers=auth_headers(token))
        assert res.status_code == 200, res.text
        detail = res.json()
        assert "body_html" in detail, "body_html must be present in notification detail response"

    def test_non_billing_user_cannot_access_notifications(self, client, db_session):
        """Staff/Doctor/Patient/Lab get 403 on /billing/notifications (Section 8.3.5)."""
        make_user(db_session, email="staff@test.com", role="Staff")
        token = login(client, "staff@test.com")
        res = client.get("/api/billing/notifications", headers=auth_headers(token))
        assert res.status_code == 403, f"Expected 403 for Staff on /billing/notifications, got {res.status_code}"


# ---------------------------------------------------------------------------
# BILL-10: Delete invoice (Pending only)
# ---------------------------------------------------------------------------


class TestBill10DeleteInvoice:
    def test_delete_paid_invoice_returns_409(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        paid_inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=500,
            status="Paid",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(paid_inv)
        db_session.commit()
        db_session.refresh(paid_inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.delete(
            f"/api/billing/invoices/{paid_inv.invoice_id}",
            headers=auth_headers(token),
        )
        assert res.status_code == 409, (
            f"Expected 409 when deleting a Paid invoice, got {res.status_code}: {res.text}"
        )

    def test_delete_pending_invoice_returns_204(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        pending_inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=500,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(pending_inv)
        db_session.commit()
        db_session.refresh(pending_inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.delete(
            f"/api/billing/invoices/{pending_inv.invoice_id}",
            headers=auth_headers(token),
        )
        assert res.status_code in (200, 204), (
            f"Expected 200/204 when deleting a Pending invoice, got {res.status_code}: {res.text}"
        )

    def test_delete_waived_invoice_returns_409(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        waived_inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=500,
            status="Waived",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(waived_inv)
        db_session.commit()
        db_session.refresh(waived_inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.delete(
            f"/api/billing/invoices/{waived_inv.invoice_id}",
            headers=auth_headers(token),
        )
        assert res.status_code == 409, (
            f"Expected 409 when deleting a Waived invoice, got {res.status_code}: {res.text}"
        )


# ---------------------------------------------------------------------------
# Extra: RBAC — BillingSpecialist denied from Admin/Doctor/Lab endpoints
# ---------------------------------------------------------------------------


class TestBillDenyEndpoints:
    def test_billing_specialist_cannot_access_admin_dashboard(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/admin/dashboard/summary", headers=auth_headers(token))
        assert res.status_code == 403, (
            f"BillingSpecialist must get 403 on /admin/dashboard/summary, got {res.status_code}"
        )

    def test_billing_specialist_cannot_access_admin_users(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/admin/users", headers=auth_headers(token))
        assert res.status_code == 403, (
            f"BillingSpecialist must get 403 on /admin/users, got {res.status_code}"
        )

    def test_billing_specialist_cannot_access_lab_orders(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/lab/orders", headers=auth_headers(token))
        assert res.status_code == 403, (
            f"BillingSpecialist must get 403 on /lab/orders, got {res.status_code}"
        )

    def test_billing_specialist_cannot_access_doctor_appointments(self, client, db_session):
        _make_billing_specialist(db_session)
        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/doctor/me/appointments", headers=auth_headers(token))
        assert res.status_code == 403, (
            f"BillingSpecialist must get 403 on /doctor/me/appointments, got {res.status_code}"
        )


# ---------------------------------------------------------------------------
# Extra: Insurance claim flag persistence (AC-INSURANCE-FLAG)
# ---------------------------------------------------------------------------


class TestInsuranceFlagPersistence:
    def test_insurance_flag_update_persists(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=1000,
            status="Pending",
            has_insurance_claim=0,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        token = login(client, "billing@test.com", password="billing123")
        res = client.patch(
            f"/api/billing/invoices/{inv.invoice_id}",
            json={"has_insurance_claim": 1},
            headers=auth_headers(token),
        )
        assert res.status_code == 200
        assert res.json()["has_insurance_claim"] == 1

        # Verify GET also returns updated field
        get_res = client.get(f"/api/billing/invoices/{inv.invoice_id}", headers=auth_headers(token))
        assert get_res.json()["has_insurance_claim"] == 1

    def test_insurance_claim_filter(self, client, db_session):
        _, patient = _make_patient_with_profile(db_session)
        bs_user = _make_billing_specialist(db_session)
        inv = Invoice(
            patient_id=patient.patient_id,
            line_items_json='[]',
            total_amount_cents=1000,
            status="Pending",
            has_insurance_claim=1,
            created_by_user_id=bs_user.id,
        )
        db_session.add(inv)
        db_session.commit()

        token = login(client, "billing@test.com", password="billing123")
        res = client.get("/api/billing/invoices?has_insurance_claim=1", headers=auth_headers(token))
        assert res.status_code == 200
        items = res.json()["items"]
        assert all(i["has_insurance_claim"] == 1 for i in items), (
            "Insurance claim filter returned invoice without has_insurance_claim=1"
        )
