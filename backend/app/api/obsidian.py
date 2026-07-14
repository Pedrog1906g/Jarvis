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
