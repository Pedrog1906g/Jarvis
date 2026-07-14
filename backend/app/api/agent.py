"""Auto-melhoria do NEXUS (somente dono).

Fluxo seguro:
  1. Lê o GITHUB_TOKEN (variável de ambiente no Render OU token salvo criptografado
     no banco pelo dono, via /api/agent/set_github_token).
  2. Clona o repo num diretório temporário.
  3. Cria uma tag de BACKUP do commit atual.
  4. Pede ao LLM (Groq) UMA alteração de arquivo, restrita a pastas permitidas.
  5. Aplica, comita e empurra para main (dispara CI de APK + deploy do Render).
  6. Em background, monitora o build do GitHub Actions; se FALHAR, faz `git revert`
     e empurra de volta (rollback automático). Nunca força o push.

Tudo é owner-only e as mudanças são limitadas a código de app/backend/docs
(NUNCA .github/workflows, segredos ou arquivos de CI).

Auth git (robusta): usa o token na URL como usuário e DESATIVA o credential
helper (`-c credential.helper=`), evitando que ambientes como o Render "limppem"
as credenciais da remote.url após o clone. O status é persistido no BANCO
(confiável entre instâncias do Render).
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
GITHUB_TOKEN_ENV = os.getenv("GITHUB_TOKEN", "")
STATUS_KEY = "self_improve_status"

# Frases que disparam a auto-melhoria direto no chat (só o dono).
TRIGGER_PHRASES = (
    "auto melhore", "auto-melhore", "se auto melhore", "auto melhorar",
    "melhore seu código", "melhore o código", "melhore a si mesmo",
    "melhore seu app", "se auto aperfeiçoe", "aperfeiçoe seu código",
    "melhore seu sistema", "se atualize", "atualize a si mesmo",
)


def _run(cmd, cwd, timeout=150):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _git_net(args, cwd, token, timeout=150):
    """Roda um comando git de REDE de forma robusta em QUALQUER ambiente.

    Estratégia tripla (para vencer configs globais como as do Render):
      1. insteadOf na própria linha do comando injeta o token na URL
         (https://github.com/... -> https://TOKEN@github.com/...), com prioridade
         máxima, derrotando qualquer insteadOf global que "limpe" o usuário.
      2. GIT_ASKPASS embutido fornece o token em tempo de execução (backup).
      3. credential.helper desativado para não cachear/reescrever.
    """
    script = tempfile.NamedTemporaryFile(
        mode="w", suffix=".sh", delete=False, prefix="nexus-askpass-"
    )
    script.write(
        '#!/bin/sh\ncase "$1" in\n  *Username*) echo "' + token + '" ;;\n'
        '  *Password*) echo "" ;;\nesac\n'
    )
    script.close()
    os.chmod(script.name, 0o700)
    env = dict(os.environ)
    env["GIT_ASKPASS"] = script.name
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(
            [
                "git",
                "-c", "credential.helper=",
                "-c", f"url.https://{token}@github.com/.insteadOf=https://github.com/",
            ] + args,
            cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env,
        )
    finally:
        try:
            os.unlink(script.name)
        except Exception:
            pass


def _status(stage: str, status: str, message: str = "", backup_tag: str = "", run_url: str = ""):
    """Persiste o status da auto-melhoria no BANCO (não em /tmp), para funcionar
    de forma confiável mesmo com várias instâncias do Render."""
    payload = json.dumps({
        "stage": stage, "status": status, "message": message,
        "backup_tag": backup_tag, "run_url": run_url, "ts": int(time.time()),
    })
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key=STATUS_KEY).first()
            if row:
                row.value = payload
            else:
                row = models.Setting(key=STATUS_KEY, value=payload)
                db.add(row)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


def _configure_identity(cwd):
    """Define a identidade do git no repo clonado (necessário p/ commitar/reverter)."""
    _run(["git", "config", "user.email", "pedrogentil797@gmail.com"], cwd, timeout=30)
    _run(["git", "config", "user.name", "Pedro Gentil Bastos"], cwd, timeout=30)


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


def get_github_token() -> str:
    """Token do GitHub: prioriza variável de ambiente; senão, lê criptografado do banco."""
    if GITHUB_TOKEN_ENV:
        return GITHUB_TOKEN_ENV
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import decrypt
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key="github_token").first()
            return decrypt(row.value) if row and row.value else ""
        finally:
            db.close()
    except Exception:
        return ""


def _latest_build_run(commit_sha: str):
    token = get_github_token()
    if not token:
        return None
    url = f"https://api.github.com/repos/{REPO}/actions/runs?per_page=20"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
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
                try:
                    tmp = tempfile.mkdtemp()
                    token = get_github_token()
                    _git_net(["clone", f"https://github.com/{REPO}.git", tmp], "/tmp", token, 150)
                    _configure_identity(tmp)
                    _run(["git", "revert", "--no-edit", commit_sha], cwd=tmp, timeout=60)
                    res = _git_net(
                        ["push", f"https://github.com/{REPO}.git", "main"],
                        tmp, token, 60,
                    )
                    if res.returncode == 0:
                        _status("rolled_back", "reverted", f"build falhou; revertido automaticamente. {conclusion}", backup_tag, run_url)
                    else:
                        _status("rolled_back", "manual_needed", f"build falhou; revert manual necessário. {res.stderr[:200]}", backup_tag, run_url)
                except Exception as e:
                    _status("rolled_back", "manual_needed", f"erro ao reverter: {e}", backup_tag, run_url)
                return
    _status("monitoring", "timeout", "timeout monitorando o build (verifique em Actions).", backup_tag)


def _do_self_improve(request_text: str) -> dict:
    token = get_github_token()
    if not token:
        _status("error", "no_token", "GITHUB_TOKEN não configurado (nem no Render, nem salvo no app).")
        return {"status": "error", "message": "sem token"}
    tmp = tempfile.mkdtemp()
    clone = _git_net(["clone", f"https://github.com/{REPO}.git", tmp], "/tmp", token, 150)
    if clone.returncode != 0:
        _status("error", "clone_failed", "falha ao clonar o repo: " + clone.stderr[:200])
        return {"status": "error", "message": "falha ao clonar o repo: " + clone.stderr[:200]}
    _configure_identity(tmp)
    _status("cloned", "running", "repo clonado", "")

    # 2) backup
    rev = _run(["git", "rev-parse", "HEAD"], cwd=tmp, timeout=30).stdout.strip()
    backup_tag = f"backup-{int(time.time())}"
    _run(["git", "tag", backup_tag, rev], cwd=tmp, timeout=30)
    _git_net(["push", f"https://github.com/{REPO}.git", backup_tag], tmp, token, 60)

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
        _status("error", "llm_invalid", "LLM não retornou mudança válida: " + str(llm_out)[:300])
        return {"status": "error", "message": "LLM não retornou mudança válida: " + str(llm_out)[:300]}
    path = data["path"]
    content = data.get("content", "")
    if not _path_allowed(path):
        _status("error", "path_denied", f"caminho não permitido por segurança: {path}")
        return {"status": "error", "message": f"caminho não permitido por segurança: {path}"}
    if not content.strip():
        _status("error", "empty", "conteúdo vazio recusado.")
        return {"status": "error", "message": "conteúdo vazio recusado."}

    # 4) escreve, comita, empurra
    full = os.path.join(tmp, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    _run(["git", "add", "-A"], cwd=tmp, timeout=30)
    commit = _run(["git", "commit", "-m", f"auto-improve(owner): {request_text[:80]}"], cwd=tmp, timeout=60)
    if commit.returncode != 0:
        _status("error", "commit_failed", "nada para commitar ou erro: " + commit.stderr[:200])
        return {"status": "error", "message": "nada para commitar ou erro: " + commit.stderr[:200]}
    push = _git_net(["push", f"https://github.com/{REPO}.git", "main"], tmp, token, 60)
    if push.returncode != 0:
        _status("error", "push_failed", "falha ao empurrar: " + push.stderr[:200])
        return {"status": "error", "message": "falha ao empurrar: " + push.stderr[:200]}

    sha = _run(["git", "rev-parse", "HEAD"], cwd=tmp, timeout=30).stdout.strip()
    _status("pushed", "running", "empurrado — build do APK iniciado.", backup_tag)
    _poll_and_rollback(sha, backup_tag)  # roda dentro da thread de background
    return {
        "status": "started",
        "backup_tag": backup_tag,
        "message": "Mudança enviada. Estou monitorando o build; se falhar, reverterei sozinho. Backup: " + backup_tag,
    }


def trigger_self_improve(text: str) -> bool:
    """Inicia a auto-melhoria em background (usado pelo chat ou pelo endpoint)."""
    if not get_github_token():
        _status("error", "no_token", "GITHUB_TOKEN não configurado.")
        return False
    _status("queued", "running", "auto-melhoria na fila (executando em background)...", "")
    threading.Thread(target=_do_self_improve, args=(text,), daemon=True).start()
    return True


def detect_self_improve(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in TRIGGER_PHRASES)


class ImproveRequest(BaseModel):
    request: str


class GithubTokenRequest(BaseModel):
    token: str


@router.post("/self_improve")
def self_improve(body: ImproveRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode usar auto-melhoria"}
    if not get_github_token():
        return {"status": "error",
                "message": "GITHUB_TOKEN não configurado. Vá em Ajustes → Auto-melhoria e cole seu token do GitHub uma vez."}
    trigger_self_improve(body.request)
    return {
        "status": "started",
        "message": "Auto-melhoria iniciada em background. Pergunte 'status da auto-melhoria' p/ acompanhar. "
                   "Se o build do APK falhar, eu revertero sozinho (backup automático).",
    }


@router.get("/self_improve/status")
def self_improve_status(user: models.User = Depends(get_current_user)):
    data = {"status": "idle", "message": "nenhuma auto-melhoria iniciada ainda."}
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key=STATUS_KEY).first()
            if row and row.value:
                data = json.loads(row.value)
        finally:
            db.close()
    except Exception:
        pass
    data["token_configured"] = bool(get_github_token())
    data["token_source"] = "env" if GITHUB_TOKEN_ENV else ("db" if get_github_token() else "none")
    return data


@router.post("/set_github_token")
def set_github_token(body: GithubTokenRequest, user: models.User = Depends(get_current_user)):
    if user.username != "owner":
        return {"status": "error", "message": "apenas o dono pode salvar o token"}
    tok = (body.token or "").strip()
    if not tok:
        return {"status": "error", "message": "token vazio"}
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import encrypt
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key="github_token").first()
            enc = encrypt(tok)
            if row:
                row.value = enc
            else:
                row = models.Setting(key="github_token", value=enc)
                db.add(row)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "message": f"erro ao salvar: {e}"}
    return {"status": "ok", "message": "Token do GitHub salvo com segurança (criptografado no banco)."}


@router.get("/github_token_status")
def github_token_status(user: models.User = Depends(get_current_user)):
    tok = get_github_token()
    return {"configured": bool(tok), "source": "env" if GITHUB_TOKEN_ENV else ("db" if tok else "none")}
