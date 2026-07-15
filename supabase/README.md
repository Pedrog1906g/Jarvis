# Supabase — estrutura do NEXUS AI

Tudo que o NEXUS precisa para usar o Supabase **já está preparado** nesta pasta.
Nenhuma chave está fixada em código: basta preencher as variáveis de ambiente.

## Arquivos
- `schema.sql` — cria todas as tabelas, índices, RLS (segurança por linha) e o
  trigger que cria o perfil do usuário no login. Rode no SQL Editor do Supabase.
- `../backend/app/core/supabase_client.py` — cliente configurável (lê env vars;
  é no-op se não configurado). Import preguiçoso do `supabase-py` (não obrigatório).
- `../backend/app/services/supabase_sync.py` — sincronização best-effort
  (mensagens, memória, config) para cross-device. Não quebra o fluxo se desativado.

## Passo a passo
1. Crie o projeto em https://supabase.com (anote a senha do banco).
2. SQL Editor → cole `supabase/schema.sql` → Run.
3. Anote em Settings → API:
   - Project URL (`SUPABASE_URL`)
   - anon public key (`SUPABASE_ANON_KEY`)
   - service_role key (`SUPABASE_SERVICE_ROLE_KEY`) — guarde bem, é secreta
   - JWT Secret (`SUPABASE_JWT_SECRET`)
4. No Render (serviço `nexus-api` → Environment) adicione as 4 variáveis acima.
5. Pronto. O backend passa a espelhar dados no Supabase (cross-device) e a tabela
   `profiles` passa a ser populada automaticamente pelo Auth do Supabase.

## Variáveis (sem valores fixos)
```
SUPABASE_URL=https://<proj>.supabase.co
SUPABASE_ANON_KEY=<anon key>
SUPABASE_SERVICE_ROLE_KEY=<service role key>
SUPABASE_JWT_SECRET=<jwt secret>
```

## Banco de dados
Para usar o Supabase como banco PRINCIPAL (em vez do SQLite/Postgres do Render),
basta trocar `DATABASE_URL` no Render pela connection string do Supabase. O app
já usa SQLAlchemy, então nenhuma linha de código muda — só a string de conexão.
Veja também `../SUPABASE.md` para a migração de dados existentes.
