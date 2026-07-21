from __future__ import annotations

from datetime import datetime, timedelta, timezone

from conftest import auth_headers, login, make_department, make_doctor_user, make_user


def _signup_patient(client, email, full_name="Patient"):
    res = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "password": "Passw0rd!",
            "full_name": full_name,
            "phone": "555-0000",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


# ---------------- Appointment booking (AC-APT-1/2/3) ----------------


def test_book_appointment_creates_scheduled_row_visible_to_both_sides(client, db_session):
    dept = make_department(db_session, "Derm")
    doc_user, doctor = make_doctor_user(db_session, email="dermdoc@example.com", department=dept)
    _signup_patient(client, "dermpat@example.com")

    token_doc = login(client, "dermdoc@example.com")
    token_pat = login(client, "dermpat@example.com")

    res = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": "2030-04-01T11:00:00"},
        headers=auth_headers(token_pat),
    )
    assert res.status_code == 201
    assert res.json()["status"] == "Scheduled"

    pat_list = client.get("/api/patients/me/appointments", headers=auth_headers(token_pat)).json()
    doc_list = client.get("/api/doctor/me/appointments", headers=auth_headers(token_doc)).json()
    assert pat_list["total"] == 1
    assert doc_list["total"] == 1


def test_double_booking_same_slot_rejected_409(client, db_session):
    dept = make_department(db_session, "Pulm")
    doc_user, doctor = make_doctor_user(db_session, email="pulmdoc@example.com", department=dept)
    _signup_patient(client, "pulmpatA@example.com", "Pulm A")
    _signup_patient(client, "pulmpatB@example.com", "Pulm B")

    token_a = login(client, "pulmpatA@example.com")
    token_b = login(client, "pulmpatB@example.com")

    slot = {"doctor_id": doctor.doctor_id, "scheduled_at": "2030-05-01T09:00:00"}
    first = client.post("/api/patients/me/appointments", json=slot, headers=auth_headers(token_a))
    assert first.status_code == 201

    second = client.post("/api/patients/me/appointments", json=slot, headers=auth_headers(token_b))
    assert second.status_code == 409

    doc_token = login(client, "pulmdoc@example.com")
    doc_appts = client.get("/api/doctor/me/appointments", headers=auth_headers(doc_token)).json()
    assert doc_appts["total"] == 1  # no duplicate row created


def test_cancel_within_notice_window_rejected(client, db_session):
    dept = make_department(db_session, "Onco")
    doc_user, doctor = make_doctor_user(db_session, email="oncodoc@example.com", department=dept)
    _signup_patient(client, "oncopat@example.com")
    token_pat = login(client, "oncopat@example.com")

    near_future = (datetime.now(timezone.utc) + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": near_future},
        headers=auth_headers(token_pat),
    )
    assert book.status_code == 201, book.text
    appt_id = book.json()["appointment_id"]

    res = client.delete(f"/api/patients/me/appointments/{appt_id}", headers=auth_headers(token_pat))
    assert res.status_code == 409


def test_cancel_outside_notice_window_succeeds(client, db_session):
    dept = make_department(db_session, "Endo")
    doc_user, doctor = make_doctor_user(db_session, email="endodoc@example.com", department=dept)
    _signup_patient(client, "endopat@example.com")
    token_pat = login(client, "endopat@example.com")

    far_future = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": far_future},
        headers=auth_headers(token_pat),
    )
    appt_id = book.json()["appointment_id"]

    res = client.delete(f"/api/patients/me/appointments/{appt_id}", headers=auth_headers(token_pat))
    assert res.status_code == 200
    assert res.json()["status"] == "Cancelled"


# ---------------- Lab workflow (AC-LAB-1/2/3) ----------------


def test_lab_order_workflow_end_to_end(client, db_session):
    dept = make_department(db_session, "Radiology")
    doc_user, doctor = make_doctor_user(db_session, email="raddoc@example.com", department=dept)
    make_user(db_session, email="labtech2@example.com", role="Lab")
    _signup_patient(client, "radpat@example.com")

    token_doc = login(client, "raddoc@example.com")
    token_lab = login(client, "labtech2@example.com")
    token_pat = login(client, "radpat@example.com")

    # Establish doctor-patient relationship first.
    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": "2030-06-01T09:00:00"},
        headers=auth_headers(token_pat),
    )
    assert book.status_code == 201

    pat_me = client.get("/api/patients/me", headers=auth_headers(token_pat)).json()
    patient_id = pat_me["patient_id"]

    order_res = client.post(
        f"/api/doctor/patients/{patient_id}/lab-orders",
        json={"test_type": "XRay", "notes": "Chest X-ray"},
        headers=auth_headers(token_doc),
    )
    assert order_res.status_code == 201, order_res.text
    order_id = order_res.json()["order_id"]
    assert order_res.json()["status"] == "Pending"

    # AC-LAB-1: appears in Lab's pending queue.
    queue = client.get("/api/lab/orders?status=Pending", headers=auth_headers(token_lab)).json()
    assert any(o["order_id"] == order_id for o in queue["items"])

    # Lab marks in progress, then uploads a result.
    client.patch(f"/api/lab/orders/{order_id}/status", json={"status": "InProgress"}, headers=auth_headers(token_lab))
    result_res = client.post(
        f"/api/lab/orders/{order_id}/results",
        data={"result_data": "Clear, no abnormalities"},
        headers=auth_headers(token_lab),
    )
    assert result_res.status_code == 201, result_res.text
    assert result_res.json()["version"] == 1
    assert result_res.json()["is_finalized"] is True

    # AC-LAB-2: visible to ordering doctor and owning patient.
    doc_results = client.get(f"/api/doctor/lab-orders/{order_id}/results", headers=auth_headers(token_doc))
    assert doc_results.status_code == 200
    assert len(doc_results.json()["results"]) == 1

    pat_records = client.get("/api/patients/me/records", headers=auth_headers(token_pat)).json()
    assert len(pat_records["lab_results"]) == 1

    # Unrelated doctor cannot see it.
    doc2_user, doc2 = make_doctor_user(db_session, email="raddoc2@example.com", department=dept)
    token_doc2 = login(client, "raddoc2@example.com")
    doc2_res = client.get(f"/api/doctor/lab-orders/{order_id}/results", headers=auth_headers(token_doc2))
    assert doc2_res.status_code == 403

    # AC-LAB-3: amending creates a new version, original remains retrievable.
    amend_res = client.post(
        f"/api/lab/orders/{order_id}/results/amend",
        data={"result_data": "Correction: mild inflammation noted"},
        headers=auth_headers(token_lab),
    )
    assert amend_res.status_code == 201, amend_res.text
    assert amend_res.json()["version"] == 2

    all_results = client.get(f"/api/lab/orders/{order_id}/results", headers=auth_headers(token_lab)).json()
    assert len(all_results["results"]) == 2
    versions = {r["version"] for r in all_results["results"]}
    assert versions == {1, 2}


# ---------------- Blog (AC-BLOG-1/2) ----------------


def test_draft_blog_article_not_visible_publicly(client, db_session):
    make_user(db_session, email="blogadmin@example.com", role="Admin")
    token_admin = login(client, "blogadmin@example.com")

    create = client.post(
        "/api/admin/blog",
        data={"title": "Draft Only Article", "body": "secret body"},
        headers=auth_headers(token_admin),
    )
    assert create.status_code == 201, create.text
    slug = create.json()["slug"]

    listing = client.get("/api/public/blog").json()
    assert all(item["slug"] != slug for item in listing["items"])

    detail = client.get(f"/api/public/blog/{slug}")
    assert detail.status_code == 404


def test_publishing_article_makes_it_public(client, db_session):
    make_user(db_session, email="blogadmin2@example.com", role="Admin")
    token_admin = login(client, "blogadmin2@example.com")

    create = client.post(
        "/api/admin/blog",
        data={"title": "Published Article", "body": "public body"},
        headers=auth_headers(token_admin),
    )
    article_id = create.json()["article_id"]
    slug = create.json()["slug"]

    publish = client.patch(f"/api/admin/blog/{article_id}/publish", headers=auth_headers(token_admin))
    assert publish.status_code == 200
    assert publish.json()["published_at"] is not None

    detail = client.get(f"/api/public/blog/{slug}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Published Article"


# ---------------- Contact form (AC-CONTACT-1/2) ----------------


def test_contact_form_valid_submission_creates_row(client):
    res = client.post(
        "/api/public/contact-messages",
        json={"name": "Visitor", "email": "visitor@example.com", "subject": "Question", "message": "Hello there"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "New"


def test_contact_form_missing_field_rejected_no_row(client, db_session):
    res = client.post(
        "/api/public/contact-messages",
        json={"name": "Visitor", "email": "visitor2@example.com", "message": "Hello"},  # missing subject
    )
    assert res.status_code == 422

    from app.models import ContactMessage

    count = db_session.query(ContactMessage).count()
    assert count == 0


# ---------------- Billing (AC-BILL-1) ----------------


def test_staff_created_invoice_visible_to_owning_patient_and_admin_not_others(client, db_session):
    from app.models import Invoice

    p1 = _signup_patient(client, "billpat1@example.com", "Bill Pat One")
    p2 = _signup_patient(client, "billpat2@example.com", "Bill Pat Two")
    make_user(db_session, email="billadmin@example.com", role="Admin")

    token_p1 = login(client, "billpat1@example.com")
    token_p2 = login(client, "billpat2@example.com")
    token_admin = login(client, "billadmin@example.com")

    p1_me = client.get("/api/patients/me", headers=auth_headers(token_p1)).json()

    invoice = Invoice(
        patient_id=p1_me["patient_id"],
        line_items_json="[]",
        total_amount_cents=5000,
        status="Pending",
        created_by_user_id=1,
    )
    db_session.add(invoice)
    db_session.commit()

    own = client.get("/api/patients/me/invoices", headers=auth_headers(token_p1)).json()
    assert own["total"] == 1

    other = client.get("/api/patients/me/invoices", headers=auth_headers(token_p2)).json()
    assert other["total"] == 0

    admin_view = client.get("/api/admin/invoices", headers=auth_headers(token_admin)).json()
    assert admin_view["total"] == 1


# ---------------- Admin account management ----------------


def test_admin_can_create_and_deactivate_staff_account(client, db_session):
    dept = make_department(db_session, "AdminDept")
    make_user(db_session, email="rootadmin@example.com", role="Admin")
    token_admin = login(client, "rootadmin@example.com")

    create = client.post(
        "/api/admin/users",
        json={
            "email": "newstaff@example.com",
            "password": "Passw0rd!",
            "role": "Staff",
            "full_name": "New Staff",
            "department_id": dept.department_id,
        },
        headers=auth_headers(token_admin),
    )
    assert create.status_code == 201, create.text
    user_id = create.json()["id"]

    deactivate = client.patch(
        f"/api/admin/users/{user_id}/status", json={"is_active": False}, headers=auth_headers(token_admin)
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    login_attempt = client.post("/api/auth/login", json={"email": "newstaff@example.com", "password": "Passw0rd!"})
    assert login_attempt.status_code == 403
