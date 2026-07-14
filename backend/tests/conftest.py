"""Configuração de testes: banco isolado em SQLite + modo DEMO (sem Groq)."""
import os
import tempfile
import pytest

# Define o ambiente ANTES de importar o app (o config lê as envs na importação).
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["GROQ_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret-change-me"
os.environ["OWNER_PASSPHRASE"] = "nexus"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
