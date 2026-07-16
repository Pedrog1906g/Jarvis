# NEXUS AI (JARVIS)

Assistente pessoal inspirado no JARVIS do Homem de Ferro. Backend FastAPI (Python) + HUD web + app Android (Kotlin/Jetpack Compose).

## Como rodar no Replit

**Workflow:** `Backend NEXUS AI`
- Comando: `cd backend && pip install -r requirements.txt -q && uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload`
- Porta: `5000`
- O preview abre o HUD web em `/` — faça login com usuário `owner` e senha `nexus` (padrão).

## Variáveis de ambiente necessárias

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GROQ_API_KEY` | Recomendada | LLM via Groq (Llama 3.3). Sem ela: modo DEMO. |
| `JWT_SECRET` | ✅ Sim | Segredo para JWT — já configurado como secret no Replit. |
| `OWNER_PASSPHRASE` | Opcional | Senha do dono (padrão: `nexus`) |
| `DATABASE_URL` | Opcional | SQLite por padrão. PostgreSQL para produção. |
| `OPENAI_API_KEY` | Opcional | LLM alternativo. |
| `ANTHROPIC_API_KEY` | Opcional | LLM alternativo (Claude). |
| `GOOGLE_API_KEY` | Opcional | LLM alternativo (Gemini). |
| `OPENAI_TTS_API_KEY` | Opcional | TTS real na web (define `TTS_PROVIDER=openai`). |
| `GITHUB_TOKEN` | Opcional | Auto-melhoria via GitHub REST API. |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | Opcional | Sincronização cross-device. |
| `FIREBASE_PROJECT_ID/CLIENT_EMAIL/PRIVATE_KEY` | Opcional | Espelhamento Firestore. |

## Estrutura

```
backend/          FastAPI — LLM, memória, voz, agente, Supabase, Firebase
  app/
    api/          Endpoints REST + WebSocket
    core/         LLM, memória, voz, segurança, personalidade
    db/           Modelos SQLAlchemy (SQLite/PostgreSQL)
    plugins/      Spotify (intent routing), controle de sistema
    services/     Obsidian, learning loop, reminder scheduler
  tests/          43 testes (pytest) — rodam sem chave de API
web/              HUD Iron Man (HTML/JS/CSS puro) — métricas reais via /api/metrics
android/          App Android (Kotlin + Jetpack Compose)
nexus-llm-wiki/   Vault de conhecimento (Obsidian via GitHub)
supabase/         Schema SQL para sincronização cross-device
```

## Rodar testes

```bash
cd backend && python -m pytest tests/ -v
```

43 testes cobrem: auth, chat, memória, voz, métricas, agente, Obsidian, tarefas agendadas, lembretes, plugins Spotify e controle de sistema.

## Funcionalidades

| Funcionalidade | Estado |
|---|---|
| Chat (WebSocket + REST) | ✅ Real |
| Memória curto/longo prazo | ✅ Real |
| Compressão de histórico | ✅ Real |
| STT via Groq Whisper | ✅ Real (requer GROQ_API_KEY) |
| TTS (android provider) | ✅ Real (app Android usa TTS nativo) |
| TTS (openai provider) | ✅ Real (requer OPENAI_TTS_API_KEY) |
| Auto-melhoria via GitHub | ✅ Real (requer GITHUB_TOKEN) |
| Rollback automático | ✅ Real |
| Lembretes + scheduler | ✅ Real |
| Learning loop (7 dias) | ✅ Real |
| Obsidian sync (GitHub) | ✅ Real (requer GITHUB_TOKEN) |
| Métricas do sistema (HUD) | ✅ Real (psutil) |
| Supabase sync | ✅ Real (requer credenciais) |
| Firebase sync | ✅ Real (requer credenciais) |
| mDNS auto-discovery | ✅ Real |
| Spotify (execução) | ⚠️ Intent routing — execução no Android app |
| TTS Piper (offline) | ⚠️ Integração pendente |

## Preferências do usuário

- Linguagem: Português (BR)
- Projeto usa FastAPI + SQLAlchemy + SQLite (sem migração para Replit DB)
- Não reestruturar o projeto; manter stack existente
- Métricas sempre reais (psutil instalado)
- Todos os testes devem rodar sem chave de API (modo DEMO)
