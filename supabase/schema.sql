-- ============================================================================
-- NEXUS AI — Esquema do Supabase (Postgres)
-- Rode no SQL Editor do Supabase. Nenhuma chave está fixada em código.
-- Depois defina no Render: SUPABASE_URL, SUPABASE_ANON_KEY,
-- SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET (ver supabase/README.md).
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Perfil (para usar o Auth nativo do Supabase no futuro)
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    username text unique,
    display_name text default 'Owner',
    created_at timestamptz default now()
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, username, display_name)
    values (new.id,
            coalesce(new.raw_user_meta_data->>'username', new.email),
            coalesce(new.raw_user_meta_data->>'display_name', 'Owner'))
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Tabelas de dados — identificadas por owner_username (modelo atual do app)
-- ---------------------------------------------------------------------------
create table if not exists public.conversations (
    id bigserial primary key,
    owner_username text not null,
    title text default 'Nova conversa',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_conversations_owner on public.conversations(owner_username);

create table if not exists public.messages (
    id bigserial primary key,
    conversation_id bigint not null references public.conversations(id) on delete cascade,
    role text not null,
    content text not null,
    created_at timestamptz default now()
);
create index if not exists idx_messages_conv on public.messages(conversation_id);

create table if not exists public.memory_facts (
    id bigserial primary key,
    owner_username text not null,
    fact text not null,
    category text default 'geral',
    importance integer default 1,
    created_at timestamptz default now()
);
create index if not exists idx_memory_owner on public.memory_facts(owner_username);

-- Memória vetorial (opcional). Para busca por similaridade, habilite o pgvector:
--   create extension vector;  e troque embedding por vector(1536).
create table if not exists public.memory_embeddings (
    id bigserial primary key,
    owner_username text not null,
    fact_id bigint,
    content text,
    embedding float4[],
    created_at timestamptz default now()
);

create table if not exists public.reminders (
    id bigserial primary key,
    owner_username text not null,
    title text not null,
    note text,
    due_at timestamptz not null,
    done boolean default false,
    notified boolean default false,
    created_at timestamptz default now()
);
create index if not exists idx_reminders_owner on public.reminders(owner_username);

create table if not exists public.plugin_states (
    id bigserial primary key,
    name text unique not null,
    enabled boolean default false,
    config jsonb default '{}'::jsonb,
    updated_at timestamptz default now()
);

create table if not exists public.settings (
    key text primary key,
    value text,
    updated_at timestamptz default now()
);

create table if not exists public.scheduled_tasks (
    id bigserial primary key,
    owner_username text not null,
    action text not null,
    payload jsonb default '{}'::jsonb,
    note text,
    run_at timestamptz not null,
    done boolean default false,
    created_at timestamptz default now()
);
create index if not exists idx_tasks_owner on public.scheduled_tasks(owner_username);

create table if not exists public.files (
    id bigserial primary key,
    owner_username text not null,
    name text not null,
    path text,
    size_bytes bigint default 0,
    storage_key text,
    created_at timestamptz default now()
);
create index if not exists idx_files_owner on public.files(owner_username);

-- Sync de mensagens entre celular e PC (cross-device).
create table if not exists public.sync_messages (
    id bigserial primary key,
    owner_username text not null,
    conversation_id text,
    role text not null,
    content text not null,
    created_at timestamptz default now()
);
create index if not exists idx_syncm_owner on public.sync_messages(owner_username);

-- ---------------------------------------------------------------------------
-- Row Level Security: por padrão nada é visível; o backend escreve com
-- service_role (que bypassa RLS). Anon não acessa nada.
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.memory_facts enable row level security;
alter table public.memory_embeddings enable row level security;
alter table public.reminders enable row level security;
alter table public.scheduled_tasks enable row level security;
alter table public.files enable row level security;
alter table public.sync_messages enable row level security;
alter table public.settings enable row level security;
alter table public.plugin_states enable row level security;

-- Política única: service_role (backend) pode tudo; anon bloqueado.
do $$
declare t text;
begin
  foreach t in array array['profiles','conversations','messages','memory_facts',
    'memory_embeddings','reminders','scheduled_tasks','files','sync_messages',
    'settings','plugin_states']
  loop
    execute format('drop policy if exists %1$s_svc on public.%1$s;', t);
    execute format('create policy %1$s_svc on public.%1$s for all to service_role using (true) with check (true);', t);
  end loop;
end $$;
