"""Integração com Firebase Admin SDK (opcional, via variáveis de ambiente).

Se FIREBASE_PROJECT_ID / FIREBASE_CLIENT_EMAIL / FIREBASE_PRIVATE_KEY estiverem
definidos (no Render), o backend:
  - inicializa o Firebase Admin SDK;
  - pode validar ID tokens do Firebase Auth (`verify_id_token`);
  - espelha (best-effort) usuários, histórico, memória e lembretes no Firestore.

Sem essas variáveis o backend roda normalmente no modo JWT/SQLite (dev e Render).
Nenhuma chave do Firebase é escrita no APK — tudo fica nas Environment Variables do Render.
"""
import logging
import threading

from app.config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_PRIVATE_KEY,
)

logger = logging.getLogger("nexus.firebase")

_app = None
_enabled = False
_lock = threading.Lock()


def _service_account() -> dict | None:
    if not (FIREBASE_PROJECT_ID and FIREBASE_CLIENT_EMAIL and FIREBASE_PRIVATE_KEY):
        return None
    # Variáveis de ambiente não preservam quebras de linha: o JSON da chave privada
    # costuma vir como "\\n". Convertemos de volta para "\n".
    private_key = FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
    return {
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "client_email": FIREBASE_CLIENT_EMAIL,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def init_firebase() -> None:
    global _app, _enabled
    cert = _service_account()
    if cert is None:
        logger.info("Firebase não configurado: modo JWT/SQLite padrão.")
        return
    try:
        import firebase_admin
        from firebase_admin import credentials

        _app = firebase_admin.initialize_app(credentials.Certificate(cert))
        _enabled = True
        logger.info("Firebase Admin inicializado (project=%s).", FIREBASE_PROJECT_ID)
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao inicializar Firebase: %s", e)


def is_enabled() -> bool:
    return _enabled


def verify_id_token(id_token: str) -> dict:
    import firebase_admin
    from firebase_admin import auth as fb_auth

    return fb_auth.verify_id_token(id_token, app=_app)


def firestore():
    from firebase_admin import firestore

    return firestore.client(app=_app)


def mirror(payload: dict, collection: str, doc_id: str) -> None:
    """Espelha (best-effort) um documento no Firestore. Nunca quebra o fluxo principal."""
    if not _enabled:
        return
    try:
        db = firestore()
        db.collection(collection).document(str(doc_id)).set(payload, merge=True)
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao espelhar no Firestore (%s/%s): %s", collection, doc_id, e)


# --- Espelhamentos de domínio (usados pelos endpoints quando o Firebase está ativo) ---

def mirror_user(user) -> None:
    mirror(
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "updated_at": _now(),
        },
        "users",
        user.id,
    )


def mirror_message(conversation_id: int, message) -> None:
    mirror(
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "updated_at": _now(),
        },
        f"conversations/{conversation_id}/messages",
        message.id,
    )


def mirror_memory(owner_id: int, facts: list) -> None:
    mirror({"owner_id": owner_id, "facts": facts, "updated_at": _now()}, "memory", owner_id)


def mirror_reminder(owner_id: int, reminder) -> None:
    mirror(
        {
            "id": reminder.id,
            "title": reminder.title,
            "note": reminder.note,
            "due_at": reminder.due_at.isoformat() if hasattr(reminder.due_at, "isoformat") else str(reminder.due_at),
            "done": reminder.done,
            "updated_at": _now(),
        },
        f"users/{owner_id}/reminders",
        reminder.id,
    )


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
