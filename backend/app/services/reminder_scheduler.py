"""Agendador de lembretes (thread em background).

Verifica lembretes vencidos a cada 30 segundos e:
  1. Marca o lembrete como notificado no banco.
  2. Entrega a notificação ao usuário via WebSocket (se conectado).
  3. Espelha no Firebase/FCM (se configurado) para push no Android.
"""
import logging
import threading
import time
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db import models

logger = logging.getLogger("nexus.reminders")


def _deliver_reminder(r: models.Reminder):
    """Envia o lembrete para todos os canais de notificação disponíveis."""
    payload = {
        "type": "reminder",
        "id": r.id,
        "title": r.title,
        "note": r.note or "",
        "due_at": r.due_at.isoformat(),
    }

    # ── 1. WebSocket (HUD web / app) ────────────────────────────────────────
    try:
        from app.core.ws_manager import manager
        delivered = manager.push_sync(r.owner_id, payload)
        if delivered:
            logger.info("Lembrete '%s' entregue via WebSocket (user %d)", r.title, r.owner_id)
    except Exception as e:
        logger.warning("Falha WS lembrete: %s", e)

    # ── 2. Firebase FCM (push Android — best-effort) ─────────────────────────
    try:
        from app.core.firebase import mirror_reminder, is_enabled
        if is_enabled():
            mirror_reminder(r.owner_id, r)
    except Exception:
        pass

    logger.info("🔔 Lembrete vencido: '%s' (user_id=%d)", r.title, r.owner_id)


def _loop(interval: int = 30):
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc)
                due = db.query(models.Reminder).filter(
                    models.Reminder.done == False,
                    models.Reminder.notified == False,
                    models.Reminder.due_at <= now,
                ).all()
                for r in due:
                    _deliver_reminder(r)
                    r.notified = True
                if due:
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error("Erro no scheduler de lembretes: %s", e)
        time.sleep(interval)


def start_scheduler():
    threading.Thread(target=_loop, daemon=True).start()
