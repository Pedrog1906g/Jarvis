import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.config import APP_VERSION, APP_NAME, DEMO_MODE
from app.core.llm import is_available

router = APIRouter(prefix="/api/system", tags=["system"])

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.get("/info")
def info(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    changelog = ""
    try:
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
            changelog = f.read()
    except Exception:
        pass
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "llm_available": is_available(),
        "demo_mode": DEMO_MODE,
        "user": {"id": user.id, "username": user.username, "display_name": user.display_name},
        "changelog": changelog,
        "update_available": False,  # o agente atualiza a versão conforme evolução
    }


@router.get("/health")
def health():
    return {"status": "online", "version": APP_VERSION}
