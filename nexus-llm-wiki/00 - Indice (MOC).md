---
name: nexus-indice
description: Mapa principal (MOC) do vault de conhecimento do NEXUS AI — ponto de entrada para LLMs e humanos
triggers:
  - "indice do nexus"
  - "por onde comeco"
  - "mapa do conhecimento"
version: 1.1.0
tags: [nexus, indice, moc, wiki]
---

# NEXUS AI — Índice do Conhecimento (LLM Wiki)

Vault em formato **skill LLM Wiki** para o [[NEXUS AI]]. Cada nota tem *frontmatter*
(YAML com `name`, `description`, `triggers`, `version`, `tags`) e usa *wikilinks*
`[[nota]]` para conectar ideias. Abra no [[Obsidian]] para navegar gráfico.

## Como usar
- Humanos: clique nos links `[[...]]` ou use o Graph view do Obsidian.
- LLMs/skills: leia o `frontmatter` de cada nota para decidir se ela responde ao pedido;
  siga os `triggers` para rotear perguntas.

## Mapa de conteúdo
- [[Visão Geral]] — o que é, para quem e o que resolve
- [[Arquitetura]] — componentes e fluxo de dados
- [[Backend FastAPI]] — API, auth, chat, auto-melhoria, agendamentos
- [[App Android]] — telas, wake word, controle do celular, segurança
- [[Auto-Melhoria]] — como o NEXUS se atualiza sozinho (REST API + rollback)
- [[Segurança]] — armazenamento criptografado, JWT, owner-only
- [[Super Base (Supabase)]] — migração do Postgres free para Supabase
- [[Agendamentos e Lembretes]] — tarefas futuras (ex.: auto-melhoria em 20 dias)
- [[Memória da IA]] — o que o NEXUS guarda sobre o dono e o projeto
- [[Guias e Troubleshooting]] — passos rápidos e consertos comuns

> Mantido sincronizado com o repositório `Pedrog1906g/Jarvis` (branch `main`).
