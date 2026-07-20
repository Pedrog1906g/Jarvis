"""Conexão NEXUS <-> Obsidian (segundo cérebro / análise de dados).

Três modos (automáticos, sem código fixo), em ordem de prioridade:
  • Obsidian Local REST API: se a chave OBSIDIAN_API_KEY estiver configurada, o
    NEXUS lê/escreve o seu vault REAL do Obsidian (plugin "Local REST API") usando
    a chave. Funciona quando o backend consegue alcançar o Obsidian (ex.: backend
    rodando no mesmo PC, ou Obsidian acessível). É o "segundo cérebro" de verdade.
  • Vault LOCAL: se OBSIDIAN_VAULT_PATH apontar para uma pasta, lê/escreve .md localmente.
  • GitHub (padrão na nuvem): usa a pasta `nexus-llm-wiki/` do repo via GitHub REST API.

Tudo é best-effort: se algo falhar, cai no próximo modo e o NEXUS continua funcionando.
"""
import os
import time
from datetime import datetime, timezone

import httpx

from app.services import github_fs
from app.db import models
from app.core.ws_manager import manager  # avisa o EXE (Obsidian local do dono)

VAULT = "nexus-llm-wiki"
CONTEXT_NOTES = [
    f"{VAULT}/09 - Memoria da IA.md",
    f"{VAULT}/11 - Conexao com Obsidian.md",
    f"{VAULT}/13 - Aprendizados (Learnings).md",
]
_CACHE = {"text": None, "ts": 0}
_TTL = 300

# Vault local (Obsidian no PC). Se vazio, usa o GitHub como vault remoto.
_LOCAL_VAULT = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
# Obsidian Local REST API (plugin "Local REST API").
_OBS_KEY_ENV = os.getenv("OBSIDIAN_API_KEY", "").strip()
_OBS_URL_ENV = os.getenv("OBSIDIAN_API_URL", "http://127.0.0.1:27123").rstrip("/")


# --------------------------------------------------------------------------- #
# Configuração da chave (banco tem prioridade sobre o ambiente)               #
# --------------------------------------------------------------------------- #
def _db_value(setting_key: str) -> str:
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import decrypt
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key=setting_key).first()
            return decrypt(row.value) if row and row.value else ""
        finally:
            db.close()
    except Exception:
        return ""


def get_obsidian_key() -> str:
    k = _db_value("obsidian_api_key")
    if k:
        return k
    return _OBS_KEY_ENV


def get_obsidian_url() -> str:
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key="obsidian_api_url").first()
            if row and row.value:
                return row.value.strip().rstrip("/")
        finally:
            db.close()
    except Exception:
        pass
    return _OBS_URL_ENV


# --------------------------------------------------------------------------- #
# Obsidian Local REST API (plugin "Local REST API")                          #
# --------------------------------------------------------------------------- #
def _rest(method: str, path: str, *, body=None):
    key = get_obsidian_key()
    if not key:
        return None
    url = f"{get_obsidian_url()}/vault/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        if method == "GET":
            r = httpx.get(url, headers=headers, timeout=15)
        elif method == "PUT":
            headers["Content-Type"] = "text/markdown"
            r = httpx.put(url, headers=headers, content=body, timeout=15)
        else:
            return None
        return r if r.status_code in (200, 201) else None
    except Exception:
        return None


def rest_read(path: str):
    r = _rest("GET", path)
    return r.text if r else None


def rest_write(path: str, content: str) -> bool:
    return _rest("PUT", path, body=content) is not None


def rest_ping() -> bool:
    key = get_obsidian_key()
    if not key:
        return False
    try:
        r = httpx.get(f"{get_obsidian_url()}/",
                      headers={"Authorization": f"Bearer {key}"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def _obsidian_context() -> str:
    """Lê as notas do vault real do Obsidian e monta o contexto do 'segundo cérebro'."""
    if not get_obsidian_key():
        return None
    try:
        key = get_obsidian_key()
        r = httpx.get(f"{get_obsidian_url()}/vault/",
                      headers={"Authorization": f"Bearer {key}"}, timeout=15)
        if r.status_code != 200:
            return None
        files = r.json() if "application/json" in r.headers.get("content-type", "") else []
        md_files = [f.get("path") for f in files
                    if isinstance(f, dict) and str(f.get("path", "")).lower().endswith(".md")]
        parts = []
        budget = 6000
        for p in md_files:
            content = rest_read(p)
            if not content:
                continue
            chunk = f"### {p}\n{content[:1500]}"
            if budget - len(chunk) <= 0:
                parts.append("... (demais notas omitidas por limite de contexto)")
                break
            parts.append(chunk)
            budget -= len(chunk)
        return "\n\n".join(parts) if parts else None
    except Exception:
        return None


def _obsidian_append(note: str, block: str) -> bool:
    existing = rest_read(note) or ""
    new = (existing.rstrip() + "\n\n" + block) if existing.strip() else block
    return rest_write(note, new)


# --------------------------------------------------------------------------- #
# Backends locais / GitHub (fallback)                                        #
# --------------------------------------------------------------------------- #
def _local_path(note: str) -> str:
    rel = note[len(VAULT) + 1:] if note.startswith(VAULT + "/") else note
    return os.path.join(_LOCAL_VAULT, rel)


def _read(note: str):
    """Retorna (conteudo, sha) ou None."""
    if _LOCAL_VAULT:
        p = _local_path(note)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return f.read(), None
            except Exception:
                return None
        return None
    return github_fs.gh_read(note)


def _write(note: str, content: str, message: str, sha=None) -> bool:
    if _LOCAL_VAULT:
        p = _local_path(note)
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False
    return github_fs.gh_write(note, content, message, sha)


def _truncate(s: str, n: int = 900) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "\n... (truncado)"


def _tail(s: str, n: int = 1600) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else "... (aprendizados mais antigos omitidos)\n" + s[-n:]


def load_context(force: bool = False) -> str:
    now = time.time()
    if not force and _CACHE["text"] is not None and now - _CACHE["ts"] < _TTL:
        return _CACHE["text"]
    # 1) Obsidian real (Local REST API) tem prioridade quando configurado.
    text = _obsidian_context()
    # 2) Fallback: notas fixas do vault (local ou GitHub).
    if not text:
        parts = []
        for note in CONTEXT_NOTES:
            r = _read(note)
            if r:
                t = r[0]
                if note.endswith("Aprendizados (Learnings).md"):
                    parts.append(f"### {note.split('/')[-1]}\n{_tail(t, 1600)}")
                else:
                    parts.append(f"### {note.split('/')[-1]}\n{_truncate(t, 700)}")
        text = "\n\n".join(parts)
    _CACHE["text"] = text
    _CACHE["ts"] = now
    return text


def chat_context_message() -> dict:
    text = load_context()
    if not text:
        return None
    return {
        "role": "system",
        "content": "CONTEXTO DO VAULT (Obsidian / LLM Wiki — conhecimento vivo do NEXUS):\n" + text,
    }


def _append(note: str, block: str) -> bool:
    r = _read(note)
    sha = r[1] if r else None
    existing = r[0] if r else ""
    new = (existing.rstrip() + "\n\n" + block) if existing.strip() else block
    return _write(note, new, f"obsidian: atualiza {note}", sha)


def _broadcast_learning(note: str, block: str):
    """Avisa o EXE (que roda no PC do dono, junto do Obsidian) para gravar o
    bloco no vault REAL. O backend na nuvem não alcança o Obsidian local, então
    o EXE faz a ponte. Best-effort: ignora se ninguém estiver conectado."""
    try:
        manager.broadcast_sync({"type": "obsidian_sync", "note": note, "block": block})
    except Exception:
        pass


def add_learning(title: str, content: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"## {title}\n_{ts}_\n\n{content}\n"
    # Avisa o EXE para espelhar no Obsidian real (segundo cérebro).
    _broadcast_learning("NEXUS Aprendizados.md", block)
    # Prefere o Obsidian real quando configurado.
    if get_obsidian_key() and _obsidian_append("NEXUS Aprendizados.md", block):
        _CACHE["text"] = None
        return True
    ok = _append(f"{VAULT}/13 - Aprendizados (Learnings).md", block)
    _CACHE["text"] = None
    return ok


def log_session(summary: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"- **{ts}**: {summary}"
    _broadcast_learning("NEXUS Registro de Sessoes.md", block)
    if get_obsidian_key() and _obsidian_append("NEXUS Registro de Sessoes.md", block):
        return True
    return _append(f"{VAULT}/12 - Registro de Sessoes.md", block)


def read_note(path: str) -> str:
    r = _read(path)
    return r[0] if r else ""


def obsidian_status() -> dict:
    key = get_obsidian_key()
    mode = "obsidian_rest" if key else ("local" if _LOCAL_VAULT else "github_vault")
    reachable = rest_ping() if key else False
    return {
        "configured": bool(key),
        "url": get_obsidian_url(),
        "mode": mode,
        "reachable": reachable,
    }
