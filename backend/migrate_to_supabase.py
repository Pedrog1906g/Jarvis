"""Migra os dados do Postgres atual (Render) para a Super Base (Supabase).

Pré-requisitos:
  1. Criar o projeto em https://supabase.com e anotar a connection string
     (Settings -> Database -> Connection string -> URI, já com a senha).
  2. Ter o DATABASE_URL atual (origem = Postgres free do Render) em uma variável.

Uso:
  export DATABASE_URL="postgresql://USUARIO:SENHA@db.render.com:5432/nexus"      # ORIGEM
  export TARGET_DATABASE_URL="postgresql://postgres:SENHA@db.SEU-PROJ.supabase.co:5432/postgres"  # DESTINO
  python backend/migrate_to_supabase.py

O script cria as tabelas no destino e copia todas as linhas (users, conversations,
messages, memory_facts, reminders, plugin_states, settings, scheduled_tasks).

Depois de migrar: no Render -> nexus-api -> Environment, troque DATABASE_URL pela
string da Supabase e aguarde o deploy. O app passa a usar a Super Base.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db import models

SRC = os.getenv("DATABASE_URL")
DST = os.getenv("TARGET_DATABASE_URL")
assert SRC and DST, (
    "Defina DATABASE_URL (origem) e TARGET_DATABASE_URL (destino da Super Base)."
)

print("Origem:", SRC[:25], "...")
print("Destino:", DST[:25], "...")

src_engine = create_engine(SRC, future=True)
dst_engine = create_engine(DST, future=True)

# Garante que as tabelas existem no destino (Supabase já é Postgres).
Base.metadata.create_all(dst_engine)

Src = sessionmaker(bind=src_engine, future=True)()
Dst = sessionmaker(bind=dst_engine, future=True)()

TABLES = [
    models.User, models.Conversation, models.Message, models.MemoryFact,
    models.Reminder, models.PluginState, models.Setting, models.ScheduledTask,
]

for model in TABLES:
    rows = Src.query(model).all()
    print(f"  {model.__tablename__}: {len(rows)} linha(s)")
    for r in rows:
        # expunge da origem e faz merge no destino (upsert por PK)
        Src.expunge(r)
        Dst.merge(r)
    Dst.commit()

print("Migracao para a Super Base concluida com sucesso.")
Src.close()
Dst.close()
