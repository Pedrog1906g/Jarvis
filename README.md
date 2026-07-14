# NEXUS AI — Assistente Pessoal (estilo JARVIS)

![Build APK](https://github.com/Pedrog1906g/Jarvis/actions/workflows/build.yml/badge.svg)
![Backend Tests](https://github.com/Pedrog1906g/Jarvis/actions/workflows/test-backend.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Projeto iniciado em **modo de testes (v1.0.0)**, começando pela **versão de celular (Android nativo)**.
O objetivo é ter tudo **funcional para a fase de testes de 1–2 semanas**, e eu (o agente) vou
**evoluindo o código continuamente** conforme você for testando e pedindo ajustes.

> **Sobre a "IA que se auto-atualiza":** mantemos o controle com você. A evolução é feita por mim
> (o agente) a cada ciclo de feedback. Há também um sistema interno de versão/atualizações:
> `VERSION` + `CHANGELOG.md` + endpoint `/api/system/info` (o app mostra a versão e as novidades).
> Auto-modificação de código em tempo de execução sem supervisão não é seguro, então mantemos
> o fluxo: você testa → me diz o que ajustar → eu atualizo e sobe uma nova versão.

---

## Arquitetura (fase 1)

```
┌─────────────────────────┐      WebSocket / REST      ┌──────────────────────────┐
│  Android (Kotlin)       │  ◄──────────────────────►  │  Núcleo NEXUS (FastAPI)  │
│  Jetpack Compose        │      JWT + JSON            │  - LLM (Groq)            │
│  - Chat texto + voz     │                            │  - Memória curta/longa   │
│  - Biometria            │                            │  - Lembretes             │
│  - Lembretes            │                            │  - Plugins (Spotify...)  │
│  - TTS/STT nativo       │                            │  - Whisper STT           │
└─────────────────────────┘                            └──────────────────────────┘
                                                                │
                                                                ▼
                                                       PostgreSQL / SQLite + Redis (futuro)
```

Tecnologias: **Python + FastAPI**, **Groq** (LLM + Whisper), **Kotlin + Jetpack Compose**,
**WebSocket** (streaming), **JWT** (auth), **SQLite** (padrão, trocável por PostgreSQL),
**TTS/STT** nativo do Android, arquitetura de **plugins** extensível.

---

## O que está FUNCIONAL nesta versão (v1.0.0)

- ✅ **Backend (cérebro) rodando e testado** — login, chat (REST + WebSocket streaming),
  memória, lembretes, plugins, status/versão. Roda em **modo DEMO** sem chave para validar a UX.
- ✅ **Chat por texto** com streaming (tokens aparecendo em tempo real).
- ✅ **Personalidade "Nexus"** definida (inteligente, educado, estratégico, humor moderado).
- ✅ **Memória**: curta (contexto da conversa) + longa (fatos extraídos e persistidos no banco).
- ✅ **Voz no app Android**: STT (fala → texto) e TTS (texto → voz) usando os motores do aparelho.
- ✅ **Autenticação** JWT + tela de login + **desbloqueio por biometria** (guarda o token com segurança).
- ✅ **Lembretes e notificações** (CRUD; agendador no backend marca os vencidos).
- ✅ **Plugins prontos para expandir**: Spotify (stub OAuth) e Controle de Sistema (classificação de intenção).
- ✅ **Histórico** de conversas.
- ✅ **Versionamento / auto-update**: `VERSION`, `CHANGELOG.md`, tela de Ajustes mostra versão e novidades.
- ✅ **Cliente web de teste** (`web/index.html`) para validar o cérebro pelo navegador antes de compilar o app.

### O que ficou funcional nesta versão
- ✅ **Controle real do celular**: abrir apps, volume, câmera, SMS, ligação e alarme. O backend
  classifica a intenção e empurra a ação via WebSocket para o app executar.
- ✅ **Spotify OAuth real + Web API**: play/pause/próxima/anterior/volume (exige app no Spotify
  Developer + conta Premium; conecte pela tela Dispositivos).
- ✅ **Tela de Chaves** no app: cola a Groq API Key (e Spotify) e o backend liga o modelo na hora.

### O que ainda é STUB / próxima fase
- 🟡 **"Ei Nexus" (wake word)**: o botão de voz funciona; detecção contínua por palavra-chave fica
  para depois (ex.: Porcupine).
- 🟡 **Casa inteligente (Home Assistant) e Smart TV / PC**: a arquitetura de plugins existe; a
  integração física é a próxima fase.
- 🟡 **Memória semântica com embeddings** (pgvector) e resumo de documentos/imagens.

---

## 1) Rodar o backend (o cérebro)

Pré-requisitos: Python 3.11+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edite o .env e COLE sua GROQ_API_KEY (não mande a chave no chat — deixe só no arquivo .env)
python run.py
```

- Abrir: http://localhost:8000  •  Documentação: http://localhost:8000/docs
- Sem chave → roda em **modo DEMO** (respostas simuladas) para testar fluxo/UX.
- Pegue a chave em: https://console.groq.com/keys

### Testar o cérebro rápido (sem celular)
Abra `web/index.html` no navegador (PC ou celular, na mesma rede). Informe a URL do servidor
(ex.: `http://192.168.x.x:8000`), usuário `owner`, frase `nexus`. Converse via WebSocket.

Ou via linha de comando (servidor rodando):
```bash
python tests/smoke_test.py
```

---

## 2) Gerar o LINK DE INSTALAÇÃO do APK (GitHub Actions) — recomendado

Esse é o caminho que gera um **link direto de download** (igual a um "link interno de instalação"):
o GitHub Actions compila o APK numa máquina com recursos normais e cria um **Release** com o arquivo —
você abre o link no navegador, o APK baixa e instala (com "Fontes desconhecidas" ativado).

1. Crie um repositório vazio no seu GitHub.
2. Empurre este projeto para ele:
   ```bash
   cd nexus-ai
   git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
   git push -u origin main
   ```
   (ou me mande o repositório + um token de acesso e eu empurro e disparo o build pra você)
3. Vá em **Actions** → o workflow `Build NEXUS AI APK` roda sozinho.
4. Quando terminar, vá em **Releases** → baixe o `app-debug.apk`.
   Link direto de instalação (sempre o APK mais recente):
   `https://github.com/Pedrog1906g/Jarvis/releases/latest/download/app-debug.apk`
5. No celular: abra o link/arquivo → permita "Instalar de fontes desconhecidas" → instale.

> O workflow está em `.github/workflows/build.yml`. Ele instala JDK17 + Android SDK,
> compila `assembleDebug` e publica o APK no Release a cada push na `main`.

### Ou compilar no Android Studio (dev)
Pré-requisitos: **Android Studio** (Hedgehog+), SDK 34.
1. Abra a pasta `android/`, aguarde a sincronização do Gradle.
2. `Run 'app'` num emulador ou celular (USB com Depuração USB).

### Conectar o app ao backend
- **Emulador**: o padrão `http://10.0.2.2:8000` já aponta para o `localhost` do PC. ✅
- **Celular físico** (mesma Wi-Fi do PC):
  - Toque em **"🔎 Buscar na rede"** na tela de Login — o app descobre o backend sozinho via
    mDNS (o backend anuncia o serviço `_nexus._tcp`; precisa de `zeroconf` instalado).
  - Ou digite o IP da máquina, ex.: `http://192.168.1.20:8000` (tela **Ajustes** ou `Login → Servidor`).
  - Use **"Testar"** para validar a conexão antes de logar.
- Libere a porta `8000` no firewall se necessário; celular e PC na mesma Wi-Fi.

### Tela de Chaves (onde você cola a Groq/Spotify)
Em **Ajustes → Chaves**: cole sua **GROQ_API_KEY** (e, se for usar Spotify, o Client ID/Secret do
Spotify Developer). O app manda pro backend, que salva e **liga o modelo real na hora** (sem reiniciar).
Nunca cole a chave no chat — use essa tela.

---

## 3) Fluxo de uso no celular
1. Abrir o app → tela de **Login** (servidor, usuário `owner`, frase `nexus`).
2. Se já logado antes, **desbloqueia com a biometria**.
3. **Chat**: escreva ou toque no 🎤 (fala). A Nexus responde em texto e você pode ouvir (🔊).
4. **☰ menu**: Histórico, Lembretes, Dispositivos, Ajustes.
5. **Lembretes**: ➕ cria (data/hora em `AAAA-MM-DD HH:MM`).
6. **Ajustes**: vê versão, changelog e altera a URL do servidor.

---

## 4) Como funciona a evolução / "auto-update"

- Eu mantenho `VERSION` e `CHANGELOG.md`. A cada melhoria, sobe a versão e registro o que mudou.
- O endpoint `/api/system/info` devolve a versão atual + changelog; a tela Ajustes exibe.
- Você testa por 1–2 semanas, me diz o que está estranho/faltando, e eu aplico as correções
  (código do backend e/ou do app) e gero uma nova versão.
- Para o app nativo, "atualizar" = eu editar o código e você dar um novo `Run` no Android Studio
  (distribuição via Play Store / App Distribution fica para quando estiver maduro).

---

## Próximas fases sugeridas (você prioriza)
1. Wake word "Ei Nexus" (Porcupine) + serviço always-on em background.
2. Casa inteligente (Home Assistant) e integração Smart TV.
3. Memória semântica com embeddings (pgvector) e resumo de documentos/imagens.
4. App para Windows/Linux.
5. Pipeline de atualização OTA (Firebase App Distribution / Play Store).

---

## Estrutura de pastas
```
nexus-ai/
├── VERSION, CHANGELOG.md, README.md
├── backend/            # Núcleo FastAPI (LLM Groq, memória, voz, plugins, auth)
│   ├── app/ (api, core, db, plugins, services)
│   ├── tests/smoke_test.py
│   └── run.py
├── android/            # App nativo Kotlin + Jetpack Compose
│   └── app/src/main/ (ui, data, viewmodel, util, service)
└── web/                # Cliente web leve para testar o cérebro
```
