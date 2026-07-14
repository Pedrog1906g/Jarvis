---
name: nexus-guias
description: Passos rápidos e consertos comuns do NEXUS — health check, revogar token, trocar banco
triggers:
  - "como resolver"
  - "troubleshooting do nexus"
  - "passo a passo nexus"
version: 1.1.0
tags: [nexus, guia, troubleshooting, ops]
---

# Guias e Troubleshooting

## Health check
```bash
curl https://nexus-api-2o1y.onrender.com/api/system/health
# -> {"status":"online","version":"1.0.0"}
```

## Login (owner)
```bash
TOKEN=$(curl -s -X POST https://nexus-api-2o1y.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"owner","passphrase":"nexus"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
```

## Conferir auto-melhoria
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://nexus-api-2o1y.onrender.com/api/agent/self_improve/status
```

## Auto-melhoria não escreve no repo (403)
- Causa comum: o `GITHUB_TOKEN` de ambiente no Render tem **só leitura**.
- Solução: salvar um token com **Contents: write** via
  `POST /api/agent/set_github_token` (vai para o **banco criptografado**, que tem
  prioridade). Veja [[Auto-Melhoria]] e [[Segurança]].

## Trocar o banco para Supabase
Seguir [[Super Base (Supabase)]] (`SUPABASE.md` no repo): migrar dados e trocar
`DATABASE_URL` no Render.

## Revogar o token GitHub (segurança)
Quando tudo estiver num token **dedicado** do Pedro:
1. GitHub → Settings → Developer settings → Fine-grained tokens → revogar o atual.
2. Criar um novo fine-grained token (só p/ `Pedrog1906g/Jarvis`, permissão **Contents:
   read & write**) e registrar no app ou no Render.
> Não revogue antes de registrar o novo, senão a [[Auto-Melhoria]] para de funcionar.

## APK
Gerado pelo CI a cada push em `main`; baixe em `.../releases/latest/download/app-debug.apk`.
Build demora alguns minutos. Ver [[App Android]].

Veja também: [[Backend FastAPI]], [[Segurança]], [[Auto-Melhoria]].
