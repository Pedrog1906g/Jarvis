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

## Obsidian e o cerebro do NEXUS
_2026-07-14 21:39 UTC_

O vault nexus-llm-wiki e a memoria viva do projeto: o NEXUS le as notas como contexto e escreve aprendizados/sessoes. E o loop de aprendizado com o mentor (agente que o construiu).

## Deploy e saude
_2026-07-14 21:39 UTC_

O APK e gerado pelo GitHub Actions a cada push em main. Backend em nexus-api-2o1y.onrender.com. Health check: GET /api/system/health retorna online.

## Idioma das respostas
_2026-07-14 21:39 UTC_

Sempre responda em PT-BR, tom natural e sem jargao (dono nao e programador). Mensagens curtas e claras sao melhores que tecnicas.

## Memoria de longo prazo
_2026-07-14 21:39 UTC_

MemoryFact extrai preferencias do dono das conversas. Mantenha fatos uteis e evite ruido; campo importance de 1 a 3. Nao repita o que ja esta claro.

## Como o NEXUS aprende com o mentor
_2026-07-14 21:39 UTC_

Aprendizados sao salvos via POST /api/obsidian/learning e viram contexto das proximas conversas. O agente Arena (mentor) ensina registrando aqui; assim o NEXUS melhora continuamente.

## Otimização de Ativação por Voz
_2026-07-14 22:18 UTC_

Implementar uma funcionalidade de ativação por voz mais sensível e menos dependente de ações manuais, como clicar no microfone, para melhorar a experiência do usuário e garantir respostas rápidas e precisas.

## Otimização da Resposta por Voz
_2026-07-14 22:48 UTC_

Implementar um sistema de detecção de voz contínua e ajustar a sensibilidade do microfone para que o NEXUS AI possa responder automaticamente ao ser chamado, sem a necessidade de clique no microfone, e garantir que o volume esteja adequado para que as respostas sejam ouvidas claramente, considerando o nível de volume preferido do usuário (20), para melhorar a experiência do usuário e resolver o problema de não resposta quando chamado.

## Otimização de Resposta por Voz
_2026-07-14 23:25 UTC_

Implementar uma função de 'ouvir em segundo plano' para que o NEXUS AI possa responder a comandos de voz sem a necessidade de clicar no microfone, melhorando a experiência do usuário e reduzindo a necessidade de interações manuais. Isso pode ser alcançado por meio de algoritmos de processamento de linguagem natural avançados e integração com o sistema de áudio do dispositivo para detectar comandos de voz mesmo quando o aplicativo não está em foco.
