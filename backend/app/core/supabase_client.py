"""Cliente Supabase configurável (PRONTO, sem segredos fixos).

Lê as env vars:
  SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
Se não estiverem definidas, `is_configured()` retorna False e todas as funções
são no-op (None/False), então o app funciona normalmente sem o Supabase.

O pacote `supabase` é importado de forma preguiçosa (lazy): NÃO é obrigatório
instalá-lo para o backend rodar. Para ativar, `pip install supabase` e defina
as env vars acima no Render.
"""
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def is_configured() -> bool:
    return bool(SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY))


_client = None


def get_client():
    """Retorna um client do Supabase (service role) ou None se não configurado."""
    global _client
    if not is_configured():
        return None
    if _client is None:
        try:
            from supabase import create_client  # lazy import
        except Exception:
            return None
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


def upsert(table: str, row: dict) -> bool:
    c = get_client()
    if c is None:
        return False
    try:
        c.table(table).upsert(row).execute()
        return True
    except Exception:
        return False


def select(table: str, **filters) -> list:
    c = get_client()
    if c is None:
        return []
    try:
        q = c.table(table).select("*")
        for k, v in filters.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception:
        return []


def upload(bucket: str, path: str, data: bytes) -> bool:
    c = get_client()
    if c is None:
        return False
    try:
        c.storage.from_(bucket).upload(path, data, {"upsert": "true"})
        return True
    except Exception:
        return False
