"""Testes estendidos do NEXUS AI.

Cobre endpoints e módulos sem cobertura na suite original:
- Voz (transcribe / synthesize)
- Métricas (/api/metrics/system, /api/metrics/ping)
- Status do agente (/api/agent/self_improve/status)
- GitHub token status
- Obsidian (/api/obsidian/context)
- Tarefas agendadas (/api/scheduled_tasks)
- Lembretes: listagem e vencidos
- Memória: extração de fatos (modo DEMO, sem LLM)
- Voice core: transcribe em DEMO, synthesize com provider 'android'
- system.py: update_available é booleano real
- Spotify: status retorna campos corretos, intent_classified
- system_control: classificação de intents
"""
import io
import pytest


def _login(client):
    r = client.post("/api/auth/login", json={"username": "owner", "passphrase": "nexus"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── Métricas ────────────────────────────────────────────────────────────────

def test_metrics_ping_no_auth(client):
    """ping não precisa de auth — qualquer um pode medir latência."""
    r = client.get("/api/metrics/ping")
    assert r.status_code == 200
    d = r.json()
    assert "ts" in d
    assert d["status"] == "ok"


def test_metrics_system_requires_auth(client):
    r = client.get("/api/metrics/system")
    assert r.status_code == 401


def test_metrics_system_returns_expected_fields(client):
    h = _login(client)
    r = client.get("/api/metrics/system", headers=h)
    assert r.status_code == 200
    d = r.json()
    for key in ("cpu_percent", "memory_percent", "disk_percent",
                "nexus_version", "llm_available", "demo_mode", "timestamp", "real"):
        assert key in d, f"Campo ausente: {key}"
    assert isinstance(d["cpu_percent"], (int, float))
    assert isinstance(d["memory_percent"], (int, float))
    assert isinstance(d["real"], bool)


# ─── Sistema / update_available ───────────────────────────────────────────────

def test_system_info_update_available_is_bool(client):
    h = _login(client)
    r = client.get("/api/system/info", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["update_available"], bool), (
        "update_available deve ser bool, não hardcoded False"
    )


def test_health_no_auth(client):
    r = client.get("/api/system/health")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


# ─── Voz ─────────────────────────────────────────────────────────────────────

def test_voice_transcribe_returns_demo_text_without_api_key(client):
    h = _login(client)
    fake_audio = b"\x00" * 100  # bytes vazios — modo DEMO retorna string fixa
    r = client.post(
        "/api/voice/transcribe",
        files={"file": ("audio.webm", io.BytesIO(fake_audio), "audio/webm")},
        headers=h,
    )
    assert r.status_code == 200
    d = r.json()
    assert "text" in d
    assert isinstance(d["text"], str)
    # Em modo DEMO, deve retornar a string de placeholder (não vazia, não erro)
    assert len(d["text"]) > 0


def test_voice_synthesize_android_provider_returns_204(client):
    """Com TTS_PROVIDER='android' (padrão), o backend retorna 204 (sem corpo).
    O app Android usa o TTS nativo — nenhum áudio é gerado no servidor."""
    h = _login(client)
    r = client.post("/api/voice/synthesize", json={"text": "Olá, sou o JARVIS."}, headers=h)
    # 204 = sem conteúdo (provider android) OU 200 com bytes (provider openai)
    assert r.status_code in (200, 204)


# ─── Agente / Auto-melhoria ───────────────────────────────────────────────────

def test_agent_status_is_accessible(client):
    h = _login(client)
    r = client.get("/api/agent/self_improve/status", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert "token_configured" in d
    assert isinstance(d["token_configured"], bool)


def test_agent_github_token_status(client):
    h = _login(client)
    r = client.get("/api/agent/github_token_status", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert "configured" in d
    assert "source" in d
    assert d["source"] in ("db", "env", "none")


def test_agent_self_improve_fails_without_token(client):
    """Sem GITHUB_TOKEN, a resposta deve ser error (não 500)."""
    h = _login(client)
    r = client.post("/api/agent/self_improve", json={"request": "teste"}, headers=h)
    assert r.status_code == 200
    d = r.json()
    assert d["status"] in ("error", "started")  # error sem token, started com token


# ─── Obsidian ────────────────────────────────────────────────────────────────

def test_obsidian_context_accessible(client):
    """Deve retornar 200 (context pode ser string vazia se GitHub não configurado)."""
    h = _login(client)
    r = client.get("/api/obsidian/context", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert "context" in d
    assert isinstance(d["context"], str)


# ─── Tarefas agendadas ────────────────────────────────────────────────────────

def test_scheduled_tasks_list_empty(client):
    h = _login(client)
    r = client.get("/api/scheduled_tasks", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_scheduled_tasks_create_and_list(client):
    h = _login(client)
    r = client.post(
        "/api/scheduled_tasks",
        json={"action": "remind", "run_at": "2035-01-01T09:00:00", "note": "Teste agendado"},
        headers=h,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["task"]["action"] == "remind"

    r2 = client.get("/api/scheduled_tasks", headers=h)
    assert any(t["action"] == "remind" for t in r2.json())


def test_scheduled_tasks_invalid_action(client):
    h = _login(client)
    r = client.post(
        "/api/scheduled_tasks",
        json={"action": "invalid_action", "run_at": "2035-01-01T09:00:00"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "error"


# ─── Lembretes ────────────────────────────────────────────────────────────────

def test_reminders_list(client):
    h = _login(client)
    r = client.get("/api/reminders", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_reminders_due_endpoint(client):
    h = _login(client)
    r = client.get("/api/reminders/due", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ─── Plugins ─────────────────────────────────────────────────────────────────

def test_spotify_status_has_required_fields(client):
    h = _login(client)
    r = client.get("/api/plugins/spotify/status", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert "name" in d
    assert "enabled" in d
    assert "authenticated" in d
    assert "oauth_configured" in d
    assert "note" in d
    assert d["name"] == "spotify"
    assert isinstance(d["authenticated"], bool)
    assert isinstance(d["oauth_configured"], bool)


def test_spotify_command_intent_classified(client):
    h = _login(client)
    for cmd, expected_action in [
        ("tocar rock", "play"),
        ("pausar", "pause"),
        ("próxima música", "next"),
        ("playlist de trabalho", "playlist"),
    ]:
        r = client.post("/api/plugins/spotify/command", json={"command": cmd}, headers=h)
        assert r.status_code == 200
        d = r.json()
        assert d["action"] == expected_action, f"Comando '{cmd}': esperava '{expected_action}', obteve '{d['action']}'"
        assert d["status"] == "intent_classified"


def test_system_control_intents(client):
    h = _login(client)
    cases = [
        ("abrir whatsapp", "open_app"),
        ("volume máximo", "volume"),
        ("câmera", "camera"),
    ]
    for cmd, expected_intent in cases:
        r = client.post("/api/plugins/system/command", json={"command": cmd}, headers=h)
        assert r.status_code == 200
        assert r.json()["intent"] == expected_intent, f"Comando '{cmd}': esperava '{expected_intent}'"


def test_system_control_dangerous_requires_confirmation(client):
    h = _login(client)
    r = client.post("/api/plugins/system/command", json={"command": "apagar tudo"}, headers=h)
    assert r.status_code == 200
    d = r.json()
    assert d["dangerous"] is True
    assert d["requires_confirmation"] is True


# ─── Módulos core (unitários) ──────────────────────────────────────────────────

def test_voice_transcribe_demo_mode():
    """Transcribe em DEMO retorna placeholder não-vazio (sem chamar Groq)."""
    from app.core.voice import transcribe_audio
    result = transcribe_audio(b"\x00" * 64)
    assert isinstance(result, str)
    assert len(result) > 0


def test_voice_synthesize_android_returns_none():
    """synthesize_speech com TTS_PROVIDER='android' deve retornar None."""
    import os
    os.environ["TTS_PROVIDER"] = "android"
    # Force reload to pick up env change
    import importlib
    import app.core.voice as voice_mod
    importlib.reload(voice_mod)
    result = voice_mod.synthesize_speech("Olá JARVIS")
    assert result is None


def test_memory_get_long_term_empty():
    """get_long_term com banco vazio retorna lista vazia, sem erro."""
    from app.core.memory import get_long_term
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        facts = get_long_term(db, owner_id=9999, query="qualquer coisa")
        assert isinstance(facts, list)
    finally:
        db.close()


def test_supabase_upsert_noop_when_unconfigured():
    """upsert retorna False graciosamente sem Supabase configurado."""
    from app.core.supabase_client import upsert, is_configured
    assert not is_configured()
    result = upsert("qualquer_tabela", {"chave": "valor"})
    assert result is False


def test_agent_parse_change_json_format():
    """_parse_change aceita formato JSON e retorna (path, content)."""
    from app.api.agent import _parse_change
    import json
    payload = json.dumps({"path": "backend/app/core/llm.py", "content": "# conteudo"})
    result = _parse_change(payload)
    assert result is not None
    path, content = result
    assert path == "backend/app/core/llm.py"
    assert content == "# conteudo"


def test_agent_parse_change_path_format():
    """_parse_change aceita formato PATH: + bloco de código."""
    from app.api.agent import _parse_change
    payload = "PATH: web/index.html\n```\n<html>oi</html>\n```"
    result = _parse_change(payload)
    assert result is not None
    path, content = result
    assert path == "web/index.html"
    assert "<html>" in content


def test_agent_path_denied_workflows():
    """Arquivos de CI nunca podem ser modificados pelo agente."""
    from app.api.agent import _path_allowed
    assert not _path_allowed(".github/workflows/build.yml")
    assert not _path_allowed(".github/workflows/test-backend.yml")
    assert not _path_allowed("backend/../.github/workflows/evil.yml")
