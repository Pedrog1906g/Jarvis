---
name: nexus-super-base
description: Migração do Postgres free do Render para a Super Base (Supabase) — por que e como
triggers:
  - "super base"
  - "supabase"
  - "migrar o banco"
version: 1.1.0
tags: [nexus, supabase, banco, migracao]
---

# Super Base (Supabase)

O NEXUS usa Postgres via SQLAlchemy + `psycopg2`. O **Supabase é Postgres**, então a
troca é só a string de conexão — sem mudar código do app.

## Por que
- Postgres free do Render **expira em ~90 dias** (dados somem).
- Supabase tem camada free sem prazo. Ver [[Agendamentos e Lembretes]] (aviso de renovação).

## Como (resumo; detalhes em `SUPABASE.md` no repo)
1. Criar projeto em https://supabase.com e copiar a URI `postgresql://postgres:<SENHA>@db.<PROJ>.supabase.co:5432/postgres`.
2. Rodar `backend/migrate_to_supabase.py`:
   ```bash
   export DATABASE_URL="...render..."        # origem
   export TARGET_DATABASE_URL="...supabase..." # destino
   python backend/migrate_to_supabase.py
   ```
3. No Render → **nexus-api → Environment**, trocar `DATABASE_URL` pela URI do Supabase.
4. Aguardar deploy e checar `/api/system/health` → `online`.

O script cria as tabelas e copia `users`, `conversations`, `messages`, `memory_facts`,
`reminders`, `plugin_states`, `settings` e `scheduled_tasks`.

Veja também: [[Arquitetura]], [[Backend FastAPI]], [[Guias e Troubleshooting]].
