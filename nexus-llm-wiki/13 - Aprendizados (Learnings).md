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
