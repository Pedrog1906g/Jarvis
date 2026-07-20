"""Ponte local JARVIS <-> Obsidian (plugin "Local REST API") no PC do dono.

O backend (na nuvem) NÃO enxerga o Obsidian local do Pedro. Por isso o EXE —
que roda no MESMO PC do Obsidian — recebe os aprendizados/sessões via WebSocket
e os escreve aqui, no vault REAL do Pedro. Assim o "segundo cérebro" funciona
de verdade, em tempo real, sem expor o Obsidian na internet.

Requer o plugin "Local REST API" do Obsidian instalado e ligado (porta 27123).
"""
from __future__ import annotations

import logging
import requests

log = logging.getLogger("jarvis.obsidian")

DEFAULT_URL = "http://127.0.0.1:27123"
_OBS_FILE = "obsidian_local.log"


class ObsidianLocal:
    """Cliente mínimo do Obsidian Local REST API (apenas o que o JARVIS usa)."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_URL):
        self.key = (api_key or "").strip()
        self.base = (base_url or DEFAULT_URL).rstrip("/")
        self.available = False

    # ----------------------------- internos -----------------------------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.key}"}

    # ----------------------------- API -----------------------------
    def ping(self) -> bool:
        """Retorna True se o Obsidian (Local REST API) estiver acessível."""
        if not self.key:
            return False
        try:
            r = requests.get(self.base + "/", headers=self._headers(), timeout=4)
            self.available = (r.status_code == 200)
        except Exception:
            self.available = False
        return self.available

    def read(self, path: str):
        if not self.key:
            return None
        try:
            r = requests.get(self.base + "/vault/" + path.lstrip("/"),
                             headers=self._headers(), timeout=8)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        return None

    def write(self, path: str, content: str) -> bool:
        """Sobrescreve (ou cria) a nota no vault local."""
        if not self.key:
            return False
        try:
            r = requests.put(
                self.base + "/vault/" + path.lstrip("/"),
                headers={**self._headers(), "Content-Type": "text/markdown"},
                data=content.encode("utf-8"),
                timeout=8,
            )
            return r.status_code in (200, 201, 204)
        except Exception:
            return False

    def append(self, path: str, block: str) -> bool:
        """Adiciona um bloco ao final da nota (sem duplicar se já existir)."""
        if not self.key or not (block or "").strip():
            return False
        existing = self.read(path) or ""
        if block.strip() in existing:
            return True  # já está lá (reconexão / backfill)
        new = (existing.rstrip() + "\n\n" + block) if existing.strip() else block
        return self.write(path, new)
