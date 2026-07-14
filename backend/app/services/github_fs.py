"""Acesso leve ao conteúdo do repositório via GitHub REST API.

Usado pela integração com o Obsidian: lê e escreve as notas do vault (que vivem na
pasta `nexus-llm-wiki/` do repo) sem usar `git`. Reutiliza o mesmo token do GitHub
(token do banco tem prioridade, env como fallback).
"""
import os
import base64
import httpx
from urllib.parse import quote

from app.db.database import SessionLocal
from app.db import models
from app.core.crypto import decrypt
from app.config import GITHUB_TOKEN as ENV_TOKEN, GITHUB_REPO

API_BASE = "https://api.github.com"


def get_token():
    try:
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key="github_token").first()
            tok = decrypt(row.value) if row and row.value else ""
        finally:
            db.close()
        if tok:
            return tok
    except Exception:
        pass
    return ENV_TOKEN


def _url(path: str) -> str:
    return f"{API_BASE}/repos/{GITHUB_REPO}/contents/{quote(path, safe='/')}"


def gh_read(path: str):
    """Retorna (conteudo, sha) ou None se não existir/erro."""
    token = get_token()
    if not token:
        return None
    try:
        r = httpx.get(
            _url(path),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=30,
        )
        if r.status_code == 200:
            d = r.json()
            return base64.b64decode(d["content"]).decode("utf-8"), d["sha"]
    except Exception:
        pass
    return None


def gh_write(path: str, content: str, message: str, sha=None) -> bool:
    token = get_token()
    if not token:
        return False
    body = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        body["sha"] = sha
    try:
        r = httpx.put(
            _url(path),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json=body,
            timeout=30,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False
