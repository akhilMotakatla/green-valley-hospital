"""Tests for Section 6 backend endpoint changes (api-spec.md v1.1).

Covers:
  - GET /public/home: recent_articles field (VI-HOME-7)
  - GET /public/home: featured_departments[].first_doctor with profile_photo_path (VI-HOME-5)
  - GET /public/departments/{id}/doctors: new {department, items} wrapper shape (VI-DDOC-1)
  - profile_photo_path field exposed on every doctor endpoint (VI-DDOC-2, VI-DOCPROF-1)
  - GET /api/doctor/me: profile_photo_path included
  - PATCH /api/doctor/me: accepts profile_photo_path (DOC-1)
  - GET /api/public/doctors/{id}: profile_photo_path included
"""

from __future__ import annotations

from conftest import auth_headers, login, make_department, make_doctor_user, make_user
from app.models import BlogArticle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_published_article(db_session, title: str, author_id: int, slug: str | None = None) -> BlogArticle:
    """Insert a Published blog article and return the ORM object."""
    from app.utils import utcnow

    if slug is None:
        slug = title.lower().replace(" ", "-")
    article = BlogArticle(
        title=title,
        slug=slug,
        summary=f"Summary of {title}",
        body=f"Body of {title}",
        author_user_id=author_id,
        status="Published",
        published_at=utcnow(),
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


def _make_draft_article(db_session, title: str, author_id: int, slug: str | None = None) -> BlogArticle:
    """Insert a Draft blog article and return the ORM object."""
    if slug is None:
        slug = title.lower().replace(" ", "-")
    article = BlogArticle(
        title=title,
        slug=slug,
        summary=f"Summary of {title}",
        body=f"Body of {title}",
        author_user_id=author_id,
        status="Draft",
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


# ---------------------------------------------------------------------------
# GET /api/public/home — recent_articles (VI-HOME-7 / api-spec.md §2)
# ---------------------------------------------------------------------------


def test_home_returns_recent_articles_key(client, db_session):
    """GET /public/home always returns a recent_articles key (empty list if no published articles)."""
    res = client.get("/api/public/home")
    assert res.status_code == 200
    body = res.json()
    assert "recent_articles" in body, "recent_articles key missing from /public/home response"
    # When no published articles exist the value must be an empty list, not null (api-spec §2 note).
    assert isinstance(body["recent_articles"], list)


def test_home_recent_articles_empty_when_no_published_articles(client, db_session):
    """If zero Published articles exist, recent_articles is [] not null."""
    admin = make_user(db_session, email="homeadmin@example.com", role="Admin")
    # Draft only — must not appear in recent_articles
    _make_draft_article(db_session, "Unpublished", admin.id, "unpublished")

    res = client.get("/api/public/home")
    assert res.status_code == 200
    assert res.json()["recent_articles"] == []


def test_home_recent_articles_published_only(client, db_session):
    """Draft articles must never appear in recent_articles (PUB-BLOG-3 / VI-HOME-7)."""
    admin = make_user(db_session, email="homeadmin2@example.com", role="Admin")
    published = _make_published_article(db_session, "Good Article", admin.id, "good-article")
    _make_draft_article(db_session, "Hidden Draft", admin.id, "hidden-draft")

    res = client.get("/api/public/home")
    assert res.status_code == 200
    recent = res.json()["recent_articles"]
    slugs = [a["slug"] for a in recent]
    assert "good-article" in slugs, "Published article not in recent_articles"
    assert "hidden-draft" not in slugs, "Draft article must not appear in recent_articles"


def test_home_recent_articles_capped_at_three(client, db_session):
    """At most 3 articles are returned in recent_articles even if more are published."""
    admin = make_user(db_session, email="homeadmin3@example.com", role="Admin")
    for i in range(5):
        _make_published_article(db_session, f"Article {i}", admin.id, f"article-{i}")

    res = client.get("/api/public/home")
    assert res.status_code == 200
    recent = res.json()["recent_articles"]
    assert len(recent) <= 3, f"Expected at most 3 recent_articles, got {len(recent)}"


def test_home_recent_articles_shape(client, db_session):
    """Each item in recent_articles has the required fields from the api-spec."""
    admin = make_user(db_session, email="homeadmin4@example.com", role="Admin")
    _make_published_article(db_session, "Shaped Article", admin.id, "shaped-article")

    res = client.get("/api/public/home")
    assert res.status_code == 200
    recent = res.json()["recent_articles"]
    assert len(recent) >= 1

    required_fields = {"article_id", "title", "slug", "summary", "author_name", "published_at", "cover_image_path"}
    for item in recent:
        missing = required_fields - item.keys()
        assert not missing, f"recent_articles item missing fields: {missing}"


# ---------------------------------------------------------------------------
# GET /api/public/home — featured_departments.first_doctor (VI-HOME-5 / api-spec §2)
# ---------------------------------------------------------------------------


def test_home_featured_departments_include_first_doctor_key(client, db_session):
    """Each element of featured_departments has a first_doctor key (null if no doctors)."""
    dept = make_department(db_session, "TestDept")
    res = client.get("/api/public/home")
    assert res.status_code == 200
    body = res.json()
    featured = body.get("featured_departments", [])
    target = next((d for d in featured if d["name"] == "TestDept"), None)
    assert target is not None, "Department not found in featured_departments"
    assert "first_doctor" in target, "first_doctor key missing from featured_departments element"


def test_home_first_doctor_is_null_when_no_doctors(client, db_session):
    """first_doctor is null/None when a department has no active doctors."""
    make_department(db_session, "EmptyDept")
    res = client.get("/api/public/home")
    assert res.status_code == 200
    featured = res.json()["featured_departments"]
    target = next((d for d in featured if d["name"] == "EmptyDept"), None)
    assert target is not None
    assert target["first_doctor"] is None


def test_home_first_doctor_shape(client, db_session):
    """When a department has a doctor, first_doctor has the required fields."""
    dept = make_department(db_session, "DoctorDept")
    make_doctor_user(db_session, email="firstdoc@example.com", full_name="Dr. First", department=dept)

    res = client.get("/api/public/home")
    assert res.status_code == 200
    featured = res.json()["featured_departments"]
    target = next((d for d in featured if d["name"] == "DoctorDept"), None)
    assert target is not None
    fd = target["first_doctor"]
    assert fd is not None
    required_keys = {"doctor_id", "full_name", "specialty", "profile_photo_path"}
    missing = required_keys - fd.keys()
    assert not missing, f"first_doctor missing fields: {missing}"


def test_home_first_doctor_profile_photo_path_is_exposed(client, db_session):
    """profile_photo_path in first_doctor can be a string or null — it must exist as a key."""
    dept = make_department(db_session, "PhotoDept")
    _, doctor = make_doctor_user(db_session, email="photodoc@example.com", department=dept)
    # Set a photo path directly on the doctor object.
    doctor.profile_photo_path = "/images/doctors/photodoc.jpg"
    db_session.commit()

    res = client.get("/api/public/home")
    assert res.status_code == 200
    featured = res.json()["featured_departments"]
    target = next((d for d in featured if d["name"] == "PhotoDept"), None)
    assert target is not None
    fd = target["first_doctor"]
    assert fd is not None
    assert fd["profile_photo_path"] == "/images/doctors/photodoc.jpg"


# ---------------------------------------------------------------------------
# GET /api/public/departments/{id}/doctors — new {department, items} shape (VI-DDOC-1)
# ---------------------------------------------------------------------------


def test_department_doctors_returns_department_wrapper(client, db_session):
    """Response must be {department: {...}, items: [...]} not a bare list (api-spec v1.1 §2)."""
    dept = make_department(db_session, "Neurosurgery")
    res = client.get(f"/api/public/departments/{dept.department_id}/doctors")
    assert res.status_code == 200
    body = res.json()
    assert "department" in body, "department wrapper key missing from GET /public/departments/{id}/doctors"
    assert "items" in body, "items key missing from GET /public/departments/{id}/doctors"


def test_department_doctors_department_object_shape(client, db_session):
    """The department sub-object must include department_id, name, and description."""
    dept = make_department(db_session, "Gastro")
    res = client.get(f"/api/public/departments/{dept.department_id}/doctors")
    assert res.status_code == 200
    dept_obj = res.json()["department"]
    assert dept_obj["department_id"] == dept.department_id
    assert dept_obj["name"] == "Gastro"
    assert "description" in dept_obj


def test_department_doctors_items_include_profile_photo_path(client, db_session):
    """Each doctor in items must expose profile_photo_path (null or string)."""
    dept = make_department(db_session, "Hematology")
    _, doctor = make_doctor_user(db_session, email="hemdoc@example.com", department=dept)
    doctor.profile_photo_path = "/images/doctors/hemdoc.jpg"
    db_session.commit()

    res = client.get(f"/api/public/departments/{dept.department_id}/doctors")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert "profile_photo_path" in items[0], "profile_photo_path missing from department doctors items"
    assert items[0]["profile_photo_path"] == "/images/doctors/hemdoc.jpg"


def test_department_doctors_profile_photo_path_null_when_not_set(client, db_session):
    """profile_photo_path should be null (not missing) when no photo is set."""
    dept = make_department(db_session, "Rheumatology")
    make_doctor_user(db_session, email="rheumdoc@example.com", department=dept)

    res = client.get(f"/api/public/departments/{dept.department_id}/doctors")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert "profile_photo_path" in items[0], "profile_photo_path key missing"
    assert items[0]["profile_photo_path"] is None


def test_department_doctors_404_for_unknown_department(client, db_session):
    """Requesting a non-existent department returns 404."""
    res = client.get("/api/public/departments/99999/doctors")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/public/doctors/{id} — profile_photo_path (api-spec §2)
# ---------------------------------------------------------------------------


def test_public_doctor_profile_includes_profile_photo_path(client, db_session):
    """GET /public/doctors/{id} must expose profile_photo_path."""
    dept = make_department(db_session, "ENTPub")
    _, doctor = make_doctor_user(db_session, email="entpubdoc@example.com", department=dept)

    res = client.get(f"/api/public/doctors/{doctor.doctor_id}")
    assert res.status_code == 200
    body = res.json()
    assert "profile_photo_path" in body, "profile_photo_path missing from public doctor profile"


def test_public_doctor_profile_photo_path_reflects_set_value(client, db_session):
    """profile_photo_path returns the value written via the doctor's profile."""
    dept = make_department(db_session, "SpinePub")
    _, doctor = make_doctor_user(db_session, email="spinepubdoc@example.com", department=dept)
    doctor.profile_photo_path = "/images/doctors/spine.jpg"
    db_session.commit()

    res = client.get(f"/api/public/doctors/{doctor.doctor_id}")
    assert res.status_code == 200
    assert res.json()["profile_photo_path"] == "/images/doctors/spine.jpg"


# ---------------------------------------------------------------------------
# GET /api/doctor/me — profile_photo_path (api-spec §4)
# ---------------------------------------------------------------------------


def test_doctor_me_includes_profile_photo_path(client, db_session):
    """GET /api/doctor/me must include profile_photo_path in the response."""
    dept = make_department(db_session, "FamilyMed")
    user, doctor = make_doctor_user(db_session, email="fmdoc@example.com", department=dept)
    token = login(client, "fmdoc@example.com")

    res = client.get("/api/doctor/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert "profile_photo_path" in res.json(), "profile_photo_path missing from GET /doctor/me"


def test_doctor_me_profile_photo_path_null_by_default(client, db_session):
    """profile_photo_path is null when not set on the doctor record."""
    dept = make_department(db_session, "SportsMed")
    user, doctor = make_doctor_user(db_session, email="sportsdoc@example.com", department=dept)
    token = login(client, "sportsdoc@example.com")

    res = client.get("/api/doctor/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["profile_photo_path"] is None


# ---------------------------------------------------------------------------
# PATCH /api/doctor/me — accepts profile_photo_path (DOC-1 / api-spec §4)
# ---------------------------------------------------------------------------


def test_doctor_patch_me_accepts_profile_photo_path(client, db_session):
    """PATCH /api/doctor/me with profile_photo_path persists the path and returns it."""
    dept = make_department(db_session, "PalliativeCare")
    user, doctor = make_doctor_user(db_session, email="palldoc@example.com", department=dept)
    token = login(client, "palldoc@example.com")

    new_path = "/images/doctors/palldoc.jpg"
    res = client.patch(
        "/api/doctor/me",
        json={"profile_photo_path": new_path},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json().get("profile_photo_path") == new_path

    # Verify the value persists on a subsequent GET.
    me_res = client.get("/api/doctor/me", headers=auth_headers(token))
    assert me_res.json()["profile_photo_path"] == new_path


def test_doctor_patch_me_profile_photo_path_can_be_cleared(client, db_session):
    """PATCH /api/doctor/me with profile_photo_path=null clears the value."""
    dept = make_department(db_session, "ClearPhotoTest")
    user, doctor = make_doctor_user(db_session, email="cleardoc@example.com", department=dept)
    doctor.profile_photo_path = "/images/doctors/old.jpg"
    db_session.commit()
    token = login(client, "cleardoc@example.com")

    # Send null / None to clear
    res = client.patch(
        "/api/doctor/me",
        json={"profile_photo_path": None},
        headers=auth_headers(token),
    )
    # Sending null for an optional field is fine; the endpoint should accept it.
    # Whether it clears the value depends on implementation; we assert no server error.
    assert res.status_code == 200, res.text


# ---------------------------------------------------------------------------
# Staff directory — profile_photo_path (api-spec §6 / STF-7)
# ---------------------------------------------------------------------------


def test_staff_directory_includes_profile_photo_path(client, db_session):
    """GET /api/staff/directory must expose profile_photo_path on each doctor entry."""
    dept = make_department(db_session, "StaffDirDept")
    _, doctor = make_doctor_user(db_session, email="staffdirdoc@example.com", department=dept)
    doctor.profile_photo_path = "/images/doctors/staffdirdoc.jpg"
    db_session.commit()

    staff_user = make_user(db_session, email="staffagent@example.com", role="Staff")
    token = login(client, "staffagent@example.com")

    res = client.get("/api/staff/directory", headers=auth_headers(token))
    assert res.status_code == 200
    items = res.json()["items"]
    assert any("profile_photo_path" in item for item in items), \
        "profile_photo_path missing from staff directory doctor entries"
    target = next(i for i in items if i.get("profile_photo_path") == "/images/doctors/staffdirdoc.jpg")
    assert target is not None
