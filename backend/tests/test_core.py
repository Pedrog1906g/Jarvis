"""Testes unitários puros do NEXUS AI.

Não precisam de banco, rede ou API key — rodam em qualquer lugar (CI incluso).
Cobrem lógica crítica que não deve quebrar:
  - identidade JARVIS (persona)
  - segurança do auto-melhoria (caminhos permitidos/negados)
  - gatilhos de auto-melhoria
  - hash de senha e roundtrip de token JWT
"""
import hashlib

from app.core import personality
from app.core.security import create_token, decode_token, hash_passphrase
from app.api import agent


def test_jarvis_persona_present():
    assert personality.JARVIS_SYSTEM_PROMPT
    assert "JARVIS" in personality.JARVIS_SYSTEM_PROMPT
    # alias antigo mantido para não quebrar imports
    assert personality.NEXUS_SYSTEM_PROMPT == personality.JARVIS_SYSTEM_PROMPT


def test_path_allowed_accepts_app_code():
    assert agent._path_allowed("android/app/src/main/java/com/nexusai/app/MainActivity.kt")
    assert agent._path_allowed("web/index.html")
    assert agent._path_allowed("backend/app/core/llm.py")
    assert agent._path_allowed("README.md")


def test_path_allowed_rejects_ci_and_traversal():
    assert not agent._path_allowed(".github/workflows/build.yml")
    assert not agent._path_allowed("../secrets.py")
    assert not agent._path_allowed("backend/../../etc/passwd")
    assert not agent._path_allowed("/etc/passwd")


def test_self_improve_triggers():
    assert agent.detect_self_improve("melhore o app")
    assert agent.detect_self_improve("mude o código")
    assert not agent.detect_self_improve("qual é o seu nome?")


def test_hash_passphrase_is_strong_and_deterministic():
    h = hash_passphrase("nexus")
    assert h == hashlib.sha256(b"nexus").hexdigest()
    assert h != "nexus"
    assert hash_passphrase("nexus") == h  # determinístico


def test_jwt_token_roundtrip():
    tok = create_token(1, "owner")
    payload = decode_token(tok)
    assert payload["sub"] == "1"
    assert payload["username"] == "owner"


def test_supabase_sync_is_noop_when_unconfigured():
    from app.services import supabase_sync
    # Sem as env vars do Supabase, deve ser no-op e nunca lançar erro.
    assert supabase_sync.sc.is_configured() is False
    assert supabase_sync.sync_message("owner", 1, "user", "oi") is False
    assert supabase_sync.sync_memory("owner", "gosta de pizza") is False
    assert supabase_sync.sync_setting("k", "v") is False
