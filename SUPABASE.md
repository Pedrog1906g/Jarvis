# Super Base (Supabase) — passo a passo

O NEXUS usa Postgres via SQLAlchemy + `psycopg2`. O Supabase **é** Postgres, então
a troca é direta: não precisa mudar nenhuma linha de código do app — só a string de
conexão (`DATABASE_URL`).

## Por que migrar
- O Postgres free do Render **expira em ~90 dias** (os dados somem).
- O Supabase tem camada free sem prazo e traz Auth, Storage e Realtime de brinde.

## 1) Criar o projeto
1. Acesse https://supabase.com e crie um projeto (região mais perto de você).
2. Anote a **senha** do banco (você define na criação).
3. Vá em **Settings → Database → Connection string** e copie a URI `postgresql://...`.
   Ela tem o formato:
   `postgresql://postgres:<SENHA>@db.<PROJETO>.supabase.co:5432/postgres`

## 2) Migrar os dados atuais
No seu computador (com o repo clonado e o Python do backend instalado):

```bash
cd Jarvis/backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://USUARIO:SENHA@db.render.com:5432/nexus"   # ORIGEM (Render)
export TARGET_DATABASE_URL="postgresql://postgres:<SENHA>@db.<PROJ>.supabase.co:5432/postgres"  # DESTINO
python migrate_to_supabase.py
```

O script cria as tabelas na Super Base e copia todos os dados (usuários, conversas,
mensagens, memória, lembretes, configurações e tarefas agendadas).

> Dica: se preferir, exporte um dump do Render (`pg_dump`) e importe pela UI do
> Supabase (SQL Editor → restaurar). O script acima é o caminho mais simples.

## 3) Apontar o Render para a Super Base
1. No painel do Render, abra o serviço **nexus-api**.
2. **Environment** → edite `DATABASE_URL` e cole a URI do Supabase.
3. Salve e aguarde o deploy (ele reinicia sozinho).
4. Confira: `https://nexus-api-2o1y.onrender.com/api/system/health` deve retornar `online`.

Pronto — o NEXUS está na Super Base, sem prazo de expiração.

## 4) (Opcional) usar Auth/Storage do Supabase
O backend já tem o `AUTH_MODE=jwt` e suporte a Firebase opcional. Para usar o Auth
nativo do Supabase, basta plugar o `SUPABASE_URL` e `SUPABASE_KEY` nas env vars e
(extensão futura) trocar o `security.py` pelo cliente `supabase-py`. Não é necessário
para o funcionamento básico.
