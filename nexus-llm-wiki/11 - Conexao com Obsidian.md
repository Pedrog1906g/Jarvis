---
name: nexus-conexao-obsidian
description: Como o NEXUS está conectado ao vault do Obsidian (leitura e escrita viva)
triggers:
  - "conexao com obsidian"
  - "nexus e obsidian"
  - "como o nexus usa o vault"
version: 1.1.0
tags: [nexus, obsidian, integracao, vault]
---

# Conexão NEXUS ↔ Obsidian

O NEXUS está **conectado** a este vault (formato LLM Wiki). A ligação funciona nos dois
sentidos:

## NEXUS → Obsidian (o sistema enxerga o vault)
A cada conversa, o backend lê as notas curadas deste vault (`Memória da IA`, `Conexão`,
`Aprendizados`) e injeta como contexto no modelo. Ou seja, o NEXUS "sabe" o que está aqui.

## Obsidian → NEXUS (o sistema escreve de volta)
- `POST /api/obsidian/learning` salva um **aprendizado** neste vault (é assim que o
  NEXUS aprende com o dono e com o agente mentor — ver [[Aprendizados (Learnings)]]).
- Após cada **auto-melhoria**, o NEXUS registra a sessão em [[Registro de Sessoes]].
- Assim o conhecimento não fica preso no chat: ele mora no vault e aparece no Obsidian.

## Como manter sincronizado no seu PC
O vault vive na pasta `nexus-llm-wiki/` do repositório. Abra essa pasta como vault no
Obsidian (clone do repo ou cópia local). Quando o NEXUS escreve aqui, o commit vai pro
GitHub e aparece no seu Obsidian ao observar/puxar a pasta.

Veja também: [[Memória da IA]], [[Aprendizados (Learnings)]], [[Registro de Sessoes]].
