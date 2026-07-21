"""Application configuration.

Reads settings from environment variables (with .env support) with sensible
defaults for local development, per docs/architecture.md.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root = three levels up from this file (src/backend/app/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# db/green_valley.db lives at the project root's db/ folder, NOT inside src/backend,
# per the orchestrator's explicit instruction.
DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "green_valley.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

UPLOADS_DIR = PROJECT_ROOT / "uploads"
LAB_RESULTS_DIR = UPLOADS_DIR / "lab_results"
BLOG_COVERS_DIR = UPLOADS_DIR / "blog_covers"

# JWT settings (HS256, 60-minute TTL, no refresh token per architecture.md §3).
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# CORS: allow the Vite dev server origin.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# Appointment cancellation minimum notice window (architecture.md §4.1).
CANCELLATION_NOTICE_HOURS = 2

# Upload limits (architecture.md §4.3).
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
LAB_ATTACHMENT_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
BLOG_COVER_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
