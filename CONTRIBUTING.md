# Contribuindo com o NEXUS AI

Obrigado por querer melhorar a NEXUS AI! Este é um projeto guiado por feedback: o agente
evolui o código continuamente a partir dos testes do dono. Pull requests são bem-vindos.

## Antes de começar
- Leia o [`README.md`](README.md) e o [`CHANGELOG.md`](CHANGELOG.md).
- Abra uma **issue** (bug ou feature) antes de grandes mudanças, para alinharmos o escopo.

## Setup rápido
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q

# Android (precisa de Android Studio + SDK 34, ou use o build via GitHub Actions)
```

## Padrões
- **Backend**: FastAPI + Pydantic v2. Mantenha os modelos de resposta e os contratos do app
  (veja `android/app/.../data/model/ChatModels.kt`) em sincronia. Campos opcionais usam
  `Optional[...] = None` para aceitar `null` vindo do app Android (Gson serializa nulos).
- **Android**: Kotlin + Jetpack Compose. Use `State`/`StateFlow` para UI reativa; trate erros
  de rede nos ViewModels (try/catch → `error.value`).
- **Segurança**: nunca commite `.env`, chaves de API ou `*.db`. Use sempre o `.gitignore`.

## Testes
- Backend: `pytest` em `backend/tests/` (roda no CI a cada push).
- App: o APK é construído e publicado em Release pelo workflow `build.yml`.

## Commits
Mensagens claras e em português ou inglês. Referencie a issue quando aplicável (ex.: `fix #12`).
