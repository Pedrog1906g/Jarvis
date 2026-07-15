"""Sincronização best-effort com o Supabase (cross-device: celular <-> PC).

Todas as funções são seguras: retornam False se o Supabase não estiver
configurado ou em caso de erro. NÃO quebram o fluxo principal do backend.

Para ativar: defina SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY no Render
(ver supabase/README.md). Até lá, é no-op.
"""
from app.core import supabase_client as sc


def sync_message(owner_username: str, conversation_id, role: str, content: str) -> bool:
    if not sc.is_configured():
        return False
    try:
        return sc.upsert("sync_messages", {
            "owner_username": owner_username,
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content,
        })
    except Exception:
        return False


def sync_memory(owner_username: str, fact: str, category: str = "geral",
                importance: int = 1) -> bool:
    if not sc.is_configured():
        return False
    try:
        return sc.upsert("memory_facts", {
            "owner_username": owner_username,
            "fact": fact,
            "category": category,
            "importance": importance,
        })
    except Exception:
        return False


def sync_setting(key: str, value: str) -> bool:
    if not sc.is_configured():
        return False
    try:
        return sc.upsert("settings", {"key": key, "value": value})
    except Exception:
        return False
