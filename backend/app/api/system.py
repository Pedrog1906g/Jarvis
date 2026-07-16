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


def _check_update_available() -> bool:
    """Verifica se há uma versão mais recente comparando APP_VERSION com o
    arquivo VERSION na raiz do repositório (atualizado pelo agente a cada deploy).
    Retorna True somente quando a versão no arquivo difere da versão em execução."""
    try:
        version_file = os.path.join(ROOT, "..", "VERSION")
        if not os.path.isfile(version_file):
            return False
        with open(version_file, encoding="utf-8") as f:
            file_version = f.read().strip()
        return file_version != APP_VERSION
    except Exception:
        return False


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
        "update_available": _check_update_available(),
    }


@router.get("/health")
def health():
    return {"status": "online", "version": APP_VERSION}
