# CHANGELOG — NEXUS AI

## v1.1.0 (auto-melhoria real + Super Base + Obsidian)
- **Auto-melhoria funciona de verdade no Render**: `agent.py` reescrito para usar 100% a
  **GitHub REST API** (`GET`/`PUT`/`DELETE` em `/repos/{repo}/contents`), sem `git` nenhum.
  O Render negava `git push` com 403, mas a REST API com token Bearer funciona. Backup
  automático (tag + conteúdo original do arquivo alvo) e **rollback sozinho** se o build
  do APK no GitHub Actions falhar. Gatilho "auto melhore" no chat continua owner-only.
- **Correção de permissão do token**: `get_github_token()` agora prioriza o token salvo
  no banco pelo dono (via `/api/agent/set_github_token`) sobre o `GITHUB_TOKEN` de ambiente.
  Isso contorna o token de ambiente do Render (que tem só leitura) e faz a escrita no repo
  funcionar — a auto-melhoria passa a escrever de verdade.
- (em andamento) **Super Base (Supabase)** + **agendamento de 20 dias** + **vault Obsidian
  no formato LLM Wiki** — ver GUIA_FACIL_NEXUS.md.

## v1.0.0 (tudo funcional — celular / nativo)
- Correções de estabilidade (Jul/2026): backend aceita `null` em campos opcionais
  (`conversation_id`, `note`) que o app envia via Gson; app Android libera tráfego HTTP/WS
  (cleartext) para conexão em dev; deep link `nexusai://spotify/callback`; ícone adaptativo;
  backend migrado para `lifespan` + suíte de testes pytest rodando no CI.
- Conexão em celular físico (Jul/2026): **auto-descoberta do backend via mDNS** (o app acha
  o servidor na mesma Wi-Fi sem digitar IP) + botão **"Testar conexão"** na tela de Login.
  O backend anuncia o serviço `_nexus._tcp` na LAN (requer `zeroconf` instalado).
- Infraestrutura em nuvem (Jul/2026): `render.yaml` + `Procfile` (backend escuta em
  `0.0.0.0:$PORT`); URL padrão do app aponta para `https://nexus-api.onrender.com` via
  `API_BASE_URL`; integração **Firebase Admin SDK** (env vars `FIREBASE_*`, auth bridge
  `/api/auth/firebase` e espelhamento Firestore de usuários/histórico/memória/lembretes).
  Guia passo a passo em `DEPLOY.md`.
- Build do APK nativo Android (Kotlin + Jetpack Compose) gerado e instalável.
- Tela de **Chaves** no app: cole a Groq API Key e o Spotify Client ID/Secret direto pelo app.
- **Hot-reload** da chave Groq: liga o modelo real sem reiniciar o backend.
- **Controle real do celular**: abrir apps, volume, câmera, SMS, ligação e alarme. O backend classifica a intenção e empurra a ação via WebSocket para o app executar.
- **Spotify OAuth real + Web API** (play/pause/próxima/anterior/volume) — exige app no Spotify Developer + conta Premium.
- Canal de ações backend→app (WebSocket) para executar comandos no dispositivo.

## v0.1.0 (fase de testes — celular / nativo)
- Núcleo da IA (FastAPI) com provedor Groq (LLM + Whisper STT).
- Chat por texto com streaming (WebSocket) e modo não-streaming (REST).
- Personalidade "Nexus" definida (inteligente, educado, estratégico, objetivo, humor moderado).
- Memória curta (contexto da conversa) + memória longa (fatos extraídos e persistidos).
- Autenticação JWT (login do dono) + preparação para biometria no app.
- Lembretes e notificações (CRUD + agendador de verificação).
- Plugins: Spotify (stub OAuth) e controle de sistema (stub) — prontos para expandir.
- App Android nativo (Kotlin + Jetpack Compose): login+biometria, chat texto/voz, histórico, lembretes, dispositivos, ajustes.
- Sistema de versão/auto-atualização (VERSION + CHANGELOG + endpoint /api/system/info).
- Cliente web leve (mobile) para testar o cérebro pelo navegador enquanto o app nativo é compilado.
- Modo DEMO (sem chave de API) para validar fluxo e UX antes de conectar o Groq real.
