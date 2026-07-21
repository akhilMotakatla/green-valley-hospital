from __future__ import annotations

import json
import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import (
    BLOG_COVER_CONTENT_TYPES,
    BLOG_COVERS_DIR,
    LAB_ATTACHMENT_CONTENT_TYPES,
    LAB_RESULTS_DIR,
    MAX_UPLOAD_SIZE_BYTES,
)
from app.models import AuditLogEntry


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def unique_slug(db: Session, title: str) -> str:
    from app.models import BlogArticle

    base = slugify(title)
    slug = base
    counter = 2
    while db.query(BlogArticle).filter(BlogArticle.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def paginate(query, page: int, page_size: int):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def total_pages(total: int, page_size: int) -> int:
    """Compute total_pages per the pagination convention.
    Returns 0 when total is 0 (api-spec.md Conventions — AC-PAGINATE-2).
    """
    if total == 0:
        return 0
    return math.ceil(total / page_size)


def write_audit_log(db: Session, *, actor_user_id: int, action: str, target_user_id: int | None = None, details: str | None = None) -> None:
    entry = AuditLogEntry(actor_user_id=actor_user_id, action=action, target_user_id=target_user_id, details=details)
    db.add(entry)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    v = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def save_upload(file: UploadFile, dest_dir: Path, filename: str, *, kind: str) -> str:
    """Validates and saves an uploaded file, returns the relative path stored
    on disk (relative to the project's /uploads/ root), per architecture.md §4.3.
    """
    allowed = LAB_ATTACHMENT_CONTENT_TYPES if kind == "lab" else BLOG_COVER_CONTENT_TYPES
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File exceeds 10 MB limit")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_bytes(contents)

    if kind == "lab":
        return str(dest_path.relative_to(LAB_RESULTS_DIR.parent.parent))
    return str(dest_path.relative_to(BLOG_COVERS_DIR.parent.parent))


def dumps(value) -> str:
    return json.dumps(value)


def loads(value: str | None):
    if value is None:
        return None
    return json.loads(value)
