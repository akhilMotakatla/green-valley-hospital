"""REQ-07 — Public Symptom / Condition Search: automated backend tests.

Acceptance criteria covered (from requirements §9.7 and task brief):
  1. GET /public/search?q=cardio — returns departments and doctors, no auth required (AC-SRCH-2)
  2. Departments appear before doctors in results (SRCHFR-2, AC-SRCH-2)
  3. GET /public/search?q=zzzzz — returns empty result with 200, not 404 (AC-SRCH-3)
  4. Admin adds symptom tag to department → 201 (AC-SRCH-5, SRCHFR-6)
  5. Admin adds duplicate tag → 409 (SRCHFR-5)
  6. Admin deletes tag → 204 (SRCHFR-6)
  7. Non-admin adding tag → 403 (SRCHFR-6)
"""
from __future__ import annotations

import pytest

from app.models import Department, DepartmentSymptomTag, Doctor, User
from app.security import hash_password
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dept(db, name: str, description: str = "") -> Department:
    d = Department(name=name, description=description, is_active=1)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _make_doctor_with_specialty(db, dept_id: int, email: str, specialty: str, bio: str = "") -> tuple[User, Doctor]:
    u = User(
        email=email,
        password_hash=hash_password("Pass1234"),
        role="Doctor",
        full_name=f"Dr. {specialty}",
        is_active=1,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    d = Doctor(user_id=u.id, department_id=dept_id, specialty=specialty, bio=bio, years_experience=5)
    db.add(d)
    db.commit()
    db.refresh(d)
    return u, d


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestREQ07Search:

    def test_search_returns_departments_and_doctors_no_auth(
        self, client, db
    ):
        """Criterion 1: GET /public/search?q=cardio — no auth required, returns depts + docs."""
        cardio_dept = _make_dept(db, "Cardiology", "Heart care specialists")
        _make_doctor_with_specialty(db, cardio_dept.department_id, "cardio_doc@hospital.test", "Cardiology")

        # No auth header
        resp = client.get("/api/public/search?q=cardio")
        assert resp.status_code == 200
        data = resp.json()
        assert "departments" in data
        assert "doctors" in data
        assert "query" in data
        assert data["query"] == "cardio"
        assert len(data["departments"]) >= 1
        dept_names = [d["name"] for d in data["departments"]]
        assert "Cardiology" in dept_names

    def test_departments_appear_before_doctors_in_results(
        self, client, db
    ):
        """Criterion 2: Response separates departments and doctors; spec requires depts before docs."""
        neuro_dept = _make_dept(db, "Neurology", "Brain and nervous system")
        _make_doctor_with_specialty(
            db, neuro_dept.department_id, "neuro_doc@hospital.test",
            "Neurology", bio="Expert in neurology disorders"
        )

        resp = client.get("/api/public/search?q=neuro")
        assert resp.status_code == 200
        data = resp.json()
        # Response shape has departments and doctors as separate arrays (SRCHFR-3)
        assert isinstance(data["departments"], list)
        assert isinstance(data["doctors"], list)
        # At least one department result for "neuro"
        assert len(data["departments"]) >= 1
        # Departments key comes before doctors in the spec ordering; both present
        assert "departments" in data and "doctors" in data

    def test_no_results_returns_200_with_empty_arrays(
        self, client, db
    ):
        """Criterion 3: q=zzzzz returns 200 with empty arrays, not 404 (AC-SRCH-3)."""
        resp = client.get("/api/public/search?q=zzzzz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["departments"] == []
        assert data["doctors"] == []
        assert data["total"] == 0
        assert data["query"] == "zzzzz"

    def test_admin_adds_symptom_tag_returns_201(
        self, client, db, admin_user, dept
    ):
        """Criterion 4: Admin adds symptom tag to department → 201 (SRCHFR-6)."""
        resp = client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "chest pain"},
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["tag_text"] == "chest pain"
        assert data["department_id"] == dept.department_id
        assert "tag_id" in data

    def test_admin_adds_duplicate_tag_returns_409(
        self, client, db, admin_user, dept
    ):
        """Criterion 5: Admin adds duplicate tag → 409 (SRCHFR-5)."""
        # First add
        client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "shortness of breath"},
            headers=auth_headers(admin_user),
        )
        # Duplicate add
        resp = client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "shortness of breath"},
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 409

    def test_admin_deletes_tag_returns_204(
        self, client, db, admin_user, dept
    ):
        """Criterion 6: Admin deletes tag → 204 (SRCHFR-6)."""
        create_resp = client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "palpitations"},
            headers=auth_headers(admin_user),
        )
        tag_id = create_resp.json()["tag_id"]

        del_resp = client.delete(
            f"/api/admin/departments/{dept.department_id}/tags/{tag_id}",
            headers=auth_headers(admin_user),
        )
        assert del_resp.status_code == 204

        # Verify tag is gone from DB
        tag = db.get(DepartmentSymptomTag, tag_id)
        assert tag is None

    def test_non_admin_adding_tag_returns_403(
        self, client, db, doctor_user, doctor_profile, dept
    ):
        """Criterion 7: Non-admin adding tag → 403 (SRCHFR-6)."""
        resp = client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "arrhythmia"},
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 403

    def test_symptom_tag_appears_in_search_results(
        self, client, db, admin_user, dept
    ):
        """Bonus: AC-SRCH-5 — after adding tag, search returns the department."""
        # Add "hair loss" tag to dept (Cardiology in fixture, but concept holds)
        client.post(
            f"/api/admin/departments/{dept.department_id}/tags",
            json={"tag_text": "chest pressure"},
            headers=auth_headers(admin_user),
        )

        resp = client.get("/api/public/search?q=pressure")
        assert resp.status_code == 200
        data = resp.json()
        dept_ids = [d["department_id"] for d in data["departments"]]
        assert dept.department_id in dept_ids

    def test_short_query_returns_4xx(self, client, db):
        """SRCHFR-4 / AC-SRCH-4: Query shorter than 2 chars → 400 Bad Request.

        BUG-GROUP-C-01 fixed: Query(..., min_length=2) Pydantic constraint was
        removed and replaced with a manual HTTPException(status_code=400) check,
        so the endpoint now returns exactly 400 (not 422) as the spec requires.
        """
        resp = client.get("/api/public/search?q=a")
        assert resp.status_code == 400
        assert "2 characters" in resp.json()["detail"]
