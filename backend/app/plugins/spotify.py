"""Plugin Spotify (stub funcional).
Para produção: implementar OAuth2 com Spotify e chamar a Web API.
Aqui mantemos o estado/intenção para demonstrar a arquitetura de plugins.
"""
from sqlalchemy.orm import Session
from app.db import models


def status(db: Session, owner_id: int):
    s = db.query(models.PluginState).filter(models.PluginState.name == "spotify").first()
    return {
        "name": "spotify",
        "enabled": bool(s.enabled) if s else False,
        "authenticated": False,  # implementar OAuth depois
        "note": "Stub: conecte OAuth do Spotify para controle real (play/pause/playlist).",
    }


def handle(command: str, db: Session, owner_id: int):
    cmd = command.lower()
    if "tocar" in cmd or "play" in cmd:
        return {"action": "play", "query": command, "status": "stub"}
    if "pausar" in cmd or "pause" in cmd:
        return {"action": "pause", "status": "stub"}
    if "playlist" in cmd:
        return {"action": "playlist", "query": command, "status": "stub"}
    return {"action": "unknown", "echo": command}
