from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.core.firebase import mirror_reminder

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderCreate(BaseModel):
    title: str
    note: Optional[str] = None
    due_at: str  # ISO 8601, ex.: 2026-07-15T09:30:00


class ReminderOut(BaseModel):
    id: int
    title: str
    note: Optional[str] = None
    due_at: str
    done: bool


@router.get("", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    items = db.query(models.Reminder).filter(
        models.Reminder.owner_id == user.id).order_by(models.Reminder.due_at).all()
    return [_serialize(r) for r in items]


@router.post("")
def create_reminder(req: ReminderCreate, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    due = datetime.fromisoformat(req.due_at)
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    r = models.Reminder(owner_id=user.id, title=req.title, note=req.note, due_at=due)
    db.add(r)
    db.commit()
    db.refresh(r)
    try:
        mirror_reminder(user.id, r)
    except Exception:
        pass
    return _serialize(r)


@router.post("/{rid}/done")
def mark_done(rid: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    r = db.query(models.Reminder).filter(
        models.Reminder.id == rid, models.Reminder.owner_id == user.id).first()
    if not r:
        return {"ok": False}
    r.done = True
    db.commit()
    return {"ok": True}


@router.get("/due")
def due_reminders(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    items = db.query(models.Reminder).filter(
        models.Reminder.owner_id == user.id,
        models.Reminder.done == False,
        models.Reminder.due_at <= now).all()
    return [_serialize(r) for r in items]


def _serialize(r: models.Reminder):
    return {
        "id": r.id, "title": r.title, "note": r.note,
        "due_at": r.due_at.isoformat(), "done": r.done,
    }
