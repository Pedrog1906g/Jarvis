-- ============================================================================
-- NEXUS AI — Esquema do Supabase (Postgres)
-- Como usar:
--   1. Supabase -> SQL Editor -> cole este arquivo -> Run.
--   2. Defina no Render as env vars: SUPABASE_URL, SUPABASE_ANON_KEY,
--      SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET (ver supabase/README.md).
-- Nenhuma senha/chave está fixada aqui.
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Perfil do usuário (espelha auth.users do Supabase Auth)
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    username text unique not null,
    display_name text default 'Owner',
    voiceprint text,
    created_at timestamptz default now()
);

-- Trigger: cria um profile automaticamente quando um usuário se registra no Auth.
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
-- Tabelas de dados (owner referencia profiles.id)
-- ---------------------------------------------------------------------------
create table if not exists public.conversations (
    id bigserial primary key,
    owner_id uuid not null references public.profiles(id) on delete cascade,
    title text default 'Nova conversa',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_conversations_owner on public.conversations(owner_id);

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
    owner_id uuid not null references public.profiles(id) on delete cascade,
    fact text not null,
    category text default 'geral',
    importance integer default 1,
    created_at timestamptz default now()
);
create index if not exists idx_memory_owner on public.memory_facts(owner_id);

-- Memória vetorial (opcional). Para busca por similaridade, habilite o pgvector:
--   create extension vector;  e troque embedding por vector(1536).
create table if not exists public.memory_embeddings (
    id bigserial primary key,
    owner_id uuid not null references public.profiles(id) on delete cascade,
    fact_id bigint,
    content text,
    embedding float4[],
    created_at timestamptz default now()
);

create table if not exists public.reminders (
    id bigserial primary key,
    owner_id uuid not null references public.profiles(id) on delete cascade,
    title text not null,
    note text,
    due_at timestamptz not null,
    done boolean default false,
    notified boolean default false,
    created_at timestamptz default now()
);
create index if not exists idx_reminders_owner on public.reminders(owner_id);

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
    owner_id uuid not null references public.profiles(id) on delete cascade,
    action text not null,
    payload jsonb default '{}'::jsonb,
    note text,
    run_at timestamptz not null,
    done boolean default false,
    created_at timestamptz default now()
);
create index if not exists idx_tasks_owner on public.scheduled_tasks(owner_id);

-- Arquivos sincronizados (upload/download entre dispositivos).
create table if not exists public.files (
    id bigserial primary key,
    owner_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    path text,
    size_bytes bigint default 0,
    storage_key text,
    created_at timestamptz default now()
);
create index if not exists idx_files_owner on public.files(owner_id);

-- Sync de mensagens entre celular e PC (identificado por nome de usuário).
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
-- Row Level Security: cada usuário só enxerga os próprios dados.
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
-- settings/plugin_states são de servidor: sem política de anon; só service_role.
alter table public.settings enable row level security;
alter table public.plugin_states enable row level security;

drop policy if exists profiles_select on public.profiles;
create policy profiles_select on public.profiles for select using (auth.uid() = id);
drop policy if exists profiles_update on public.profiles;
create policy profiles_update on public.profiles for update using (auth.uid() = id);

drop policy if exists conversations_rw on public.conversations;
create policy conversations_rw on public.conversations for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists messages_rw on public.messages;
create policy messages_rw on public.messages for all
    using (exists (select 1 from public.conversations c where c.id = conversation_id and auth.uid() = c.owner_id))
    with check (exists (select 1 from public.conversations c where c.id = conversation_id and auth.uid() = c.owner_id));
drop policy if exists memory_rw on public.memory_facts;
create policy memory_rw on public.memory_facts for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists embeddings_rw on public.memory_embeddings;
create policy embeddings_rw on public.memory_embeddings for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists reminders_rw on public.reminders;
create policy reminders_rw on public.reminders for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists tasks_rw on public.scheduled_tasks;
create policy tasks_rw on public.scheduled_tasks for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists files_rw on public.files;
create policy files_rw on public.files for all
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists syncm_svc on public.sync_messages;
create policy syncm_svc on public.sync_messages for all to service_role using (true) with check (true);
drop policy if exists settings_svc on public.settings;
create policy settings_svc on public.settings for all to service_role using (true) with check (true);
drop policy if exists plugins_svc on public.plugin_states;
create policy plugins_svc on public.plugin_states for all to service_role using (true) with check (true);
