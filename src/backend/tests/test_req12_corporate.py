"""REQ-12 — Corporate Health Check Packages (B2B): automated backend tests.

Acceptance criteria covered (from requirements §9.12 and task brief):
  1. GET /public/corporate/packages — returns active packages, no auth required (AC-CORP-1)
  2. Deactivated package not in public list (AC-CORP-2)
  3. POST /public/corporate/inquiries — submits without auth → 201 (AC-CORP-3)
  4. Admin creates package → 201 (CORPFR-2)
  5. Admin deactivates package (is_active=false) → 200, hidden from public (AC-CORP-2)
  6. Admin views inquiries → paginated list with pipeline_total_cents (CORPFR-6)
  7. Admin updates inquiry status to ClosedWon with deal_value → 200 (CORPFR-5)
  8. GET /admin/corporate/pipeline-summary — total reflects ClosedWon deals only (CORPFR-6)

Non-admin hitting admin endpoints → 403 (CORPNFR-1, AC-CORP-5) is also verified.
"""
from __future__ import annotations

import pytest

from app.models import CorporateInquiry, CorporatePackage
from app.utils import now_iso
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_package(db, name: str, tier_order: int = 1, is_active: int = 1) -> CorporatePackage:
    pkg = CorporatePackage(
        name=name,
        tier_order=tier_order,
        description=f"{name} health package",
        included_services_json='["Annual physical","Blood panel"]',
        price_range_display="$500–$800 per employee",
        is_active=is_active,
        created_at=now_iso(),
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def _make_inquiry(db, company: str = "Acme Corp", status: str = "New", deal_value: int | None = None) -> CorporateInquiry:
    inq = CorporateInquiry(
        company_name=company,
        contact_name="Jane Doe",
        email="jane@acme.com",
        status=status,
        deal_value_cents=deal_value,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    db.add(inq)
    db.commit()
    db.refresh(inq)
    return inq


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestREQ12Corporate:

    def test_public_packages_returns_active_packages_no_auth(
        self, client, db
    ):
        """Criterion 1: GET /public/corporate/packages — active packages, no auth required (AC-CORP-1)."""
        _make_package(db, "Basic", tier_order=1)
        _make_package(db, "Premium", tier_order=2)

        resp = client.get("/api/public/corporate/packages")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        names = [p["name"] for p in data["items"]]
        assert "Basic" in names
        assert "Premium" in names

    def test_deactivated_package_not_in_public_list(
        self, client, db
    ):
        """Criterion 2: Deactivated package absent from public list (AC-CORP-2)."""
        _make_package(db, "ActivePkg", tier_order=1, is_active=1)
        _make_package(db, "InactivePkg", tier_order=2, is_active=0)

        resp = client.get("/api/public/corporate/packages")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["items"]]
        assert "ActivePkg" in names
        assert "InactivePkg" not in names

    def test_public_inquiry_submission_without_auth_returns_201(
        self, client, db
    ):
        """Criterion 3: POST /public/corporate/inquiries — no auth → 201 (AC-CORP-3, CORPFR-4)."""
        resp = client.post(
            "/api/public/corporate/inquiries",
            json={
                "company_name": "TechCorp",
                "contact_name": "Alice Smith",
                "email": "alice@techcorp.com",
                "estimated_headcount": 200,
                "preferred_schedule": "Q1 2027",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "inquiry_id" in data

        # Row should be in DB with status=New
        inq = db.get(CorporateInquiry, data["inquiry_id"])
        assert inq is not None
        assert inq.status == "New"
        assert inq.company_name == "TechCorp"

    def test_admin_creates_package_returns_201(
        self, client, db, admin_user
    ):
        """Criterion 4: Admin creates package → 201 (CORPFR-2)."""
        resp = client.post(
            "/api/admin/corporate/packages",
            json={
                "name": "Enterprise",
                "tier_order": 3,
                "description": "Full corporate wellness",
                "included_services": ["Annual physical", "Blood panel", "Mental health"],
                "price_range_display": "$1200–$1800 per employee",
                "is_active": True,
            },
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Enterprise"
        assert data["is_active"] is True

    def test_admin_deactivates_package_hidden_from_public(
        self, client, db, admin_user
    ):
        """Criterion 5: Admin deactivates package → 200, package hidden from public list (AC-CORP-2)."""
        pkg = _make_package(db, "TargetPkg", tier_order=1, is_active=1)

        # Verify it's visible before deactivation
        before = client.get("/api/public/corporate/packages")
        assert "TargetPkg" in [p["name"] for p in before.json()["items"]]

        # Admin deactivates via PUT (is_active=false)
        upd_resp = client.put(
            f"/api/admin/corporate/packages/{pkg.package_id}",
            json={"is_active": False},
            headers=auth_headers(admin_user),
        )
        assert upd_resp.status_code == 200
        assert upd_resp.json()["is_active"] is False

        # Now it must not appear in the public list
        after = client.get("/api/public/corporate/packages")
        assert "TargetPkg" not in [p["name"] for p in after.json()["items"]]

    def test_admin_views_inquiries_paginated_with_pipeline_total(
        self, client, db, admin_user
    ):
        """Criterion 6: Admin views inquiries → paginated list with pipeline_total_cents (CORPFR-5/6)."""
        _make_inquiry(db, "AlphaCo", status="ClosedWon", deal_value=300000)
        _make_inquiry(db, "BetaCo", status="New")

        resp = client.get(
            "/api/admin/corporate/inquiries",
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "pipeline_total_cents" in data
        assert data["total"] == 2
        # pipeline total only reflects ClosedWon
        assert data["pipeline_total_cents"] == 300000

    def test_admin_updates_inquiry_status_closed_won_with_deal_value(
        self, client, db, admin_user
    ):
        """Criterion 7: Admin updates inquiry to ClosedWon with deal_value → 200."""
        inq = _make_inquiry(db, "GammaCo", status="Contacted")

        resp = client.patch(
            f"/api/admin/corporate/inquiries/{inq.inquiry_id}",
            json={"status": "ClosedWon", "deal_value_cents": 500000, "notes": "Signed 3-year contract"},
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ClosedWon"
        assert data["deal_value_cents"] == 500000
        assert data["notes"] == "Signed 3-year contract"

    def test_pipeline_summary_total_reflects_closed_won_only(
        self, client, db, admin_user
    ):
        """Criterion 8: GET /admin/corporate/pipeline-summary — total is sum of ClosedWon deals only."""
        _make_inquiry(db, "Delta", status="ClosedWon", deal_value=200000)
        _make_inquiry(db, "Epsilon", status="ClosedWon", deal_value=300000)
        _make_inquiry(db, "Zeta", status="New", deal_value=1000000)   # should NOT count

        resp = client.get(
            "/api/admin/corporate/pipeline-summary",
            headers=auth_headers(admin_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_closed_won_value" in data
        # Only ClosedWon deal values should sum: 200000 + 300000 = 500000
        assert data["total_closed_won_value"] == 500000

    def test_non_admin_cannot_view_inquiries_returns_403(
        self, client, db, patient_user, patient_profile
    ):
        """AC-CORP-5: Non-admin calling admin inquiry endpoint → 403 (CORPNFR-1)."""
        resp = client.get(
            "/api/admin/corporate/inquiries",
            headers=auth_headers(patient_user),
        )
        assert resp.status_code == 403

    def test_inquiry_headcount_must_be_positive(self, client, db):
        """AC-CORP-6: headcount < 1 → 400 (CORPFR-3 validation)."""
        resp = client.post(
            "/api/public/corporate/inquiries",
            json={
                "company_name": "Bad Corp",
                "contact_name": "Bob",
                "email": "bob@bad.com",
                "estimated_headcount": -5,
            },
        )
        assert resp.status_code == 400

    def test_public_packages_ordered_by_tier_order(self, client, db):
        """CORPFR-2: Active packages returned ordered by tier_order asc."""
        _make_package(db, "Gold", tier_order=3)
        _make_package(db, "Silver", tier_order=2)
        _make_package(db, "Bronze", tier_order=1)

        resp = client.get("/api/public/corporate/packages")
        assert resp.status_code == 200
        items = resp.json()["items"]
        tier_orders = [p["tier_order"] for p in items]
        assert tier_orders == sorted(tier_orders)
