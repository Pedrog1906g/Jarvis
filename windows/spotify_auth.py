"""Integração Spotify para o JARVIS Windows.

Dois modos de operação:
  1. Via backend (preferido): delega ao endpoint /api/plugins/spotify/command do NEXUS,
     que usa o OAuth2 real com o token do usuário autenticado.
  2. Local Client Credentials (fallback): busca ID de faixa no Spotify sem autenticação
     de usuário — útil apenas para obter o URI de uma música para abrir no app Spotify.

Configuração:
  - Defina SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET no .env do backend para
    o modo OAuth2 (recomendado).
  - Para fallback local, crie spotify_keys.json na mesma pasta com
    {"client_id": "...", "client_secret": "..."}.
"""

from __future__ import annotations
import base64
import json
import os
import urllib.parse
import urllib.request
from typing import Optional

# ── Chaves locais (Client Credentials — fallback) ─────────────────────────────
SPOTIFY_CLIENT_ID = "__SPOTIFY_CLIENT_ID__"
SPOTIFY_CLIENT_SECRET = "__SPOTIFY_CLIENT_SECRET__"

try:
    _here = os.path.dirname(os.path.abspath(__file__))
    _cfg = os.path.join(_here, "spotify_keys.json")
    if os.path.exists(_cfg):
        with open(_cfg, "r", encoding="utf-8") as _f:
            _c = json.load(_f)
        SPOTIFY_CLIENT_ID = _c.get("client_id", SPOTIFY_CLIENT_ID)
        SPOTIFY_CLIENT_SECRET = _c.get("client_secret", SPOTIFY_CLIENT_SECRET)
except Exception:
    pass


def _is_configured() -> bool:
    return (bool(SPOTIFY_CLIENT_ID) and not SPOTIFY_CLIENT_ID.startswith("__")
            and bool(SPOTIFY_CLIENT_SECRET) and not SPOTIFY_CLIENT_SECRET.startswith("__"))


# ── Modo 1: via backend (preferido) ──────────────────────────────────────────

def backend_command(command: str, server_url: str, token: str) -> Optional[dict]:
    """Envia comando Spotify para o backend NEXUS. Retorna resposta JSON ou None."""
    if not server_url or not token:
        return None
    try:
        import requests
        r = requests.post(
            server_url.rstrip("/") + "/api/plugins/spotify/command",
            headers={"Authorization": "Bearer " + token,
                     "Content-Type": "application/json"},
            json={"command": command},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def now_playing(server_url: str, token: str) -> Optional[dict]:
    """Retorna a faixa atual via backend."""
    if not server_url or not token:
        return None
    try:
        import requests
        r = requests.get(
            server_url.rstrip("/") + "/api/plugins/spotify/now-playing",
            headers={"Authorization": "Bearer " + token},
            timeout=10,
        )
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


def get_auth_url(server_url: str, token: str) -> Optional[str]:
    """Inicia fluxo OAuth2 via backend. Retorna URL de autorização do Spotify."""
    if not server_url or not token:
        return None
    try:
        import requests
        r = requests.get(
            server_url.rstrip("/") + "/api/plugins/spotify/auth/start",
            headers={"Authorization": "Bearer " + token},
            timeout=10,
        )
        if r.ok:
            return r.json().get("auth_url")
    except Exception:
        pass
    return None


# ── Modo 2: local Client Credentials (fallback) ───────────────────────────────

def _get_token_local() -> Optional[str]:
    if not _is_configured():
        return None
    try:
        auth = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
        ).decode("ascii")
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=body,
            headers={"Authorization": f"Basic {auth}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("access_token")
    except Exception:
        return None


def search_track(query: str, limit: int = 3) -> Optional[tuple]:
    """Busca faixa via Client Credentials local (sem autenticação de usuário).
    Retorna (track_id, nome, artistas) ou None."""
    token = _get_token_local()
    if not token:
        return None
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.spotify.com/v1/search?q={q}&type=track&limit={limit}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        items = data.get("tracks", {}).get("items", [])
        if not items:
            return None
        it = items[0]
        name = it.get("name", "")
        artists = ", ".join(a.get("name", "") for a in it.get("artists", []))
        return it.get("id"), name, artists
    except Exception:
        return None
