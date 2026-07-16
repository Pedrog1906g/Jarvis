"""API de Memória de Longo Prazo do NEXUS AI.

Expõe os fatos duráveis extraídos das conversas do dono:
  GET  /api/memory/facts           — lista todos os fatos
  POST /api/memory/facts           — adiciona fato manual
  DELETE /api/memory/facts/{fid}  — remove um fato específico
  DELETE /api/memory/facts        — limpa toda a memória (reset)
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user

router = APIRouter(prefix="/api/memory", tags=["memory"])


class FactCreate(BaseModel):
    fact: str
    category: str = "geral"
    importance: int = 1


class FactOut(BaseModel):
    id: int
    fact: str
    category: str
    importance: int
    created_at: Optional[str] = None


def _serialize(f: models.MemoryFact) -> dict:
    return {
        "id": f.id,
        "fact": f.fact,
        "category": f.category,
        "importance": f.importance,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("/facts")
def list_facts(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Lista todos os fatos de memória de longo prazo do dono, ordenados por importância."""
    facts = (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.owner_id == user.id)
        .order_by(models.MemoryFact.importance.desc(), models.MemoryFact.id.desc())
        .all()
    )
    return [_serialize(f) for f in facts]


@router.post("/facts")
def add_fact(
    req: FactCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Adiciona um fato manualmente à memória de longo prazo."""
    if not req.fact.strip():
        return {"status": "error", "message": "fato não pode ser vazio"}
    # Evita duplicatas exatas
    exists = (
        db.query(models.MemoryFact)
        .filter(
            models.MemoryFact.owner_id == user.id,
            models.MemoryFact.fact == req.fact.strip(),
        )
        .first()
    )
    if exists:
        return {"status": "exists", "fact": _serialize(exists)}
    f = models.MemoryFact(
        owner_id=user.id,
        fact=req.fact.strip(),
        category=req.category,
        importance=max(1, min(10, req.importance)),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    # Sincroniza com Supabase (best-effort)
    try:
        from app.services import supabase_sync
        if supabase_sync.sc.is_configured():
            uname = db.query(models.User).filter(models.User.id == user.id).first()
            supabase_sync.sync_memory(uname.username if uname else "owner", f.fact, f.category, f.importance)
    except Exception:
        pass
    return {"status": "ok", "fact": _serialize(f)}


@router.delete("/facts/{fid}")
def delete_fact(
    fid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Remove um fato específico da memória."""
    f = (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.id == fid, models.MemoryFact.owner_id == user.id)
        .first()
    )
    if not f:
        return {"status": "error", "message": "fato não encontrado"}
    db.delete(f)
    db.commit()
    return {"status": "ok", "deleted_id": fid}


@router.delete("/facts")
def clear_facts(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Apaga TODA a memória de longo prazo. Use com cuidado."""
    deleted = (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.owner_id == user.id)
        .delete()
    )
    db.commit()
    return {"status": "ok", "deleted_count": deleted}


@router.get("/summary")
def memory_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Resumo estatístico da memória: total de fatos por categoria."""
    facts = (
        db.query(models.MemoryFact)
        .filter(models.MemoryFact.owner_id == user.id)
        .all()
    )
    categories: dict[str, int] = {}
    for f in facts:
        categories[f.category] = categories.get(f.category, 0) + 1
    return {
        "total": len(facts),
        "by_category": categories,
        "top_facts": [_serialize(f) for f in sorted(facts, key=lambda x: -x.importance)[:5]],
    }
