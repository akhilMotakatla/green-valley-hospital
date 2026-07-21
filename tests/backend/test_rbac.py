from __future__ import annotations

from conftest import auth_headers, login, make_department, make_doctor_user, make_user


def _signup_patient(client, email, full_name="Patient One"):
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


def test_patient_hitting_doctor_only_route_gets_403(client):
    _signup_patient(client, "pat1@example.com")
    token = login(client, "pat1@example.com")
    res = client.get("/api/doctor/me", headers=auth_headers(token))
    assert res.status_code == 403


def test_patient_hitting_admin_only_route_gets_403(client):
    _signup_patient(client, "pat2@example.com")
    token = login(client, "pat2@example.com")
    res = client.get("/api/admin/users", headers=auth_headers(token))
    assert res.status_code == 403


def test_unauthenticated_request_gets_401_not_403(client):
    res = client.get("/api/doctor/me")
    assert res.status_code == 401


def test_patient_can_only_fetch_own_records(client, db_session):
    _signup_patient(client, "isoA@example.com", "Isolation A")
    _signup_patient(client, "isoB@example.com", "Isolation B")
    token_a = login(client, "isoA@example.com")
    token_b = login(client, "isoB@example.com")

    # Discover B's own patient_id via /me.
    res_b_me = client.get("/api/patients/me", headers=auth_headers(token_b))
    assert res_b_me.status_code == 200
    b_patient_id = res_b_me.json()["patient_id"]

    # AC-PAT-1: A requesting B's records by id -> 403, no data leaked.
    res = client.get(f"/api/patients/{b_patient_id}/records", headers=auth_headers(token_a))
    assert res.status_code == 403
    assert "visit_notes" not in res.json()

    # A can fetch their own records fine.
    res_a_me = client.get("/api/patients/me", headers=auth_headers(token_a))
    a_patient_id = res_a_me.json()["patient_id"]
    res_own = client.get(f"/api/patients/{a_patient_id}/records", headers=auth_headers(token_a))
    assert res_own.status_code == 200
    assert "visit_notes" in res_own.json()


def test_patient_appointments_list_only_returns_own_rows(client, db_session):
    dept = make_department(db_session, "Neurology")
    doc_user, doctor = make_doctor_user(db_session, email="docrbac@example.com", department=dept)

    pa = _signup_patient(client, "apA@example.com", "Appt A")
    pb = _signup_patient(client, "apB@example.com", "Appt B")
    token_a = login(client, "apA@example.com")
    token_b = login(client, "apB@example.com")

    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": "2030-01-01T09:00:00", "reason": "checkup"},
        headers=auth_headers(token_a),
    )
    assert book.status_code == 201, book.text

    res_a = client.get("/api/patients/me/appointments", headers=auth_headers(token_a))
    res_b = client.get("/api/patients/me/appointments", headers=auth_headers(token_b))
    assert res_a.status_code == 200 and res_b.status_code == 200
    assert res_a.json()["total"] == 1
    assert res_b.json()["total"] == 0


def test_doctor_no_relationship_gets_403_on_patient_records(client, db_session):
    dept = make_department(db_session, "Ortho")
    doc_user, doctor = make_doctor_user(db_session, email="docz@example.com", department=dept)
    patient_body = _signup_patient(client, "unrelated@example.com", "Unrelated Patient")
    token_doc = login(client, "docz@example.com")

    # AC-DOC-1: doctor has never had an appointment with this patient.
    # patient_id in the Patient table is not the user id -- fetch it.
    token_pat = login(client, "unrelated@example.com")
    pat_me = client.get("/api/patients/me", headers=auth_headers(token_pat)).json()

    res = client.get(f"/api/doctor/patients/{pat_me['patient_id']}/records", headers=auth_headers(token_doc))
    assert res.status_code == 403


def test_doctor_with_relationship_can_access_records_and_create_prescription(client, db_session):
    dept = make_department(db_session, "Cardio")
    doc_user, doctor = make_doctor_user(db_session, email="doccardio@example.com", department=dept)
    _signup_patient(client, "cardiopatient@example.com", "Cardio Patient")

    token_doc = login(client, "doccardio@example.com")
    token_pat = login(client, "cardiopatient@example.com")

    # Patient books an appointment with the doctor, establishing the
    # relationship required by AUTHZ-2.
    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doctor.doctor_id, "scheduled_at": "2030-02-01T10:00:00"},
        headers=auth_headers(token_pat),
    )
    assert book.status_code == 201, book.text
    appointment_id = book.json()["appointment_id"]

    pat_me = client.get("/api/patients/me", headers=auth_headers(token_pat)).json()
    patient_id = pat_me["patient_id"]

    records_res = client.get(f"/api/doctor/patients/{patient_id}/records", headers=auth_headers(token_doc))
    assert records_res.status_code == 200

    # AC-DOC-2: doctor creates a prescription for this patient/appointment.
    rx_res = client.post(
        f"/api/doctor/appointments/{appointment_id}/prescriptions",
        json={"medicines": [{"name": "Amoxicillin", "dosage": "500mg", "frequency": "2x/day", "duration": "7 days"}], "instructions": "Take with food"},
        headers=auth_headers(token_doc),
    )
    assert rx_res.status_code == 201, rx_res.text
    rx_body = rx_res.json()
    assert rx_body["doctor_id"] == doctor.doctor_id
    assert rx_body["patient_id"] == patient_id

    # Retrievable by the doctor (author)...
    doc_records = client.get(f"/api/doctor/patients/{patient_id}/records", headers=auth_headers(token_doc)).json()
    assert len(doc_records["prescriptions"]) == 1

    # ...and by the patient (owner).
    pat_records = client.get("/api/patients/me/records", headers=auth_headers(token_pat)).json()
    assert len(pat_records["prescriptions"]) == 1


def test_doctor_cannot_update_status_of_another_doctors_appointment(client, db_session):
    dept = make_department(db_session, "ENT")
    doc1_user, doc1 = make_doctor_user(db_session, email="entdoc1@example.com", department=dept)
    doc2_user, doc2 = make_doctor_user(db_session, email="entdoc2@example.com", department=dept)
    _signup_patient(client, "entpatient@example.com", "ENT Patient")

    token_doc1 = login(client, "entdoc1@example.com")
    token_doc2 = login(client, "entdoc2@example.com")
    token_pat = login(client, "entpatient@example.com")

    book = client.post(
        "/api/patients/me/appointments",
        json={"doctor_id": doc1.doctor_id, "scheduled_at": "2030-03-01T09:00:00"},
        headers=auth_headers(token_pat),
    )
    appointment_id = book.json()["appointment_id"]

    res = client.patch(
        f"/api/doctor/appointments/{appointment_id}/status",
        json={"status": "Completed"},
        headers=auth_headers(token_doc2),
    )
    assert res.status_code == 403

    res_owner = client.patch(
        f"/api/doctor/appointments/{appointment_id}/status",
        json={"status": "Completed"},
        headers=auth_headers(token_doc1),
    )
    assert res_owner.status_code == 200
    assert res_owner.json()["status"] == "Completed"


def test_staff_cannot_hit_doctor_or_admin_routes(client, db_session):
    make_user(db_session, email="frontdesk@example.com", role="Staff")
    token = login(client, "frontdesk@example.com")

    assert client.get("/api/doctor/me", headers=auth_headers(token)).status_code == 403
    assert client.get("/api/admin/users", headers=auth_headers(token)).status_code == 403


def test_lab_cannot_hit_admin_or_doctor_routes(client, db_session):
    make_user(db_session, email="labtech@example.com", role="Lab")
    token = login(client, "labtech@example.com")

    assert client.get("/api/admin/users", headers=auth_headers(token)).status_code == 403
    assert client.get("/api/doctor/me", headers=auth_headers(token)).status_code == 403
