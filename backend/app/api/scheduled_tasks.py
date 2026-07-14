"""Endpoints de tarefas agendadas (somente o dono)."""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user

router = APIRouter(prefix="/api/scheduled_tasks", tags=["scheduled_tasks"])


class STCreate(BaseModel):
    action: str  # self_improve | remind
    run_at: str  # ISO 8601, ex.: 2026-08-03T12:00:00
    payload: dict = {}
    note: Optional[str] = None


def _serialize(t: models.ScheduledTask):
    return {
        "id": t.id,
        "action": t.action,
        "payload": json.loads(t.payload or "{}"),
        "note": t.note,
        "run_at": t.run_at.isoformat(),
        "done": t.done,
    }


@router.get("")
def list_tasks(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    items = (
        db.query(models.ScheduledTask)
        .filter(models.ScheduledTask.owner_id == user.id)
        .order_by(models.ScheduledTask.run_at)
        .all()
    )
    return [_serialize(t) for t in items]


@router.post("")
def create_task(req: STCreate, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode agendar tarefas"}
    if req.action not in ("self_improve", "remind"):
        return {"status": "error", "message": "acao invalida (use self_improve ou remind)"}
    due = datetime.fromisoformat(req.run_at)
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    t = models.ScheduledTask(
        owner_id=user.id,
        action=req.action,
        payload=json.dumps(req.payload or {}),
        note=req.note,
        run_at=due,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"status": "ok", "task": _serialize(t)}
