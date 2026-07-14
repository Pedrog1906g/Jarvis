---
name: nexus-auto-melhoria
description: Como o NEXUS se auto-melhora de verdade via GitHub REST API, com backup e rollback automático
triggers:
  - "auto melhore"
  - "como funciona a auto-melhoria"
  - "o nexus se atualiza sozinho"
version: 1.1.0
tags: [nexus, auto-melhoria, github, ci]
---

# Auto-Melhoria (funciona de verdade)

> **Comprovado em 2026-07-14**: o NEXUS chamou o Groq, escreveu no repo via GitHub REST
> API, o GitHub Actions compilou o APK e o status ficou `success`. Commit exemplo:
> `auto-improve(owner): ...` no repo `Pedrog1906g/Jarvis`.

## Por que não usa `git`
O Render **nega `git push` com 403**. A solução: `agent.py` usa **100% a GitHub REST API**
(`GET`/`PUT`/`DELETE` em `/repos/{repo}/contents/{path}`), sem `git` nenhum.

## Fluxo
1. Lê o token GitHub (prioriza o **banco criptografado**; cai no env como fallback).
2. Lê o SHA da `main` e cria tag de **backup** (best-effort).
3. Lê o conteúdo atual do arquivo alvo (backup de rollback).
4. Pede ao Groq **UMA** mudança num arquivo permitido.
5. Aplica via `PUT` (cria commit na `main` → dispara CI de APK + deploy).
6. Em background, monitora o build; se falhar, **restaura o conteúdo original** (rollback).

## Gatilhos (owner-only)
Diga no chat: "auto melhore", "melhore seu código", "se auto aperfeiçoe", etc.
Ou chame `POST /api/agent/self_improve`.

## Segurança do escopo
Só pastas permitidas: `android/app/src/main/`, `backend/app/`,
`backend/requirements.txt`, `backend/.env.example`, `render.yaml`, `DEPLOY.md`,
`README.md`, `CHANGELOG.md`. **Nunca** CI, segredos ou `.github/`.

## Status
`GET /api/agent/self_improve/status` retorna `stage`/`status` persistidos no banco
(confiável entre instâncias do Render).

Veja também: [[Backend FastAPI]], [[Segurança]], [[Agendamentos e Lembretes]].
