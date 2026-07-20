"""Endpoints da integração Obsidian (somente o dono)."""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import models
from app.services import obsidian as _obs

router = APIRouter(prefix="/api/obsidian", tags=["obsidian"])


class LearningRequest(BaseModel):
    title: str
    content: str


@router.get("/context")
def get_context(user: models.User = Depends(get_current_user)):
    return {"context": _obs.load_context(force=True)}


@router.post("/learning")
def add_learning(req: LearningRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode salvar aprendizados"}
    ok = _obs.add_learning(req.title, req.content)
    return {
        "status": "ok" if ok else "error",
        "message": "aprendizado salvo no vault (Obsidian)" if ok else "falhou ao salvar no vault",
    }


@router.post("/sync")
def sync(user: models.User = Depends(get_current_user)):
    return {"context": _obs.load_context(force=True)}


class ObsidianKeyRequest(BaseModel):
    key: str = ""
    url: str = ""


@router.post("/set_key")
def set_key(req: ObsidianKeyRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode configurar o Obsidian"}
    key = (req.key or "").strip()
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import encrypt
        db = SessionLocal()
        try:
            # chave (criptografada)
            row = db.query(models.Setting).filter_by(key="obsidian_api_key").first()
            if key:
                enc = encrypt(key)
                if row:
                    row.value = enc
                else:
                    row = models.Setting(key="obsidian_api_key", value=enc)
                    db.add(row)
            else:
                if row:
                    db.delete(row)
            # url (não é secreto)
            if req.url:
                row2 = db.query(models.Setting).filter_by(key="obsidian_api_url").first()
                if row2:
                    row2.value = req.url.strip()
                else:
                    row2 = models.Setting(key="obsidian_api_url", value=req.url.strip())
                    db.add(row2)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": f"erro ao salvar: {e}"}
    return {"status": "ok", "message": "Configuração do Obsidian salva."}


@router.get("/status")
def status(user: models.User = Depends(get_current_user)):
    return _obs.obsidian_status()
