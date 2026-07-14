from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.plugins import spotify, system_control

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("")
def list_plugins(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    states = db.query(models.PluginState).all()
    return [{"name": s.name, "enabled": s.enabled} for s in states]


@router.post("/{name}/toggle")
def toggle(name: str, body: dict, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    enabled = bool(body.get("enabled", False))
    s = db.query(models.PluginState).filter(models.PluginState.name == name).first()
    if not s:
        s = models.PluginState(name=name, enabled=enabled)
        db.add(s)
    else:
        s.enabled = enabled
    db.commit()
    return {"name": name, "enabled": enabled}


@router.get("/spotify/status")
def spotify_status(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return spotify.status(db, user.id)


@router.post("/spotify/command")
def spotify_command(body: dict, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return spotify.handle(body.get("command", ""), db, user.id)


@router.post("/system/command")
def system_command(body: dict, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return system_control.handle(body.get("command", ""))
