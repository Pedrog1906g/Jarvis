---
name: nexus-seguranca
description: Modelo de segurança do NEXUS — armazenamento criptografado, JWT, token GitHub no banco, owner-only
triggers:
  - "segurança do nexus"
  - "como o nexus guarda senhas"
  - "token do github criptografado"
version: 1.1.0
tags: [nexus, seguranca, criptografia, jwt]
---

# Segurança (rigida e local)

O dono quer tudo **bem seguro**. Nada de segredos em texto puro.

## App Android
- `TokenStore.kt` → **EncryptedSharedPreferences** (Android Keystore + AES-256-GCM).
- `allowBackup="false"` no manifest (impede backup com segredos).
- Permissões concedidas **manualmente** pelo dono.

## Backend
- **JWT** (`HS256`, 30 dias) gerado em `/api/auth/login` com `passphrase`.
- **Token GitHub**: salvo via `POST /api/agent/set_github_token`, **criptografado com
  Fernet** (chave derivada de `JWT_SECRET`). O banco sozinho não revela o token.
- `get_github_token()` prioriza o token do **banco**; usa o do ambiente como fallback.
- Rotas de auto-melhoria e agendamentos são **owner-only** (`user.username == "owner"`).

## Rede
- CORS aberto em dev; em produção restringir origens.
- WebSocket de chat exige token na query.

## Boas práticas pendentes
- Trocar o `JWT_SECRET` por valor forte e único no Render.
- Usar token GitHub **dedicado** (fine-grained, só p/ este repo) e **revogar** o atual
  quando tudo estiver num token próprio. Ver [[Guias e Troubleshooting]].

Veja também: [[App Android]], [[Auto-Melhoria]], [[Backend FastAPI]].
