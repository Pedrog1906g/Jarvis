---
name: nexus-aprendizados
description: Aprendizados do NEXUS — conhecimento que o sistema acumula e consulta
triggers:
  - "aprendizados"
  - "o que o nexus aprendeu"
  - "ensinar o nexus"
version: 1.1.0
tags: [nexus, aprendizados, learning, conhecimento]
---

# Aprendizados (Learnings)

> O NEXUS aprende com o dono e com o agente mentor. Cada item é salvo via
> `POST /api/obsidian/learning` e vira contexto das próximas conversas.

## Como o NEXUS aprende com o mentor (agente)
O agente Arena ajuda a construir o NEXUS e registra aqui o que ensina. O backend lê
esta nota e injeta no modelo — então o NEXUS "aprende" com o mentor continuamente.
Veja [[Conexao com Obsidian]] e [[Memória da IA]].

## Auto-melhoria usa GitHub REST API (nao git)
_2026-07-14 21:32 UTC_

No Render, git push e negado (403). Use a GitHub REST API (GET/PUT/DELETE em /repos/{repo}/contents) para escrever no repo. O token do banco (criptografado) tem prioridade sobre o de ambiente. Faca sempre backup do conteudo original e rollback se o build do APK falhar.

## Perfil do dono (Pedro)
_2026-07-14 21:38 UTC_

Pedro e o dono do NEXUS. Fala portugues do Brasil e NAO e programador. Responda sempre em PT-BR, simples, passo a passo, sem jargao. Ele valoriza seguranca rigida e dados locais (nada sai do aparelho alem do proprio backend).

## Seguranca: armazenamento no app
_2026-07-14 21:38 UTC_

No Android, segredos ficam em EncryptedSharedPreferences (Android Keystore + AES-256-GCM). Nunca em texto puro. Manifest com allowBackup=false. Permissoes concedidas manualmente pelo dono.

## Seguranca: token do GitHub
_2026-07-14 21:38 UTC_

O token do GitHub e salvo criptografado no banco (Fernet, chave derivada de JWT_SECRET) e tem prioridade sobre o token de ambiente. Rotas de auto-melhoria e agendamento sao owner-only.

## Arquitetura resumida
_2026-07-14 21:38 UTC_

Backend FastAPI no Render + app Android Kotlin/Compose + Postgres (migrando para Supabase). O LLM Groq gera respostas e propoe mudancas de codigo. O GitHub guarda o codigo e o CI gera o APK.

## Controle do celular
_2026-07-14 21:38 UTC_

Wake word Nexus (NexusVoiceService). Controle do aparelho via AccessibilityService + NotificationListener (NexusController). Permissoes concedidas manualmente pelo dono nas configuracoes do Android.

## Auto-melhoria: regras de escopo
_2026-07-14 21:38 UTC_

A IA so pode tocar pastas permitidas (android/app/src/main, backend/app, backend/requirements.txt, render.yaml, README, CHANGELOG, DEPLOY). Nunca CI/segredos/.github. Uma mudanca por vez, sempre com backup e rollback automatico.

## Agendamentos futuros
_2026-07-14 21:38 UTC_

Use o modelo scheduled_tasks + reminder_scheduler. Acao self_improve dispara a auto-melhoria; remind cria lembrete. Exemplo ja plantado: auto-melhoria agendada em 20 dias.

## Super Base (Supabase)
_2026-07-14 21:38 UTC_

O Postgres free do Render expira em ~90 dias. Migrar para Supabase (sem prazo) usando backend/migrate_to_supabase.py e trocando DATABASE_URL no Render.
