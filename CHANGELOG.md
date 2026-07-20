# Changelog — NEXUS AI

Todas as versões importantes do projeto. Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-07-20

### Adicionado
- **Identidade visual própria** (J.A.R.V.I.S / F.R.I.D.A.Y / Cyberpunk / HUD militar):
  - Logo oficial: cérebro cibernético em falha (parafusos, faíscas, rachaduras, circuitos).
  - Banner para GitHub (`assets/banner.svg`).
  - Página de demonstração (`demo/index.html`) — HUD futurista, status e módulos.
- **HUD web estilo Homem de Ferro**: tela de boot ("INICIALIZANDO J.A.R.V.I.S"), moldura HUD,
  painéis holográficos, ticker de status e relógio de Brasília.
- **E-mail via SMTP** configurável em tempo real (`POST /api/email/set_config`), com
  `/api/email/config` e `/api/email/test`. Comando de chat: *"envie um email para …"*.
- **Memória de longo prazo**, busca na web ao vivo e auto-melhoria com backup/reversão.
- **Voz masculina e grave** em PT-BR (web, Windows e Android).

### Removido
- **Integração com Telegram** (função descontinuada por decisão do projeto).
- Código morto e referências órfãs relacionadas ao Telegram.

### Melhorado
- Documentação profissional: README, CHANGELOG, ROADMAP, CONTRIBUTING, SECURITY.
- Organização do repositório (pastas `assets/`, `demo/`, `docs/`).
- Padronização de comentários e estrutura.

## [0.9.0] — 2026-07 (histórico)
- Chat por voz/texto PT-BR em Web, Windows e Android.
- Integração com Obsidian (segundo cérebro) e Spotify.
- Builds automáticos de EXE (Windows) e APK (Android) via GitHub Actions.

---

© Pedrog1906g · Designed & Developed by Pedrog1906g
