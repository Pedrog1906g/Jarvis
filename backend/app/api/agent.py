"""Auto-melhoria do NEXUS (somente dono) — 100% via GitHub REST API (sem git).

Fluxo seguro e sem dependência de `git` (o Render nega push via git com 403,
mas a REST API com token Bearer funciona de verdade):

  1. Lê o GITHUB_TOKEN (variável de ambiente no Render OU token salvo
     criptografado no banco pelo dono, via /api/agent/set_github_token).
  2. Lê o SHA atual da branch main e cria uma tag de BACKUP (best-effort).
  3. Lê o conteúdo atual do arquivo alvo (GET /contents) como backup de rollback.
  4. Pede ao LLM (Groq) UMA alteração de arquivo, restrita a pastas permitidas.
  5. Aplica a mudança com PUT /repos/{repo}/contents/{path} (cria commit na main,
     dispara CI de APK + deploy do Render). Nenhum `git` envolvido.
  6. Em background, monitora o build do GitHub Actions; se FALHAR, restaura o
     conteúdo original do arquivo (PUT/DELETE) — rollback automático.

Tudo é owner-only e as mudanças são limitadas a código de app/backend/docs
(NUNCA .github/workflows, segredos ou arquivos de CI).
"""
import os
import json
import time
import base64
import threading

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
API_BASE = "https://api.github.com"

# Frases que disparam a auto-melhoria direto no chat (só o dono).
TRIGGER_PHRASES = (
    "auto melhore", "auto-melhore", "se auto melhore", "auto melhorar",
    "melhore seu código", "melhore o código", "melhore a si mesmo",
    "melhore seu app", "se auto aperfeiçoe", "aperfeiçoe seu código",
    "melhore seu sistema", "se atualize", "atualize a si mesmo",
)


# --------------------------------------------------------------------------- #
# Helpers de rede (GitHub REST API) — nenhum `git` é usado                   #
# --------------------------------------------------------------------------- #
def _gh(method: str, path: str, *, json_body=None, params=None, token: str = ""):
    token = token or get_github_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{API_BASE}/{path}"
    return httpx.request(method, url, headers=headers, json=json_body,
                         params=params, timeout=60)


def _get_head_sha(token: str) -> str:
    r = _gh("GET", f"repos/{REPO}/branches/main", token=token)
    r.raise_for_status()
    return r.json()["commit"]["sha"]


def _get_file(path: str, token: str):
    r = _gh("GET", f"repos/{REPO}/contents/{path}", token=token)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    d = r.json()
    content = base64.b64decode(d["content"]).decode("utf-8")
    return {"content": content, "sha": d["sha"]}


def _put_file(path: str, content: str, sha, message: str, token: str) -> str:
    body = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        body["sha"] = sha
    r = _gh("PUT", f"repos/{REPO}/contents/{path}", json_body=body, token=token)
    r.raise_for_status()
    return r.json()["commit"]["sha"]


def _delete_file(path: str, sha: str, message: str, token: str) -> str:
    body = {"message": message, "sha": sha, "branch": "main"}
    r = _gh("DELETE", f"repos/{REPO}/contents/{path}", json_body=body, token=token)
    r.raise_for_status()
    return r.json()["commit"]["sha"]


def _create_backup_tag(tag: str, head_sha: str, token: str):
    """Cria uma tag de backup (best-effort). Não interrompe o fluxo se falhar."""
    try:
        _gh("POST", f"repos/{REPO}/git/refs",
            json_body={"ref": f"refs/tags/{tag}", "sha": head_sha}, token=token)
    except Exception as e:
        print("[NEXUS] aviso: não criou tag de backup:", e)


# --------------------------------------------------------------------------- #
# Status persistido no BANCO (confiável entre instâncias do Render)          #
# --------------------------------------------------------------------------- #
def _status(stage, status, message="", backup_tag="", run_url=""):
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


def _extract_json(text):
    try:
        s = text.strip()
        if "```" in s:
            s = s.split("```", 2)[1]
            if s.startswith("json"):
                s = s[4:]
        return json.loads(s)
    except Exception:
        return None


def _parse_change(text):
    """Extrai (path, content) da resposta do LLM.

    Aceita dois formatos:
      - JSON: {"path": "...", "content": "..."}  (fallback de compatibilidade)
      - Formato robusto: linha 'PATH: <caminho>' seguida de um bloco de código
        com o conteúdo COMPLETO do arquivo (sem necessidade de escapar JSON,
        o que evita falhas com quebras de linha/aspas no conteúdo).
    """
    if not text:
        return None
    s = text.strip()
    # 1) JSON (compatibilidade)
    j = _extract_json(s)
    if isinstance(j, dict) and j.get("path") and j.get("content"):
        return j["path"].strip(), j["content"]
    # 2) PATH: + bloco de código
    lines = s.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().upper().startswith("PATH:"):
            path = ln.split(":", 1)[1].strip().strip('`"\'')
            path = path[1:] if path.startswith("/") else path
            if path.startswith("./"):
                path = path[2:]
            rest = "\n".join(lines[i + 1:])
            if "```" in rest:
                parts = rest.split("```")
                content = parts[1] if len(parts) > 1 else rest
            else:
                content = rest
            content = content.strip()
            if path and content:
                return path, content
            break
    return None


def _path_allowed(path: str) -> bool:
    if ".." in path or path.startswith("/"):
        return False
    if ".github/" in path or "workflows" in path:
        return False
    return any(path.startswith(p) or path == p for p in ALLOWED_PREFIXES)


def get_github_token() -> str:
    """Token do GitHub: prioriza o token salvo pelo dono no banco (seguro, owner-only);
    cai no GITHUB_TOKEN do ambiente como fallback (ex.: definido no Render).

    Motivo: o token de ambiente no Render pode ser limitado (somente leitura). O dono
    pode gravar um token com permissão de escrita via /api/agent/set_github_token e ele
    passa a ser usado com prioridade, sem precisar mexer nas variáveis de ambiente.
    """
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import decrypt
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
    return GITHUB_TOKEN_ENV


def _token_source() -> str:
    """De onde vem efetivamente o token (banco tem prioridade sobre o ambiente)."""
    try:
        from app.db.database import SessionLocal
        from app.core.crypto import decrypt
        db = SessionLocal()
        try:
            row = db.query(models.Setting).filter_by(key="github_token").first()
            if row and row.value and decrypt(row.value):
                return "db"
        finally:
            db.close()
    except Exception:
        pass
    return "env" if GITHUB_TOKEN_ENV else "none"


def _latest_build_run(commit_sha: str):
    token = get_github_token()
    if not token:
        return None
    r = _gh("GET", f"repos/{REPO}/actions/runs?per_page=20", token=token)
    try:
        data = r.json()
    except Exception:
        return None
    for run in data.get("workflow_runs", []):
        if run.get("head_sha") == commit_sha:
            return run
    return None


def _rollback(backup, backup_tag, reason, run_url):
    token = get_github_token()
    path = backup["path"]
    try:
        if backup["existed"]:
            cur = _get_file(path, token)
            cur_sha = cur["sha"] if cur else None
            _put_file(path, backup["old_content"], cur_sha,
                      f"auto-rollback: restaura {path}", token)
            _status("rolled_back", "reverted",
                    f"{reason}; conteúdo original restaurado automaticamente.",
                    backup_tag, run_url)
        else:
            cur = _get_file(path, token)
            if cur:
                _delete_file(path, cur["sha"], f"auto-rollback: remove {path}", token)
                _status("rolled_back", "reverted",
                        f"{reason}; arquivo novo removido.", backup_tag, run_url)
            else:
                _status("rolled_back", "reverted",
                        f"{reason}; nada a reverter.", backup_tag, run_url)
    except Exception as e:
        _status("rolled_back", "manual_needed",
                f"{reason}; falha ao reverter sozinho: {e}. Backup tag: {backup_tag}",
                backup_tag, run_url)


def _poll_and_rollback(commit_sha: str, backup: dict, backup_tag: str):
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
                _status("done", "success",
                        "build OK — mudança aplicada e publicada.", backup_tag, run_url)
                try:
                    from app.services import obsidian as _obs
                    _obs.log_session("Auto-melhoria: build OK e publicado via GitHub REST API (backup + rollback disponíveis).")
                except Exception:
                    pass
                return
            _rollback(backup, backup_tag, f"build falhou ({conclusion})", run_url)
            try:
                from app.services import obsidian as _obs
                _obs.log_session(f"Auto-melhoria: build falhou ({conclusion}); rollback automático acionado.")
            except Exception:
                pass
            return
    _status("monitoring", "timeout",
            "timeout monitorando o build (verifique em Actions).", backup_tag)


def _do_self_improve(request_text: str) -> dict:
    token = get_github_token()
    if not token:
        _status("error", "no_token", "GITHUB_TOKEN não configurado (nem no Render, nem salvo no app).")
        return {"status": "error", "message": "sem token"}

    # 1) SHA da main + tag de backup (best-effort)
    try:
        head_sha = _get_head_sha(token)
    except Exception as e:
        _status("error", "repo_unreachable", f"não consegui ler o repo: {e}")
        return {"status": "error", "message": f"repo unreachable: {e}"}

    backup_tag = f"backup-{int(time.time())}"
    _create_backup_tag(backup_tag, head_sha, token)

    # 2) LLM propõe a mudança (1 arquivo, pasta permitida) — formato robusto (sem JSON)
    system = (
        "Você é um engenheiro sênior Android (Kotlin/Jetpack Compose) e Python/FastAPI. "
        "O dono pediu uma melhoria no app NEXUS. Responda EXATAMENTE neste formato, sem nada "
        "antes ou depois (nem explicações):\n"
        "PATH: caminho/relativo/do/arquivo\n"
        "```\n"
        "conteúdo COMPLETO e correto do arquivo após a mudança\n"
        "```\n"
        "Regras: altere APENAS UM arquivo. Pastas permitidas: android/app/src/main/, backend/app/, "
        "backend/requirements.txt, backend/.env.example, render.yaml, DEPLOY.md, README.md, CHANGELOG.md. "
        "Mantenha o estilo existente; o código deve compilar; NÃO mexa em CI, segredos ou .github/. "
        "Se não conseguir fazer a mudança, responda apenas: PATH: \n```\n```"
    )
    user_msg = f"Pedido do dono: {request_text}\nRepositório: {REPO}. Proponha a mudança (1 arquivo)."
    try:
        llm_out = complete_chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": user_msg}],
            temperature=0.2,
        )
    except Exception as e:
        _status("error", "llm_error", f"erro ao chamar o LLM: {e}")
        return {"status": "error", "message": f"LLM error: {e}"}

    parsed = _parse_change(llm_out)
    if not parsed:
        _status("error", "llm_invalid", "LLM não retornou mudança válida: " + str(llm_out)[:300])
        return {"status": "error", "message": "LLM não retornou mudança válida: " + str(llm_out)[:300]}

    path, content = parsed
    if not _path_allowed(path):
        _status("error", "path_denied", f"caminho não permitido por segurança: {path}")
        return {"status": "error", "message": f"caminho não permitido por segurança: {path}"}
    if not content.strip():
        _status("error", "empty", "conteúdo vazio recusado.")
        return {"status": "error", "message": "conteúdo vazio recusado."}

    # 3) estado atual do arquivo (backup de rollback)
    existing = _get_file(path, token)
    backup = {
        "path": path,
        "existed": existing is not None,
        "old_content": existing["content"] if existing else "",
        "old_sha": existing["sha"] if existing else "",
    }

    # 4) aplica via REST API (sem git)
    try:
        commit_sha = _put_file(
            path, content, backup["old_sha"] or None,
            f"auto-improve(owner): {request_text[:80]}", token,
        )
    except Exception as e:
        _status("error", "push_failed", f"falha ao gravar no repo: {e}")
        return {"status": "error", "message": f"falha ao gravar no repo: {e}"}

    _status("pushed", "running", "mudança enviada via API do GitHub — build do APK iniciado.", backup_tag)
    threading.Thread(target=_poll_and_rollback, args=(commit_sha, backup, backup_tag),
                    daemon=True).start()
    return {
        "status": "started",
        "backup_tag": backup_tag,
        "message": "Mudança enviada. Estou monitorando o build; se falhar, revertero sozinho (backup automático). Backup: " + backup_tag,
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
    data["token_source"] = _token_source()
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
    return {"configured": bool(tok), "source": _token_source()}
