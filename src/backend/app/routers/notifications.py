"""REQ-02 — In-App Notification Center.

Endpoints:
  GET  /notifications/unread-count  — must respond < 200ms (NOTIFNFR-1)
  GET  /notifications               — paginated inbox for caller
  PATCH /notifications/{id}/read    — mark one as read
  POST  /notifications/mark-all-read — mark all as read

Fan-out helper create_notifications() is used by all triggering endpoints.
Poll-on-login deferred firing is in services/notification_service.py.
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Notification, User
from app.services.notification_service import check_and_fire_deferred_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _fmt_notification(n: Notification) -> dict:
    return {
        "notification_id": n.notification_id,
        "event_type": n.event_type,
        "title": n.title,
        "body": n.body,
        "related_entity_type": n.related_entity_type,
        "related_entity_id": n.related_entity_id,
        "is_read": bool(n.is_read),
        "created_at": n.created_at,
    }


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns unread notification count. Also fires any matured deferred
    notifications (poll-on-login pattern, OI-2). Must respond < 200ms.
    """
    # Fire deferred notifications first (poll-on-login)
    try:
        check_and_fire_deferred_notifications(db, current_user.id)
    except Exception:
        # Never let deferred firing break the unread count response
        db.rollback()

    count = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == current_user.id,
            Notification.is_read == 0,
        )
        .count()
    )
    return {"unread_count": count}


@router.get("")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Paginated notification inbox for the calling user, newest first."""
    q = (
        db.query(Notification)
        .filter(Notification.recipient_user_id == current_user.id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
    )
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return {
        "items": [_fmt_notification(n) for n in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.patch("/{notification_id}/read")
def mark_one_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.get(Notification, notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if n.recipient_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your notification")
    n.is_read = 1
    db.commit()
    return {"notification_id": n.notification_id, "is_read": True}


@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == current_user.id,
            Notification.is_read == 0,
        )
        .update({"is_read": 1})
    )
    db.commit()
    return {"marked_read": updated}
