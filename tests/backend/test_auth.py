from __future__ import annotations

from conftest import auth_headers, login, make_user


def test_signup_success_forces_patient_role(client):
    res = client.post(
        "/api/auth/signup",
        json={
            "email": "newpatient@example.com",
            "password": "Passw0rd1",
            "full_name": "New Patient",
            "phone": "555-1111",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["role"] == "Patient"
    assert body["email"] == "newpatient@example.com"


def test_signup_ignores_role_field_in_payload(client):
    # AC-AUTH-1: role field, if smuggled in, must be ignored server-side.
    res = client.post(
        "/api/auth/signup",
        json={
            "email": "sneaky@example.com",
            "password": "Passw0rd1",
            "full_name": "Sneaky Guy",
            "phone": "555-2222",
            "date_of_birth": "1990-01-01",
            "role": "Admin",
        },
    )
    assert res.status_code == 201, res.text
    assert res.json()["role"] == "Patient"


def test_signup_rejects_weak_password(client):
    res = client.post(
        "/api/auth/signup",
        json={
            "email": "weakpw@example.com",
            "password": "short",
            "full_name": "Weak PW",
            "phone": "555-3333",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res.status_code == 422


def test_signup_duplicate_email_rejected(client):
    payload = {
        "email": "dupe@example.com",
        "password": "Passw0rd1",
        "full_name": "Dupe",
        "phone": "555-4444",
        "date_of_birth": "1990-01-01",
    }
    first = client.post("/api/auth/signup", json=payload)
    assert first.status_code == 201
    second = client.post("/api/auth/signup", json=payload)
    assert second.status_code == 422


def test_login_success_returns_role_and_token(client, db_session):
    make_user(db_session, email="staffer@example.com", role="Staff")
    res = client.post("/api/auth/login", json={"email": "staffer@example.com", "password": "Passw0rd!"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["role"] == "Staff"
    assert body["token_type"] == "bearer"
    assert isinstance(body["expires_in"], int) and body["expires_in"] > 0
    assert body["access_token"]


def test_login_wrong_password_generic_401(client, db_session):
    make_user(db_session, email="realuser@example.com", role="Patient")
    res = client.post("/api/auth/login", json={"email": "realuser@example.com", "password": "WrongPass1"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_same_generic_401(client):
    # AUTH-5: must not reveal whether the email exists -- same message/status
    # as a known-email-wrong-password case.
    res = client.post("/api/auth/login", json={"email": "doesnotexist@example.com", "password": "WrongPass1"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_login_deactivated_account_403(client, db_session):
    make_user(db_session, email="inactive@example.com", role="Patient", is_active=False)
    res = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "Passw0rd!"})
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()


def test_me_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, db_session):
    make_user(db_session, email="me@example.com", role="Patient", full_name="Me Person")
    token = login(client, "me@example.com")
    res = client.get("/api/auth/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"
    assert res.json()["full_name"] == "Me Person"


def test_invalid_token_401(client):
    res = client.get("/api/auth/me", headers=auth_headers("not-a-real-token"))
    assert res.status_code == 401
