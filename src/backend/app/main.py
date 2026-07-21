from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BLOG_COVERS_DIR, CORS_ORIGINS, UPLOADS_DIR
from app.database import init_db
from app.routers import admin, auth, billing, doctor, lab, patient, public, staff
from app.routers.availability import admin_avail_router, doctor_avail_router, slots_router
from app.routers.notifications import router as notifications_router
from app.routers.waitlist import router as waitlist_router
from app.routers.discharge import router as discharge_router
from app.routers.surveys import router as surveys_router

app = FastAPI(title="Green Valley Hospital API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    BLOG_COVERS_DIR.mkdir(parents=True, exist_ok=True)
    # Section 8.3: email notification HTML files are written here by email_sink.py.
    os.makedirs("uploads/email_log", exist_ok=True)
    # Blog cover images are public static content once published
    # (architecture.md §4.3); lab result attachments are intentionally NOT
    # mounted here and are served only via the authenticated
    # GET /api/lab/results/{result_id}/file route.
    app.mount("/static/blog_covers", StaticFiles(directory=str(BLOG_COVERS_DIR)), name="blog_covers")


@app.get("/")
def root():
    return {"service": "Green Valley Hospital API", "status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(doctor.router, prefix="/api")
app.include_router(patient.router, prefix="/api")
app.include_router(staff.router, prefix="/api")
app.include_router(lab.router, prefix="/api")
app.include_router(lab.file_router, prefix="/api")
# Section 9 / v1.2 — BillingSpecialist portal
app.include_router(billing.router, prefix="/api")
# Notification endpoints also accept Admin (Section 9.6); mounted on a
# separate sub-router without the BillingSpecialist-only dependency.
app.include_router(billing._notif_router, prefix="/api")
# Batch 2: availability endpoints (REQ-01)
app.include_router(slots_router, prefix="/api")
app.include_router(doctor_avail_router, prefix="/api")
app.include_router(admin_avail_router, prefix="/api")
# Batch 2: in-app notifications (REQ-02)
app.include_router(notifications_router, prefix="/api")
# Batch 2 Group B: waitlist (REQ-09), discharge summaries (REQ-10), surveys (REQ-11)
app.include_router(waitlist_router, prefix="/api")
app.include_router(discharge_router, prefix="/api")
app.include_router(surveys_router, prefix="/api")
