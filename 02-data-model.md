# 02 — Data Model (additive)

All changes are **additive** to the existing Cup Clash Supabase project. Do not alter existing tables beyond what's noted. New tables get their own RLS (service-role writes; read access for the demo group as needed).

## Existing tables we rely on (do not modify)

- `profiles(id, display_name, avatar_emoji, country)`
- `groups(id, name, invite_code, ...)`
- `group_members(group_id, user_id, role, total_points, hard_points)`
- `matches(id, api_fixture_id, home_team, away_team, kickoff_at, status, home_score, away_score, yellow_cards, red_cards, prob_home, prob_draw, prob_away, difficulty_score, is_hard_to_predict, ...)`
- `bets(id, group_id, match_id, user_id, predicted_winner, predicted_yellow_cards, predicted_red_cards, predicted_score_home, predicted_score_away, favourite_player, points_awarded, created_at)`

> Note on data sources: fixtures/scores/cards come from API-FOOTBALL on the free tier **queried by date, never by `season=2026`** (that parameter is gated on free). Odds come from The Odds API. The agent system reads matches from the DB; it does not need to re-implement fixture sync.

## New tables

### `ai_agents`
One row per bettor persona.
```sql
create table ai_agents (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,              -- "The Quant"
  persona_key     text not null unique,       -- "quant" (maps to docs/05)
  llm_provider    text not null,              -- "anthropic" | "gemini"
  llm_model       text not null,              -- e.g. "claude-sonnet-4-6"
  avatar_emoji    text,
  profile_id      uuid references profiles(id),       -- its leaderboard identity
  group_member_id uuid references group_members(...), -- its seat in the demo group
  active          boolean not null default true,
  created_at      timestamptz not null default now()
);
```

### `agent_predictions`
The rich prediction behind each bet (the `bets` row stays the human-shaped pick).
```sql
create table agent_predictions (
  id                  uuid primary key default gen_random_uuid(),
  agent_id            uuid not null references ai_agents(id),
  match_id            uuid not null references matches(id),
  bet_id              uuid references bets(id),        -- the placed bet, once made
  predicted_winner    text not null,                   -- 'home'|'draw'|'away'
  prob_home           numeric not null,                -- model confidence, sums to 1
  prob_draw           numeric not null,
  prob_away           numeric not null,
  predicted_score_home int,
  predicted_score_away int,
  predicted_yellows   int,
  predicted_reds      int,
  favourite_player    text,
  reasoning           text not null,                   -- the model's written rationale
  intel_snapshot      jsonb not null,                  -- exactly what it saw
  playbook_version_id uuid references playbook_versions(id),
  created_at          timestamptz not null default now(),
  unique (agent_id, match_id)
);
```

### `agent_reflections`
Post-match learning, one per (agent, match).
```sql
create table agent_reflections (
  id              uuid primary key default gen_random_uuid(),
  agent_id        uuid not null references ai_agents(id),
  match_id        uuid not null references matches(id),
  prediction_id   uuid not null references agent_predictions(id),
  actual_result   jsonb not null,           -- score, cards, scorers
  points_earned   int not null,             -- from the app's points_awarded
  brier_score     numeric,                  -- calibration for the 1X2 prediction
  lesson          text not null,            -- short, actionable takeaway
  created_at      timestamptz not null default now(),
  unique (agent_id, match_id)
);
```

### `playbook_versions`
The evolving strategy doc, versioned per agent. Version 1 is seeded from `playbooks/seed-playbook.md`.
```sql
create table playbook_versions (
  id                    uuid primary key default gen_random_uuid(),
  agent_id              uuid not null references ai_agents(id),
  version               int not null,             -- 1, 2, 3...
  content               text not null,            -- full markdown playbook
  change_summary        text,                     -- what changed vs previous
  created_from_reflection uuid references agent_reflections(id),
  created_at            timestamptz not null default now(),
  unique (agent_id, version)
);
```

### `agent_runs`
Observability: every loop execution, tool call, and model call. Powers the demo's live log.
```sql
create table agent_runs (
  id          uuid primary key default gen_random_uuid(),
  agent_id    uuid references ai_agents(id),
  phase       text not null,        -- 'scan'|'research'|'reason'|'place'|'settle'|'reflect'|'evolve'
  match_id    uuid references matches(id),
  status      text not null,        -- 'ok'|'error'
  detail      jsonb,                -- inputs/outputs/tokens/errors
  started_at  timestamptz not null default now(),
  finished_at timestamptz
);
```

### `intel_cache`
Deterministic, free re-runs. Keyed by match + source.
```sql
create table intel_cache (
  match_id    uuid not null references matches(id),
  source      text not null,        -- 'api_football'|'odds_api'|'news'
  payload     jsonb not null,
  fetched_at  timestamptz not null default now(),
  primary key (match_id, source)
);
```

## Metrics view (for the "learning" chart)

A view (or computed query) returning, per agent over time: cumulative points, cumulative hard_points, rolling Brier score, and accuracy (% correct winner). The demo charts Brier trending down and points trending up.

## Setup data

A one-time seed script creates: the demo group, one `profiles` + `group_members` per agent, the `ai_agents` rows, and a `playbook_versions` v1 per agent from the seed playbook. See `docs/10-build-plan.md` Phase 1.
