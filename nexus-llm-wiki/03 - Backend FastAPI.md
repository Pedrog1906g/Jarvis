---
name: nexus-backend
description: Backend FastAPI do NEXUS — endpoints, autenticação, chat, auto-melhoria e agendamentos
triggers:
  - "backend do nexus"
  - "endpoints da api"
  - "como funciona a api"
version: 1.1.0
tags: [nexus, backend, fastapi, api]
---

# Backend FastAPI (NEXUS AI)

Hospedado no **Render** em `https://nexus-api-2o1y.onrender.com`. Python 3.14.

## Autenticação
- `POST /api/auth/login` → `{"username":"owner","passphrase":"nexus"}` retorna `access_token` (JWT, 30 dias).
- `GET /api/system/health` → público (`{"status":"online"}`).
- Rotas protegidas usam `Authorization: Bearer <token>`.

## Chat
- `WS /api/ws/chat?token=...` → envie `{type:message, content, conversation_id}`;
  receba `{type:start}`, `{type:delta, content}`, `{type:done, conversation_id}`.
- `POST /api/chat` (não-streaming) e `GET /api/conversations`.

## Auto-melhoria (owner-only)
- `POST /api/agent/self_improve` → `{"request":"..."}`.
- `GET /api/agent/self_improve/status` → estado (idle/running/success/rolled_back/error).
- `POST /api/agent/set_github_token` → salva token GitHub **criptografado no banco**.
- `GET /api/agent/github_token_status` → de onde vem o token (`db` ou `env`).
- Detalhes em [[Auto-Melhoria]].

## Agendamentos & Lembretes
- `GET/POST /api/reminders` → lembretes do dono.
- `GET/POST /api/scheduled_tasks` → tarefas futuras (só dono). Ver [[Agendamentos e Lembretes]].

## Modelos (SQLAlchemy)
`User`, `Conversation`, `Message`, `MemoryFact`, `Reminder`, `PluginState`,
`Setting` (chave-valor, ex.: token GitHub criptografado), `ScheduledTask`.

## Configuração (env vars no Render)
`GROQ_API_KEY`, `JWT_SECRET`, `OWNER_PASSPHRASE`, `DATABASE_URL`, `GITHUB_TOKEN`,
`GITHUB_REPO`, `FIREBASE_*` (opcional). Banco criado via `Base.metadata.create_all`.

Veja também: [[Arquitetura]], [[Segurança]], [[Auto-Melhoria]].
