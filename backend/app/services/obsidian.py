"""Conexão NEXUS ↔ Obsidian (vault LLM Wiki no repositório).

- load_context(): lê notas curadas do vault e monta o contexto que o NEXUS "enxerga"
  (o sistema fica conectado ao conhecimento do vault).
- add_learning() / log_session(): escrevem de volta no vault (via GitHub API), então o
  que o NEXUS aprende fica visível no Obsidian e vice-versa. É assim que o NEXUS
  "aprende com o mentor" (o agente que o construiu) — o ensino vira contexto das
  próximas conversas.
"""
import time
from datetime import datetime, timezone

from app.services import github_fs

VAULT = "nexus-llm-wiki"
CONTEXT_NOTES = [
    f"{VAULT}/09 - Memoria da IA.md",
    f"{VAULT}/11 - Conexao com Obsidian.md",
    f"{VAULT}/13 - Aprendizados (Learnings).md",
]
_CACHE = {"text": None, "ts": 0}
_TTL = 300


def _truncate(s: str, n: int = 900) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "\n... (truncado)"


def load_context(force: bool = False) -> str:
    now = time.time()
    if not force and _CACHE["text"] is not None and now - _CACHE["ts"] < _TTL:
        return _CACHE["text"]
    parts = []
    for note in CONTEXT_NOTES:
        r = github_fs.gh_read(note)
        if r:
            parts.append(f"### {note.split('/')[-1]}\n{_truncate(r[0])}")
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
    r = github_fs.gh_read(note)
    sha = r[1] if r else None
    existing = r[0] if r else ""
    new = (existing.rstrip() + "\n\n" + block) if existing.strip() else block
    return github_fs.gh_write(note, new, f"obsidian: atualiza {note}", sha)


def add_learning(title: str, content: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"## {title}\n_{ts}_\n\n{content}\n"
    ok = _append(f"{VAULT}/13 - Aprendizados (Learnings).md", block)
    _CACHE["text"] = None  # invalida cache para refletir o novo aprendizado
    return ok


def log_session(summary: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"- **{ts}**: {summary}"
    return _append(f"{VAULT}/12 - Registro de Sessoes.md", block)
