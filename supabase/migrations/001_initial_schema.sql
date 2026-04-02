-- Naledi Intelligence Platform — Studex Meat
-- Run this in your Supabase SQL Editor to set up the database

-- Agent tasks
create table if not exists agent_tasks (
  id uuid default gen_random_uuid() primary key,
  agent text not null,
  task text not null,
  priority text default 'normal',
  status text default 'queued',
  result jsonb,
  created_at timestamptz default now(),
  completed_at timestamptz
);

-- Campaigns
create table if not exists campaigns (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  status text default 'draft',
  channels text[] default '{}',
  scheduled_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Content
create table if not exists content (
  id uuid default gen_random_uuid() primary key,
  campaign_id uuid references campaigns(id),
  type text not null,
  title text,
  body text,
  agent text,
  status text default 'draft',
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Audiences
create table if not exists audiences (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  segment_rules jsonb default '{}',
  size_estimate int default 0,
  created_at timestamptz default now()
);

-- Token usage tracking
create table if not exists token_usage (
  id uuid default gen_random_uuid() primary key,
  model text not null,
  input_tokens int default 0,
  output_tokens int default 0,
  cost_zar numeric(10,4) default 0,
  agent text,
  created_at timestamptz default now()
);

-- Command history
create table if not exists command_history (
  id uuid default gen_random_uuid() primary key,
  command text not null,
  agent text,
  result jsonb,
  created_at timestamptz default now()
);

-- Enable Row Level Security
alter table agent_tasks enable row level security;
alter table campaigns enable row level security;
alter table content enable row level security;
alter table audiences enable row level security;
alter table token_usage enable row level security;
alter table command_history enable row level security;

-- Allow all access for service role (backend uses service key)
create policy "Service role full access" on agent_tasks for all using (true);
create policy "Service role full access" on campaigns for all using (true);
create policy "Service role full access" on content for all using (true);
create policy "Service role full access" on audiences for all using (true);
create policy "Service role full access" on token_usage for all using (true);
create policy "Service role full access" on command_history for all using (true);
