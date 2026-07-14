"""Agendador simples de lembretes (thread em background).
Verifica lembretes vencidos e os marca como notificados.
Em produção, integra com push/FCM ou notificação no app."""
import threading
import time
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.db import models


def _loop(interval: int = 30):
    while True:
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)
            due = db.query(models.Reminder).filter(
                models.Reminder.done == False,
                models.Reminder.notified == False,
                models.Reminder.due_at <= now).all()
            for r in due:
                r.notified = True
                print(f"[NEXUS] Lembrete vencido: {r.title}")
            if due:
                db.commit()
            db.close()
        except Exception as e:
            print("[NEXUS] erro no scheduler:", e)
        time.sleep(interval)


def start_scheduler():
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
