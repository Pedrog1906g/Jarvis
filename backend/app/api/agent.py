"""Auto-melhoria do NEXUS (somente dono).

Fluxo seguro:
  1. Clona o repo (via GITHUB_TOKEN) num diretório temporário.
  2. Cria uma tag de BACKUP do commit atual.
  3. Pede ao LLM (Groq) UMA alteração de arquivo, restrita a pastas permitidas.
  4. Aplica, comita e empurra para main (dispara CI de APK + deploy do Render).
  5. Em background, monitora o build do GitHub Actions; se FALHAR, faz `git revert`
     e empurra de volta (rollback automático). Nunca força o push (respeita a
     branch protection do main).

Tudo é owner-only e as mudanças são limitadas a código de app/backend/docs
(NUNCA .github/workflows, segredos ou arquivos de CI).
"""
import os
import json
import time
import threading
import tempfile
import subprocess
from typing import Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db import models
from app.core.llm import complete_chat

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Pastas que o LLM pode tocar. .github/ e segredos ficam FORA dessa lista de propósito.
ALLOWED_PREFIXES = (
    "android/app/src/main/",
    "backend/app/",
    "backend/requirements.txt",
    "backend/.env.example",
    "render.yaml",
    "DEPLOY.md",
    "README.md",
    "CHANGELOG.md",
)

REPO = os.getenv("GITHUB_REPO", "Pedrog1906g/Jarvis")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
STATUS_FILE = "/tmp/nexus_selfimprove_status.json"


def _status(stage: str, status: str, message: str = "", backup_tag: str = "", run_url: str = ""):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({
                "stage": stage, "status": status, "message": message,
                "backup_tag": backup_tag, "run_url": run_url, "ts": int(time.time()),
            }, f)
    except Exception:
        pass


def _run(cmd, cwd, timeout=150):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _extract_json(text: str) -> Optional[dict]:
    try:
        s = text.strip()
        if "```" in s:
            s = s.split("```", 2)[1]
            if s.startswith("json"):
                s = s[4:]
        return json.loads(s)
    except Exception:
        return None


def _path_allowed(path: str) -> bool:
    if ".." in path or path.startswith("/"):
        return False
    if ".github/" in path or "workflows" in path:
        return False
    return any(path.startswith(p) or path == p for p in ALLOWED_PREFIXES)


def _latest_build_run(commit_sha: str):
    """Retorna o run do GitHub Actions (build.yml) disparado por esse commit."""
    url = f"https://api.github.com/repos/{REPO}/actions/runs?per_page=20"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        r = httpx.get(url, headers=headers, timeout=30)
        data = r.json()
        for run in data.get("workflow_runs", []):
            if run.get("head_sha") == commit_sha:
                return run
    except Exception:
        pass
    return None


def _poll_and_rollback(commit_sha: str, backup_tag: str):
    """Monitora o build; se falhar, reverte o commit (sem force push)."""
    _status("monitoring", "running", "acompanhando o build do APK...", backup_tag)
    deadline = time.time() + 20 * 60
    while time.time() < deadline:
        time.sleep(30)
        run = _latest_build_run(commit_sha)
        if not run:
            continue
        status = run.get("status")
        conclusion = run.get("conclusion")
        run_url = run.get("html_url", "")
        if status == "completed":
            if conclusion == "success":
                _status("done", "success", "build OK — mudança aplicada e publicada.", backup_tag, run_url)
                return
            else:
                # Falhou: reverte o commit (git revert cria novo commit, sem force push).
                try:
                    tmp = tempfile.mkdtemp()
                    _run(["git", "clone", f"https://{GITHUB_TOKEN}@github.com/{REPO}.git", tmp], cwd="/tmp", timeout=150)
                    _run(["git", "revert", "--no-edit", commit_sha], cwd=tmp, timeout=60)
                    res = _run(["git", "push", "origin", "main"], cwd=tmp, timeout=60)
                    if res.returncode == 0:
                        _status("rolled_back", "reverted", f"build falhou; revertido automaticamente. {conclusion}", backup_tag, run_url)
                    else:
                        _status("rolled_back", "manual_needed", f"build falhou; revert manual necessário. {res.stderr[:200]}", backup_tag, run_url)
                except Exception as e:
                    _status("rolled_back", "manual_needed", f"erro ao reverter: {e}", backup_tag, run_url)
                return
    _status("monitoring", "timeout", "timeout monitorando o build (verifique em Actions).", backup_tag)


def _do_self_improve(request_text: str) -> dict:
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "GITHUB_TOKEN não configurado no Render (Environment)."}
    tmp = tempfile.mkdtemp()
    clone = _run(["git", "clone", f"https://{GITHUB_TOKEN}@github.com/{REPO}.git", tmp], cwd="/tmp", timeout=150)
    if clone.returncode != 0:
        return {"status": "error", "message": "falha ao clonar o repo: " + clone.stderr[:200]}
    _status("cloned", "running", "repo clonado", "")

    # 2) backup
    rev = _run(["git", "rev-parse", "HEAD"], cwd=tmp, timeout=30).stdout.strip()
    backup_tag = f"backup-{int(time.time())}"
    _run(["git", "tag", backup_tag, rev], cwd=tmp, timeout=30)
    _run(["git", "push", "origin", backup_tag], cwd=tmp, timeout=60)

    # 3) LLM propõe a mudança (1 arquivo, pasta permitida)
    system = (
        "Você é um engenheiro sênior Android (Kotlin/Jetpack Compose) e Python/FastAPI. "
        "O usuário pediu uma melhoria no app NEXUS. Responda SOMENTE com um JSON válido, sem comentários: "
        '{"path":"caminho/relativo/do/arquivo","content":"conteúdo COMPLETO e correto do arquivo após a mudança"}. '
        "Regras: altere APENAS UM arquivo; mantenha o estilo existente; o código deve compilar; "
        "não mexa em CI, segredos ou .github/. Se não conseguir, retorne {\"path\":\"\",\"content\":\"\",\"note\":\"motivo\"}."
    )
    user_msg = f"Pedido do dono: {request_text}\nRepositório: {REPO}. Proponha a mudança."
    llm_out = complete_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
        temperature=0.2,
    )
    data = _extract_json(llm_out)
    if not data or not data.get("path"):
        return {"status": "error", "message": "LLM não retornou mudança válida: " + str(llm_out)[:300]}
    path = data["path"]
    content = data.get("content", "")
    if not _path_allowed(path):
        return {"status": "error", "message": f"caminho não permitido por segurança: {path}"}
    if not content.strip():
        return {"status": "error", "message": "conteúdo vazio recusado."}

    # 4) escreve, comita, empurra
    full = os.path.join(tmp, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    _run(["git", "add", "-A"], cwd=tmp, timeout=30)
    commit = _run(["git", "commit", "-m", f"auto-improve(owner): {request_text[:80]}"], cwd=tmp, timeout=60)
    if commit.returncode != 0:
        return {"status": "error", "message": "nada para commitar ou erro: " + commit.stderr[:200]}
    push = _run(["git", "push", "origin", "main"], cwd=tmp, timeout=60)
    if push.returncode != 0:
        return {"status": "error", "message": "falha ao empurrar: " + push.stderr[:200]}

    sha = _run(["git", "rev-parse", "HEAD"], cwd=tmp, timeout=30).stdout.strip()
    _status("pushed", "running", "empurrado — build do APK iniciado.", backup_tag)
    _poll_and_rollback(sha, backup_tag)  # roda dentro da thread de background
    return {
        "status": "started",
        "backup_tag": backup_tag,
        "message": "Mudança enviada. Estou monitorando o build; se falhar, reverterei sozinho. Backup: " + backup_tag,
    }


class ImproveRequest(BaseModel):
    request: str


@router.post("/self_improve")
def self_improve(body: ImproveRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode usar auto-melhoria"}
    _status("queued", "running", "auto-melhoria na fila (executando em background)...", "")
    threading.Thread(target=_do_self_improve, args=(body.request,), daemon=True).start()
    return {
        "status": "started",
        "message": "Auto-melhoria iniciada em background. Pergunte 'status da auto-melhoria' p/ acompanhar. "
                   "Se o build do APK falhar, eu revertero sozinho (backup automático).",
    }


@router.get("/self_improve/status")
def self_improve_status(user: models.User = Depends(get_current_user)):
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"status": "idle", "message": "nenhuma auto-melhoria iniciada ainda."}
