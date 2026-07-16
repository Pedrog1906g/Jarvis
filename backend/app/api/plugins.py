from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.plugins import spotify, system_control
from app.core.voice import tts_provider_info

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


# ── Spotify ───────────────────────────────────────────────────────────────────

@router.get("/spotify/status")
def spotify_status(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return spotify.status(db, user.id)


@router.post("/spotify/command")
def spotify_command(body: dict, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    return spotify.handle(body.get("command", ""), db, user.id)


@router.get("/spotify/auth/start")
def spotify_auth_start(user: models.User = Depends(get_current_user)):
    """Inicia o fluxo OAuth2 PKCE do Spotify. Retorna a URL de autorização."""
    return spotify.auth_start()


@router.get("/spotify/auth/callback")
def spotify_auth_callback(code: str = "", state: str = "", error: str = "",
                          db: Session = Depends(get_db)):
    """Callback do Spotify OAuth2. Troca o code pelo access_token e salva no banco.

    Nota: este endpoint NÃO requer autenticação JWT porque é chamado pelo Spotify
    após o redirecionamento. O state garante que só pedidos legítimos são aceitos.
    """
    if error:
        return {"status": "error", "message": f"Spotify recusou: {error}"}
    if not code or not state:
        return {"status": "error", "message": "Parâmetros code/state ausentes"}
    return spotify.auth_callback(code, state, db)


@router.get("/spotify/now-playing")
def spotify_now_playing(db: Session = Depends(get_db),
                        user: models.User = Depends(get_current_user)):
    """Retorna a faixa atual do Spotify."""
    return spotify.handle("o que está tocando", db, user.id)


# ── Sistema / Controle de dispositivo ────────────────────────────────────────

@router.post("/system/command")
def system_command(body: dict, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    return system_control.handle(body.get("command", ""))


# ── Voz / TTS ─────────────────────────────────────────────────────────────────

@router.get("/voice/info")
def voice_info(user: models.User = Depends(get_current_user)):
    """Retorna informações sobre o provedor TTS ativo."""
    return tts_provider_info()
