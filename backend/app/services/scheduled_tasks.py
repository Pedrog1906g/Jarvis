"""Agendador de tarefas do NEXUS (thread em background).

Executa, sozinho, tarefas futuras salvas no banco (tabela scheduled_tasks):
  - "self_improve": dispara a auto-melhoria (o app se melhora e publica novo APK).
  - "remind": cria um lembrete imediato para o dono.

Usado para "engatilhar" coisas como a auto-melhoria de 20 em 20 dias ou o aviso
de renovação do banco antes do Postgres free expirar.
"""
import json
import threading
import time
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db import models
from app.api import agent as _agent


def _run_due():
    while True:
        try:
            now = datetime.now(timezone.utc)
            db = SessionLocal()
            try:
                due = (
                    db.query(models.ScheduledTask)
                    .filter(models.ScheduledTask.done == False,
                            models.ScheduledTask.run_at <= now)
                    .all()
                )
                for t in due:
                    try:
                        if t.action == "self_improve":
                            req = (json.loads(t.payload or "{}") or {}).get(
                                "request", "melhore a estabilidade e a documentacao do NEXUS AI"
                            )
                            _agent.trigger_self_improve(req)
                        elif t.action == "remind":
                            p = json.loads(t.payload or "{}") or {}
                            r = models.Reminder(
                                owner_id=t.owner_id,
                                title=p.get("title", t.note or "Lembrete agendado"),
                                note=p.get("note", ""),
                                due_at=now,
                            )
                            db.add(r)
                        t.done = True
                        db.commit()
                        print(f"[NEXUS] tarefa agendada executada: {t.action} (id={t.id})")
                    except Exception as e:
                        print("[NEXUS] erro ao executar tarefa agendada:", e)
            finally:
                db.close()
        except Exception as e:
            print("[NEXUS] erro no scheduler de tarefas:", e)
        time.sleep(60)


def start_scheduled_tasks():
    threading.Thread(target=_run_due, daemon=True).start()
