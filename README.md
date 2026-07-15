# JARVIS (NEXUS AI)

Assistente pessoal inspirado no JARVIS do Homem de Ferro. O **JARVIS** é a
personalidade (voz masculina, calma, elegante); o **NEXUS** é o sistema/backend.

Funciona integrado entre **Android**, **Navegador Web (PC)**, **Windows**,
**GitHub**, **Render** e **Supabase/Obsidian** (cross-device). Smart TV/Linux são
módulos planejados.

## O que funciona hoje
- 🤖 **Conversa por voz e texto** (PT-BR), respostas concisas (1–4 frases).
- 🎙️ **Wake word "Jarvis"** no celular e no PC (escuta contínua).
- 📱 **Android**: abrir apps, tocar música, lembretes, ler tela/notificações.
- 🖥️ **HUD Iron Man no PC** (reconhecimento contínuo + TTS do navegador).
- 🔄 **Auto-atualização** do app (APK assinado via CI do GitHub).
- 🛠️ **Auto-melhoria**: o JARVIS edita o próprio código, com backup e rollback
  automático (nunca mexe em CI/segredos).
- 🧠 **Memória** (curto + longo prazo) e **Obsidian** (vault local ou GitHub).
- 🔐 **Segurança**: JWT, hash de senha, RLS no Supabase, sem segredos fixos.

## Como usar

### PC (navegador)
1. Abra `https://nexus-api-2o1y.onrender.com/` (link **https**).
2. Login: usuário `owner`, acesso `nexus`.
3. Clique no 🎙️ e diga **"Jarvis, ..."** (ex.: "Jarvis, toque música").
4. ⚙️ = peça uma melhoria (ele muda o código e se atualiza).

### Celular (Android)
1. Instale o **nexus-ai-94** (https://github.com/Pedrog1906g/Jarvis/releases/latest).
   Na 1ª vez, **desinstale** o app antigo antes (assinatura diferente).
2. Permita o microfone e ligue a wake word em **Ajustes**.
3. Diga **"Jarvis"** → "Às ordens." → seu comando.

Veja o guia completo em `JARVIS_PRONTO.md` (e no chat do seu agente).

## Arquitetura
Veja [`ARCHITECTURE.md`](ARCHITECTURE.md) (diagrama Mermaid: Android/Web/Windows →
Backend FastAPI → LLM/Supabase/Obsidian/GitHub → Render/GitHub CI).

## Estrutura do repo
```
android/        App Android (Kotlin + Jetpack Compose)
backend/        Backend FastAPI (IA, memória, auto-melhoria, Obsidian)
web/            HUD Iron Man para PC (index.html)
supabase/       Schema SQL + cliente pronto (sem tokens fixos)
nexus-llm-wiki/ Vault de conhecimento (Obsidian via GitHub)
.github/        CI: build do APK + testes
```

## Desenvolvimento
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app`
- Testes: `cd backend && pytest` (sem banco/rede/API key necessários).
- App Android: abra `android/` no Android Studio; o CI gera o APK.

## Deploy
- **Render**: auto-deploy ao fazer push em `main` (hospeda o backend).
- **GitHub**: `build.yml` gera o APK (release `nexus-ai-N`); `test-backend.yml`
  roda os testes.

## Licença
MIT.
