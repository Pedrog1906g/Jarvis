---
name: nexus-memoria-ia
description: O que o NEXUS guarda — perfil do dono, decisões do projeto e conhecimento persistido
triggers:
  - "o que a ia guarda"
  - "memoria do nexus"
  - "conhecimento do projeto"
version: 1.1.0
tags: [nexus, memoria, conhecimento, dono]
---

# Memória da IA (o que o NEXUS guarda)

Este vault **é** a memória externa do projeto, sincronizado com o repo. Além dele, o
backend persiste dados relacionais (ver [[Backend FastAPI]]):

- `MemoryFact` — fatos duráveis sobre o dono (extraídos das conversas).
- `Conversation` / `Message` — histórico de chat.
- `Reminder` / `ScheduledTask` — lembretes e tarefas futuras.
- `Setting` — configurações, incluindo o **token GitHub criptografado**.
- `User` — dono (`owner`), autenticado por `passphrase`.

## Perfil do dono (Pedro) — conhecimento estável
- Nome: **Pedro** (Pedro Gentil Bastos, `pedrogentil797@gmail.com`).
- Idioma: **português do Brasil**; **não é programador**.
- Preferências: respostas **simples, passo a passo, sem jargão**; quer tudo
  **bem seguro e rígido**; dados ficam **locais** (nada sai do aparelho além do backend).
- Quer o NEXUS **funcionando de verdade** (não protótipo): auto-melhoria real, controle
  real do celular, e tudo conectado ao [[Obsidian]] neste formato LLM Wiki.

## Decisões do projeto (memory)
- Auto-melhoria via **GitHub REST API** (não `git`) por causa do 403 do Render.
- Priorizar **token do banco** sobre env para contornar token de ambiente somente-leitura.
- App Android usa **EncryptedSharedPreferences** + AccessibilityService/NotificationListener.
- Banco migrando para **Supabase** (sem prazo) — ver [[Super Base (Supabase)]].
- Tudo documentado neste vault para ser lido por LLMs/skills.

> Regra de ouro ao editar este vault: mantenha o *frontmatter* e os *wikilinks*; assim
> tanto humanos ([[Obsidian]]) quanto LLMs entendem e navegam o conhecimento.

Veja também: [[Índice (MOC)]], [[Visão Geral]], [[Segurança]].
