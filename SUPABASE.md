# Supabase — NEXUS AI

O NEXUS já está **preparado** para o Supabase. Não há nada fixado em código: basta
preencher as variáveis de ambiente.

## O que já existe (pronto para usar)
- `supabase/schema.sql` — cria tabelas, índices, RLS (segurança por linha) e o
  trigger que cria o perfil do usuário no login do Auth.
- `supabase/README.md` — passo a passo de configuração.
- `backend/app/core/supabase_client.py` — cliente configurável (no-op se não
  configurado; import preguiçoso do `supabase-py`).
- `backend/app/services/supabase_sync.py` — sincronização best-effort de
  mensagens/memória/config (cross-device). Não quebra se desativado.

## Por que usar
- O Postgres free do Render **expira em ~90 dias** (os dados somem).
- O Supabase tem camada free sem prazo e traz Auth, Storage e Realtime.

## 1) Criar o projeto
1. https://supabase.com → crie um projeto (região perto de você).
2. Anote a senha do banco.
3. Settings → Database → Connection string → copie a URI
   `postgresql://postgres:<SENHA>@db.<PROJ>.supabase.co:5432/postgres`.

## 2) Criar as tabelas
SQL Editor → cole `supabase/schema.sql` → Run.

## 3) Migrar os dados atuais (opcional)
No seu PC (repo clonado, Python do backend instalado):

```bash
cd Jarvis/backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://USUARIO:SENHA@db.render.com:5432/nexus"   # ORIGEM
export TARGET_DATABASE_URL="postgresql://postgres:<SENHA>@db.<PROJ>.supabase.co:5432/postgres"  # DESTINO
python migrate_to_supabase.py
```

O script cria as tabelas na Supabase e copia todos os dados (usuários, conversas,
mensagens, memória, lembretes, configurações e tarefas agendadas).

## 4) Apontar o Render para a Supabase
1. Painel do Render → serviço **nexus-api** → **Environment**.
2. Edite `DATABASE_URL` e cole a URI do Supabase (banco PRINCIPAL), **e** adicione
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
   `SUPABASE_JWT_SECRET` (de Settings → API do Supabase).
3. Salve e aguarde o deploy.
4. Confira: `https://nexus-api-2o1y.onrender.com/api/system/health` → `online`.

## 5) Cross-device (sincronização)
Com as env vars do Supabase definidas, o backend passa a espelhar mensagens e
memória no Supabase (`supabase_sync`). Assim, celular e PC compartilham o contexto
em tempo real quando o backend está online.

> Dica: para usar o Auth nativo do Supabase, basta plugar as env vars acima. O
> `security.py` continua válido (JWT); o cliente `supabase-py` é opcional.
