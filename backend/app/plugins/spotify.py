"""Plugin Spotify.

Estado atual: integração de intenção (intent routing). O backend classifica
o comando e retorna a ação esperada; a execução real ocorre no app Android
(que tem o SDK do Spotify) ou via OAuth2 Spotify Web API (pendente).

Para ativar controle real via Web API:
  1. Crie um app em https://developer.spotify.com/dashboard
  2. Defina SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET e SPOTIFY_REDIRECT_URI no .env
  3. Implemente o fluxo OAuth2 PKCE usando os endpoints /api/plugins/spotify/auth/*
     (a ser adicionado quando o usuário solicitar essa funcionalidade)
"""
import os
from sqlalchemy.orm import Session
from app.db import models

_SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
_HAS_OAUTH = bool(_SPOTIFY_CLIENT_ID and os.getenv("SPOTIFY_CLIENT_SECRET", ""))


def status(db: Session, owner_id: int):
    s = db.query(models.PluginState).filter(models.PluginState.name == "spotify").first()
    return {
        "name": "spotify",
        "enabled": bool(s.enabled) if s else False,
        # Autenticação real requer o fluxo OAuth2 com as credenciais do Spotify Developer.
        "authenticated": False,
        "oauth_configured": _HAS_OAUTH,
        "note": (
            "Credenciais OAuth configuradas — implemente o fluxo de autorização para autenticar."
            if _HAS_OAUTH
            else "Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no .env para ativar."
        ),
    }


def handle(command: str, db: Session, owner_id: int):
    """Classifica a intenção do comando de música e retorna a ação esperada.

    No app Android, essa ação é executada pelo SDK nativo do Spotify.
    Na web, o HUD abre o YouTube como fallback (configurado no index.html).
    """
    cmd = command.lower()
    # Checar "playlist" antes de "play" para evitar match prematuro.
    if "playlist" in cmd or "lista" in cmd:
        return {"action": "playlist", "query": command, "status": "intent_classified"}
    if any(k in cmd for k in ("tocar", "play", "toque", "ouvir")):
        return {"action": "play", "query": command, "status": "intent_classified"}
    if any(k in cmd for k in ("pausar", "pause", "parar", "stop")):
        return {"action": "pause", "status": "intent_classified"}
    if "próxima" in cmd or "next" in cmd or "pular" in cmd:
        return {"action": "next", "status": "intent_classified"}
    if "anterior" in cmd or "previous" in cmd or "voltar" in cmd:
        return {"action": "previous", "status": "intent_classified"}
    if "volume" in cmd:
        return {"action": "volume", "query": command, "status": "intent_classified"}
    return {"action": "unknown", "echo": command, "status": "unrecognized"}
