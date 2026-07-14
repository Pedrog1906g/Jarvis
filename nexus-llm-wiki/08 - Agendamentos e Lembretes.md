---
name: nexus-agendamentos
description: Lembretes e tarefas agendadas do NEXUS, incluindo a auto-melhoria programada para 20 dias
triggers:
  - "agendamentos do nexus"
  - "tarefa para daqui 20 dias"
  - "lembrete agendado"
version: 1.1.0
tags: [nexus, agendamentos, lembretes, cron]
---

# Agendamentos e Lembretes

## Lembretes (visíveis no app)
- `GET/POST /api/reminders` com `{"title","note","due_at":"ISO"}`.
- O `reminder_scheduler` marca como `notified` quando vence.

## Tarefas agendadas (executam sozinhas)
Modelo `ScheduledTask` + `start_scheduled_tasks()` (thread no backend, a cada 60s).
Ações: `self_improve` (dispara [[Auto-Melhoria]]) e `remind` (cria lembrete).

Endpoints (só dono): `GET/POST /api/scheduled_tasks`.

## Exemplo plantado (2026-07-14)
- **Auto-melhoria em 20 dias** (2026-08-03): tarefa `self_improve` que roda o NEXUS se
  melhorando e publica novo APK sozinho.
- **Lembrete 20 dias** (2026-08-03): "Revisar e auto-melhorar o NEXUS AI".
- **Aviso de renovação** (2026-10-02, ~80 dias): Postgres free do Render expire em
  ~10 dias — migrar para [[Super Base (Supabase)]] ou fazer backup.

## Como criar uma nova
```bash
curl -X POST https://nexus-api-2o1y.onrender.com/api/scheduled_tasks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"action":"self_improve","run_at":"2026-09-01T12:00:00+00:00",
       "payload":{"request":"melhore a documentacao"},"note":"melhoria mensal"}'
```

Veja também: [[Auto-Melhoria]], [[Backend FastAPI]], [[Super Base (Supabase)]].
