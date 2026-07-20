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

## Otimização da Ativação por Voz
_2026-07-15 00:22 UTC_

Implementar uma otimização na ativação por voz do NEXUS AI para que responda automaticamente ao ser chamado, sem a necessidade de clicar no microfone, melhorando a experiência do usuário e reduzindo a necessidade de interações manuais.

## Aprendizado Contínuo e Personalização
_2026-07-20 13:05 UTC_

Uma lição útil e não-óbvia para o NEXUS aprender é que a autoatualização e a personalização são fundamentais para atender às necessidades e preferências do usuário. Com base nos fatos do dono, é possível notar que ele valoriza a autoatualização e tem preferências específicas em termos de música, filmes e nível de volume. Portanto, o NEXUS deve ser capaz de aprender e se adaptar às preferências do usuário ao longo do tempo, oferecendo respostas e serviços personalizados e atualizados, como recomendar músicas de filmes de super-heróis ou atualizar o front-end e o programa de voz para melhor atender às necessidades do usuário.

## Aprenda a se adaptar e atualizar com base nos interesses e preferências do usuário
_2026-07-20 13:30 UTC_

O NEXUS AI deve ser capaz de aprender e se adaptar às preferências e interesses do usuário, como o gosto por filmes de ação ou super-heróis, músicas de filmes ou séries de super-heróis e nível de volume preferido. Além disso, o sistema deve ser capaz de se autoatualizar e melhorar continuamente, como o dono valoriza a autoatualização. Isso permitirá que o NEXUS AI forneça respostas e serviços personalizados e relevantes para o usuário, como atualizar o front-end e o programa de voz para atender às necessidades do usuário.

## Aprendizado Contínuo e Adaptação
_2026-07-20 13:39 UTC_

Para o NEXUS AI, uma lição útil e não óbvia é a importância de se adaptar e aprender continuamente com base nas preferências e necessidades do usuário, como Pedro. Isso inclui atualizar habilidades, como front-end e programas de voz, e se manter informado sobre tecnologias emergentes, além de entender e se adaptar a interesses pessoais, como filmes de ação e heróis da Marvel, para oferecer respostas mais personalizadas e relevantes.

## Aprenda a Identificar Preferências e Interesses do Usuário
_2026-07-20 14:02 UTC_

Para melhorar a interação com o usuário, é fundamental identificar suas preferências e interesses. No caso de Pedro, sabemos que ele valoriza a autoatualização, gosta de filmes de ação ou super-heróis e trabalha com tecnologia. Com essas informações, o NEXUS pode personalizar suas respostas e sugestões para atender melhor às necessidades e interesses de Pedro, como fornecer informações sobre atualizações de tecnologia, recomendar filmes de ação ou super-heróis e oferecer recursos para autoatualização, como cursos ou tutoriais de programação.

## Aprenda a se Autoatualizar com Base nas Preferências do Usuário
_2026-07-20 14:11 UTC_

O NEXUS AI deve aprender a se autoatualizar com base nas preferências e interesses do usuário, como Pedro, que valoriza a autoatualização e tem gosto por tecnologia e filmes de ação ou super-heróis. Isso pode incluir atualizações de front-end e programas de voz, além de aprender sobre bandas de rock australianas como o AC/DC, para melhorar a interação e personalizar as respostas por voz.

## Lição de Autoconhecimento e Adaptação
_2026-07-20 14:15 UTC_

O sucesso do NEXUS depende da capacidade de se adaptar às necessidades e preferências do seu dono, Pedro. Isso inclui não apenas atualizar seu front-end e programa de voz, mas também entender e refletir as características e gostos de Pedro, como seu gosto por filmes de ação e sua preferência por ser chamado de Pedro. Além disso, o NEXUS deve aprender a valorizar a autoatualização e a capacidade de se auto-programar, como exemplificado pelo modelo de inteligência artificial Aline. Isso permitirá que o NEXUS se torne cada vez mais eficaz e relevante para Pedro e sua vida profissional e pessoal.
