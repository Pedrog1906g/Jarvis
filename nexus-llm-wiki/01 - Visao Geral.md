---
name: nexus-visao-geral
description: O que é o NEXUS AI, para que serve e quais problemas resolve para o dono (Pedro)
triggers:
  - "o que é o nexus"
  - "para que serve o nexus"
  - "quem usa o nexus"
version: 1.1.0
tags: [nexus, visao-geral, produto]
---

# Visão Geral — NEXUS AI

Assistente pessoal com **cérebro em nuvem** (FastAPI + Groq) e **corpo no celular**
(app Android nativo em Kotlin/Jetpack Compose). O dono é o **Pedro** (PT-BR, não
programador) e quer tudo **bem seguro e rígido**, com armazenamento local e auto-melhoria
real.

## O que ele faz
- Conversa por texto/voz com streaming (WebSocket) e memória de longo prazo.
- **Acorda por voz** ao dizer "Nexus" (wake word) e responde em português.
- **Controla o celular**: abrir apps, volume, câmera, SMS, ligação, alarme, ler tela e notificações (via AccessibilityService + NotificationListener).
- **Se auto-melhora**: pede para "se auto melhorar" e ele muda o próprio código, testa o build e publica (ver [[Auto-Melhoria]]).
- **Agenda tarefas** para o futuro, ex.: [[Agendamentos e Lembretes]] (auto-melhoria em 20 dias).

## Pilares
1. **Segurança rígida** — [[Segurança]] (sem segredos em texto puro).
2. **Auto-melhoria de verdade** — [[Auto-Melhoria]].
3. **Dados duráveis** — Postgres (e em breve [[Super Base (Supabase)]]).
4. **Conhecimento organizado** — este vault ([[Memória da IA]]).

Veja também: [[Arquitetura]] e [[Backend FastAPI]].
