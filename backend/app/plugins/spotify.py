"""Plugin Spotify — OAuth2 PKCE + Spotify Web API.

Fluxo completo:
  1. /api/plugins/spotify/auth/start   → retorna URL de autorização do Spotify
  2. Usuário autoriza no Spotify
  3. /api/plugins/spotify/auth/callback → troca code por tokens, salva criptografado no banco
  4. /api/plugins/spotify/command       → executa comandos reais via Spotify Web API

Sem credenciais OAuth configuradas: classifica a intenção e retorna
{"status": "intent_classified"} para o app Android executar nativamente.

Configurar no .env:
  SPOTIFY_CLIENT_ID=...
  SPOTIFY_CLIENT_SECRET=...
  SPOTIFY_REDIRECT_URI=https://seu-servidor/api/plugins/spotify/auth/callback
"""
import base64
import hashlib
import os
import secrets
import time
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.db import models
from app.core.crypto import encrypt, decrypt

# ── Configuração ─────────────────────────────────────────────────────────────

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "")
SPOTIFY_SCOPES = (
    "user-read-playback-state user-modify-playback-state "
    "user-read-currently-playing playlist-read-private "
    "user-library-read streaming"
)

_HAS_OAUTH = bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)

# Armazena code_verifier temporário por state (em memória — ok para single-instance)
_pending_states: dict[str, dict] = {}  # state -> {verifier, ts}


# ── PKCE helpers ─────────────────────────────────────────────────────────────

def _pkce_pair() -> tuple[str, str]:
    """Gera (code_verifier, code_challenge) para OAuth2 PKCE."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


# ── Armazenamento de tokens no banco ─────────────────────────────────────────

_TOKEN_KEY = "spotify_token"
_REFRESH_KEY = "spotify_refresh"
_EXPIRY_KEY = "spotify_token_expiry"


def _save_tokens(db: Session, access_token: str, refresh_token: str, expires_in: int):
    expiry = str(int(time.time()) + expires_in - 60)
    for key, val in [(_TOKEN_KEY, access_token), (_REFRESH_KEY, refresh_token), (_EXPIRY_KEY, expiry)]:
        row = db.query(models.Setting).filter_by(key=key).first()
        enc = encrypt(val)
        if row:
            row.value = enc
        else:
            row = models.Setting(key=key, value=enc)
            db.add(row)
    db.commit()


def _load_access_token(db: Session) -> Optional[str]:
    """Retorna access_token válido (renova se expirado)."""
    expiry_row = db.query(models.Setting).filter_by(key=_EXPIRY_KEY).first()
    if not expiry_row:
        return None
    expiry = int(decrypt(expiry_row.value) or "0")
    if time.time() < expiry:
        row = db.query(models.Setting).filter_by(key=_TOKEN_KEY).first()
        return decrypt(row.value) if row else None
    # Tenta renovar via refresh_token
    return _refresh_access_token(db)


def _refresh_access_token(db: Session) -> Optional[str]:
    row = db.query(models.Setting).filter_by(key=_REFRESH_KEY).first()
    if not row:
        return None
    refresh_token = decrypt(row.value)
    if not refresh_token or not _HAS_OAUTH:
        return None
    try:
        creds = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        r = httpx.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
        _save_tokens(db, d["access_token"], d.get("refresh_token", refresh_token), d.get("expires_in", 3600))
        return d["access_token"]
    except Exception as e:
        print(f"[NEXUS] Spotify refresh falhou: {e}")
        return None


def is_authenticated(db: Session) -> bool:
    return bool(_load_access_token(db))


# ── OAuth2 flow ───────────────────────────────────────────────────────────────

def auth_start() -> dict:
    """Gera URL de autorização do Spotify com PKCE."""
    if not _HAS_OAUTH:
        return {"error": "Credenciais Spotify não configuradas (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET)"}
    if not SPOTIFY_REDIRECT_URI:
        return {"error": "SPOTIFY_REDIRECT_URI não configurado"}
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    # Limpa states velhos (> 10 min)
    now = time.time()
    for s in list(_pending_states):
        if now - _pending_states[s]["ts"] > 600:
            del _pending_states[s]
    _pending_states[state] = {"verifier": verifier, "ts": now}

    params = "&".join([
        f"response_type=code",
        f"client_id={SPOTIFY_CLIENT_ID}",
        f"scope={SPOTIFY_SCOPES.replace(' ', '%20')}",
        f"redirect_uri={SPOTIFY_REDIRECT_URI}",
        f"state={state}",
        f"code_challenge={challenge}",
        f"code_challenge_method=S256",
    ])
    return {
        "auth_url": f"https://accounts.spotify.com/authorize?{params}",
        "state": state,
    }


def auth_callback(code: str, state: str, db: Session) -> dict:
    """Troca o code pelo access_token e refresh_token."""
    pending = _pending_states.pop(state, None)
    if not pending:
        return {"error": "State inválido ou expirado"}
    verifier = pending["verifier"]
    if not SPOTIFY_REDIRECT_URI:
        return {"error": "SPOTIFY_REDIRECT_URI não configurado"}
    try:
        r = httpx.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "code_verifier": verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        r.raise_for_status()
        d = r.json()
        _save_tokens(db, d["access_token"], d["refresh_token"], d.get("expires_in", 3600))
        return {"status": "ok", "message": "Spotify autenticado com sucesso!"}
    except Exception as e:
        return {"error": f"Falha ao trocar code: {e}"}


# ── Status ────────────────────────────────────────────────────────────────────

def status(db: Session, owner_id: int) -> dict:
    s = db.query(models.PluginState).filter(models.PluginState.name == "spotify").first()
    authenticated = is_authenticated(db)
    return {
        "name": "spotify",
        "enabled": bool(s.enabled) if s else False,
        "authenticated": authenticated,
        "oauth_configured": _HAS_OAUTH,
        "note": (
            "Conectado ao Spotify." if authenticated
            else "Acesse /api/plugins/spotify/auth/start para autenticar." if _HAS_OAUTH
            else "Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no .env."
        ),
    }


# ── Comandos via Spotify Web API ─────────────────────────────────────────────

def _api(method: str, path: str, db: Session, **kwargs) -> Optional[dict]:
    """Faz uma chamada à Spotify Web API. Retorna None se não autenticado."""
    token = _load_access_token(db)
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = httpx.request(method, f"https://api.spotify.com/v1{path}",
                          headers=headers, timeout=10, **kwargs)
        if r.status_code == 204:
            return {"ok": True}
        if r.status_code == 401:
            return None
        r.raise_for_status()
        return r.json() if r.content else {"ok": True}
    except Exception as e:
        print(f"[NEXUS] Spotify API {method} {path} falhou: {e}")
        return None


def _get_active_device(db: Session) -> Optional[str]:
    """Retorna o ID do dispositivo ativo no Spotify."""
    data = _api("GET", "/me/player/devices", db)
    if not data:
        return None
    for d in data.get("devices", []):
        if d.get("is_active"):
            return d["id"]
    devs = data.get("devices", [])
    return devs[0]["id"] if devs else None


def handle(command: str, db: Session, owner_id: int) -> dict:
    """Executa o comando via Spotify Web API quando autenticado,
    ou classifica a intenção para execução pelo app Android."""
    cmd = command.lower()

    # ── Classificação da intenção ────────────────────────────────────────────
    # Checar "playlist" antes de "play" para evitar match prematuro.
    if "playlist" in cmd or "lista" in cmd:
        action = "playlist"
    elif any(k in cmd for k in ("tocar", "play", "toque", "ouvir")):
        action = "play"
    elif any(k in cmd for k in ("pausar", "pause", "parar", "stop")):
        action = "pause"
    elif "próxima" in cmd or "next" in cmd or "pular" in cmd:
        action = "next"
    elif "anterior" in cmd or "previous" in cmd or "voltar faixa" in cmd:
        action = "previous"
    elif "volume" in cmd:
        action = "volume"
    elif "atual" in cmd or "tocando" in cmd or "o que" in cmd:
        action = "current"
    else:
        return {"action": "unknown", "echo": command, "status": "unrecognized"}

    # ── Execução real via Web API ────────────────────────────────────────────
    token = _load_access_token(db)
    if not token:
        # Sem autenticação → retorna intenção para o app Android executar
        return {"action": action, "query": command, "status": "intent_classified"}

    device_id = _get_active_device(db)
    params = {"device_id": device_id} if device_id else {}

    if action == "play":
        # Extrai a query de busca removendo a trigger word
        import re
        query = re.sub(r'\b(tocar|toque|ouvir|play)\b', '', command, flags=re.IGNORECASE).strip()
        if query:
            # Busca a faixa
            search = _api("GET", f"/search?q={query}&type=track&limit=1", db)
            if search:
                tracks = search.get("tracks", {}).get("items", [])
                if tracks:
                    uri = tracks[0]["uri"]
                    name = tracks[0]["name"]
                    artist = tracks[0]["artists"][0]["name"] if tracks[0].get("artists") else ""
                    _api("PUT", "/me/player/play", db, json={"uris": [uri], **params})
                    return {"action": "play", "track": name, "artist": artist, "uri": uri, "status": "playing"}
        # Play genérico (retoma reprodução)
        _api("PUT", "/me/player/play", db, json=params if params else {})
        return {"action": "play", "status": "playing"}

    elif action == "pause":
        _api("PUT", "/me/player/pause", db, params=params if params else None)
        return {"action": "pause", "status": "paused"}

    elif action == "next":
        _api("POST", "/me/player/next", db, params=params if params else None)
        return {"action": "next", "status": "skipped"}

    elif action == "previous":
        _api("POST", "/me/player/previous", db, params=params if params else None)
        return {"action": "previous", "status": "previous"}

    elif action == "playlist":
        import re
        query = re.sub(r'\b(playlist|lista|de)\b', '', command, flags=re.IGNORECASE).strip()
        search = _api("GET", f"/search?q={query}&type=playlist&limit=1", db)
        if search:
            playlists = search.get("playlists", {}).get("items", [])
            if playlists:
                uri = playlists[0]["uri"]
                name = playlists[0]["name"]
                _api("PUT", "/me/player/play", db, json={"context_uri": uri, **params})
                return {"action": "playlist", "name": name, "uri": uri, "status": "playing"}
        return {"action": "playlist", "query": command, "status": "not_found"}

    elif action == "volume":
        import re
        nums = re.findall(r'\d+', cmd)
        vol = int(nums[0]) if nums else 50
        vol = max(0, min(100, vol))
        _api("PUT", f"/me/player/volume?volume_percent={vol}", db, params=params if params else None)
        return {"action": "volume", "volume": vol, "status": "ok"}

    elif action == "current":
        data = _api("GET", "/me/player/currently-playing", db)
        if data and data.get("item"):
            item = data["item"]
            return {
                "action": "current",
                "track": item.get("name"),
                "artist": item["artists"][0]["name"] if item.get("artists") else "",
                "album": item.get("album", {}).get("name"),
                "is_playing": data.get("is_playing", False),
                "status": "ok",
            }
        return {"action": "current", "status": "nothing_playing"}

    return {"action": action, "status": "intent_classified"}
