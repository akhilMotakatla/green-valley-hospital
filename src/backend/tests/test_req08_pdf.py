"""REQ-08 — Patient Medical Record Export (PDF): automated backend tests.

WeasyPrint requires GTK3 runtime which is not available on Windows. The endpoint
returns HTTP 503 with a JSON error body when WeasyPrint cannot import.

Acceptance criteria covered (from requirements §9.8 and task brief):
  1. Authenticated patient calls GET /patients/me/export-pdf
     → 503 with JSON detail about WeasyPrint unavailability (PDFFR-2, OI-3 fallback)
  2. Doctor calls GET /patients/me/export-pdf → 403 (PDFFR-2, AC-PDF-2)
  3. Staff calls GET /patients/me/export-pdf → 403 (PDFFR-2, AC-PDF-2)

Full PDF content (Content-Type: application/pdf, watermark, section ordering)
cannot be tested without WeasyPrint/GTK3. Only auth guards and the 503 fallback
behavior are tested here, per task brief scope.
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers


class TestREQ08PDF:

    def test_patient_export_pdf_returns_503_weasyprint_unavailable(
        self, client, db, patient_user, patient_profile
    ):
        """Criterion 1: Patient calls export-pdf — WeasyPrint unavailable on Windows → 503."""
        resp = client.get(
            "/api/patients/me/export-pdf",
            headers=auth_headers(patient_user),
        )
        # On this Windows machine, WeasyPrint cannot import GTK3 DLLs.
        # The endpoint raises 503 with a JSON detail rather than attempting PDF generation.
        assert resp.status_code == 503
        data = resp.json()
        assert "detail" in data
        # The error message must mention WeasyPrint or GTK3 so callers know why
        detail_lower = data["detail"].lower()
        assert "weasyprint" in detail_lower or "gtk" in detail_lower or "unavailable" in detail_lower

    def test_doctor_export_pdf_returns_403(
        self, client, db, doctor_user, doctor_profile
    ):
        """Criterion 2: Doctor calling export-pdf → 403 (PDFFR-2, AC-PDF-2).

        The PDF export endpoint is Patient-only. require_role('Patient') should
        reject a Doctor before the WeasyPrint check is reached.
        """
        resp = client.get(
            "/api/patients/me/export-pdf",
            headers=auth_headers(doctor_user),
        )
        assert resp.status_code == 403

    def test_staff_export_pdf_returns_403(
        self, client, db, staff_user, staff_member
    ):
        """Criterion 3: Staff calling export-pdf → 403 (PDFFR-2, AC-PDF-2)."""
        resp = client.get(
            "/api/patients/me/export-pdf",
            headers=auth_headers(staff_user),
        )
        assert resp.status_code == 403

    def test_unauthenticated_export_pdf_returns_401(self, client, db):
        """Sanity: unauthenticated request → 401 (not 403 or 503)."""
        resp = client.get("/api/patients/me/export-pdf")
        assert resp.status_code == 401
