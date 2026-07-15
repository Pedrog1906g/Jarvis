"""Conexão NEXUS ↔ Obsidian.

Dois backends (automáticos, sem código fixo):
  • Vault LOCAL: se a env OBSIDIAN_VAULT_PATH apontar para uma pasta existente,
    lê/escreve arquivos .md localmente (sync real com o seu Obsidian no PC).
  • GitHub (padrão): usa a pasta `nexus-llm-wiki/` do repo via GitHub REST API,
    funcionando como um vault remoto (o que o NEXUS "aprende" vira nota lá).

Tudo é best-effort: se o backend falhar, o NEXUS continua funcionando.
"""
import os
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

# Vault local (Obsidian no PC). Se vazio, usa o GitHub como vault remoto.
_LOCAL_VAULT = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()


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
    parts = []
    for note in CONTEXT_NOTES:
        r = _read(note)
        if r:
            text = r[0]
            if note.endswith("Aprendizados (Learnings).md"):
                parts.append(f"### {note.split('/')[-1]}\n{_tail(text, 1600)}")
            else:
                parts.append(f"### {note.split('/')[-1]}\n{_truncate(text, 700)}")
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


def add_learning(title: str, content: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"## {title}\n_{ts}_\n\n{content}\n"
    ok = _append(f"{VAULT}/13 - Aprendizados (Learnings).md", block)
    _CACHE["text"] = None
    return ok


def log_session(summary: str) -> bool:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"- **{ts}**: {summary}"
    return _append(f"{VAULT}/12 - Registro de Sessoes.md", block)


def read_note(path: str) -> str:
    r = _read(path)
    return r[0] if r else ""
