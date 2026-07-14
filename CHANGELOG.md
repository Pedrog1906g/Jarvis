# CHANGELOG — NEXUS AI

## v1.0.0 (tudo funcional — celular / nativo)
- Correções de estabilidade (Jul/2026): backend aceita `null` em campos opcionais
  (`conversation_id`, `note`) que o app envia via Gson; app Android libera tráfego HTTP/WS
  (cleartext) para conexão em dev; deep link `nexusai://spotify/callback`; ícone adaptativo;
  backend migrado para `lifespan` + suíte de testes pytest rodando no CI.
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
