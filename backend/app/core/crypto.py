"""Criptografia leve para segredos do NEXUS (token do GitHub, etc.).

A chave é derivada do JWT_SECRET (variável de ambiente do servidor) — ela NÃO é
armazenada no banco, então um dump do banco sozinho não revela os segredos.
"""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.config import JWT_SECRET


def _key() -> bytes:
    seed = (JWT_SECRET or "nexus-dev-secret-change-me").encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(seed).digest())


def encrypt(plain: str) -> str:
    if not plain:
        return ""
    return Fernet(_key()).encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return Fernet(_key()).decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""
