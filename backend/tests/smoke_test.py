"""Smoke test simples do backend (modo demo, sem chave de API).
Execute:  python tests/smoke_test.py   (servidor em http://localhost:8000)
Ou:       NEXUS_BASE=http://127.0.0.1:8001 python tests/smoke_test.py
"""
import httpx
import os
import sys

BASE = os.getenv("NEXUS_BASE", "http://localhost:8000")


def main():
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.get("/")
        print("GET / ->", r.status_code, r.json())

        r = c.post("/api/auth/login", json={"username": "owner", "passphrase": "nexus"})
        print("login ->", r.status_code)
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        r = c.post("/api/chat", json={"content": "Olá Nexus, qual seu nome?"},
                   headers=h)
        print("chat ->", r.status_code, r.json())

        r = c.get("/api/system/info", headers=h)
        print("system/info ->", r.status_code, "version:", r.json().get("version"))

        r = c.post("/api/reminders", json={"title": "Teste", "due_at": "2030-01-01T09:00:00"},
                   headers=h)
        print("reminder ->", r.status_code, r.json())

        print("\nSMOKE TEST OK" if r.status_code == 200 else "\nSMOKE TEST FALHOU")


if __name__ == "__main__":
    main()
