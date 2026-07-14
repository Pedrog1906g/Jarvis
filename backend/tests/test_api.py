"""Testes de contrato da API NEXUS AI (modo DEMO, sem chave de API).

Valida os endpoints usados pelo app Android, inclusive com `null` explícito
(como o Gson do app envia), que era uma fonte de erro 422.
"""
import pytest


def _login(client):
    r = client.post("/api/auth/login", json={"username": "owner", "passphrase": "nexus"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "NEXUS AI"
    assert body["status"] == "online"


def test_login_returns_token(client):
    r = client.post("/api/auth/login", json={"username": "owner", "passphrase": "nexus"})
    assert r.status_code == 200
    data = r.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "owner"


def test_login_wrong_passphrase_rejected(client):
    r = client.post("/api/auth/login", json={"username": "owner", "passphrase": "errada"})
    assert r.status_code == 401


def test_unauthenticated_request_rejected(client):
    r = client.get("/api/system/info")
    assert r.status_code == 401


def test_chat_accepts_explicit_null_conversation_id(client):
    h = _login(client)
    r = client.post(
        "/api/chat",
        json={"content": "Olá Nexus, qual seu nome?", "conversation_id": None},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert "conversation_id" in body
    assert "reply" in body


def test_system_info(client):
    h = _login(client)
    r = client.get("/api/system/info", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["app"] == "NEXUS AI"
    assert "version" in body
    assert "changelog" in body


def test_conversations_and_messages(client):
    h = _login(client)
    r = client.post(
        "/api/chat", json={"content": "Lembra que gosto de pizza", "conversation_id": None}, headers=h
    )
    cid = r.json()["conversation_id"]
    r = client.get("/api/conversations", headers=h)
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())
    r = client.get(f"/api/conversations/{cid}/messages", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_reminders_crud_with_null_note(client):
    h = _login(client)
    r = client.post(
        "/api/reminders",
        json={"title": "Pagar contas", "note": None, "due_at": "2030-03-03T09:00:00"},
        headers=h,
    )
    assert r.status_code == 200
    rid = r.json()["id"]
    r = client.post(f"/api/reminders/{rid}/done", headers=h)
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_plugins_and_commands(client):
    h = _login(client)
    r = client.get("/api/plugins", headers=h)
    assert r.status_code == 200
    r = client.post("/api/plugins/system/command", json={"command": "abrir maps"}, headers=h)
    assert r.status_code == 200
    assert r.json()["intent"] == "open_app"
    r = client.post("/api/plugins/spotify/command", json={"command": "tocar música"}, headers=h)
    assert r.status_code == 200
    assert r.json()["action"] == "play"
