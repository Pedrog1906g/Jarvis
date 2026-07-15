"""Autenticação Spotify (Client Credentials) para o JARVIS tocar a música exata.

Como o repositório é público, as chaves NÃO ficam gravadas aqui: elas são
injetadas automaticamente no momento do build (GitHub Actions) sobre os
placeholders abaixo. Para testar localmente, defina as variáveis de ambiente
SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET ou crie um arquivo spotify_keys.json
na mesma pasta com {"client_id": "...", "client_secret": "..."}.
"""

import os
import json
import base64
import urllib.parse
import urllib.request

# Placeholders — substituídos em tempo de build (não commitados com valor real).
SPOTIFY_CLIENT_ID = "__SPOTIFY_CLIENT_ID__"
SPOTIFY_CLIENT_SECRET = "__SPOTIFY_CLIENT_SECRET__"

# Fallback local (desenvolvimento / testes fora do build).
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


def _is_configured():
    return (bool(SPOTIFY_CLIENT_ID) and not SPOTIFY_CLIENT_ID.startswith("__")
            and bool(SPOTIFY_CLIENT_SECRET) and not SPOTIFY_CLIENT_SECRET.startswith("__"))


def _get_token():
    """Retorna o access_token (Client Credentials) ou None em caso de falha."""
    if not _is_configured():
        return None
    try:
        auth = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("utf-8")
        ).decode("ascii")
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=body,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("access_token")
    except Exception:
        return None


def search_track(query, limit=3):
    """Busca a música exata no Spotify.

    Retorna (track_id, nome, artistas) da melhor faixa, ou None se não achou
    ou se a API estiver indisponível (ex.: conta do app sem Premium).
    """
    token = _get_token()
    if not token:
        return None
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.spotify.com/v1/search?q={q}&type=track&limit={limit}"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = data.get("tracks", {}).get("items", [])
        if not items:
            return None
        # O Spotify já ranqueia por relevância; pegamos a 1ª.
        it = items[0]
        name = it.get("name", "")
        artists = ", ".join(a.get("name", "") for a in it.get("artists", []))
        return it.get("id"), name, artists
    except Exception:
        return None
