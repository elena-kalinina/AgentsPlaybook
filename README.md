# Cup Clash — AI Bettor League (agent build spec)

This folder is a build specification for a coding agent (e.g. Claude Code). It adds an **autonomous AI bettor league** on top of the existing *Cup Clash* World Cup 2026 prediction app. Read the docs in order, then follow `docs/10-build-plan.md`.

## What we're building

A set of AI "bettor" agents, each with its own personality and an **evolving strategy playbook**, that:
1. pull data and research for upcoming World Cup matches,
2. reason and produce a prediction (winner, score, cards, favourite player) with confidence,
3. place a real bet in the Cup Clash app **through a tool layer (MCP server)**,
4. after the match settles, compare prediction vs. result, write a lesson, and **rewrite their own playbook**,
5. compete on the existing Cup Clash leaderboard (including the "Giant-Killer" hard-to-predict column).

Three delivery modes:
- **Autonomous mode** — runs unattended (overnight matches) via the MCP/tool path. Reliable, no UI.
- **Replay mode** — re-runs the full loop over already-finished group-stage matches for a fast, reproducible demo narrative. This is the primary demo vehicle.
- **Computer-use showpiece** — ONE live bet placed by clicking the real app UI (Playwright or a computer-use model), with the MCP path as silent fallback. This is theatre, not the backbone.

## Why it's interesting (the demo thesis)

The "brain" (research → predict → reflect → improve) is the robust core and the real AI story. The "hands" (clicking the UI) is flashy but brittle, so it's isolated to a single showpiece with a fallback. Multiple personas turn the existing leaderboard into a race with rooting interest, and the Contrarian persona plugs directly into the Giant-Killer column we already built.

## Prerequisites

The coding agent will need these as environment variables (never commit them):
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — the existing Cup Clash Supabase project.
- `API_FOOTBALL_KEY` — existing fixtures/scores/cards source (free tier; query by date, never by season — see note in `docs/02-data-model.md`).
- `ODDS_API_KEY` — The Odds API (existing, for odds-as-intel).
- `ANTHROPIC_API_KEY` and/or `GEMINI_API_KEY` — the reasoning models for the agents.
- `CUP_CLASH_BASE_URL`, plus a demo agent login — only for the computer-use showpiece.

## Folder map

```
cup-clash-agents/
  README.md                      <- you are here
  AGENTS.md                      <- operating rules FOR the coding agent (read before coding)
  docs/
    01-architecture.md           <- system overview + data flow
    02-data-model.md             <- additive Supabase schema (new tables/columns)
    03-mcp-tools.md              <- the tool contract the agents call
    04-prediction-loop.md        <- the core agent state machine + pseudocode
    05-agent-personas.md         <- the league: Quant, Pundit, Contrarian, Homer
    06-playbook-system.md        <- the evolving strategy doc + versioning + calibration
    07-replay-mode.md            <- deterministic demo harness over finished matches
    08-computer-use-showpiece.md <- single live bet via the real UI + fallback
    09-demo-runbook.md           <- the on-stage script, timings, backup plan
    10-build-plan.md             <- phased build order with checkpoints
  playbooks/
    seed-playbook.md             <- starting strategy (replace with our workbook content)
```

## Build order (summary)

Follow `docs/10-build-plan.md`. In short: data model → MCP tools (with a fake data stub first) → single-agent loop end-to-end on one finished match → reflection + playbook evolution → multi-agent league → replay harness → computer-use showpiece → demo runbook rehearsal.

## Running the built system

Setup: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then copy `.env.example` to `.env` and fill in keys.

CLI commands (all output also streams to `logs/current_run.txt`):

```bash
.venv/bin/python -m src.cli run-daily-loop   # settle → reflect → evolve playbook → bet next N (BET_BATCH_SIZE=2)
.venv/bin/python -m src.cli prebet           # fresh intel + re-place ALL upcoming bets (near kickoff)
.venv/bin/python -m src.cli place-bets          # resume betting only (skip reflection; uses cached intel)
.venv/bin/python -m src.cli reflect-only     # settle + reflect + evolve, no new bets
.venv/bin/python -m src.cli check-models     # probe each configured Gemini model (quota check)
```

Scheduler daemon (local laptop — optional once GitHub Actions is active):

```bash
caffeinate -i .venv/bin/python -m src.scheduler
```

### GitHub Actions (recommended — lid-closed safe)

Push to [github.com/elena-kalinina/AgentsPlaybook](https://github.com/elena-kalinina/AgentsPlaybook) and add these **repository secrets** (Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `APP_MCP_SERVER_URL` | from `.env` |
| `APP_MCP_SERVER_TOKEN` | from `.env` |
| `CUP_CLASH_GROUP_ID` | from `.env` |
| `GEMINI_API_KEY` | from `.env` |
| `TAVILY_API_KEY` | from `.env` |

Two workflows run automatically:

- **Daily agent loop** — 10:00 Europe/Brussels: `reflect-only` then `place-bets` (separate steps so a summarize failure doesn't re-reflect). Pushes playbook + `data/` state back to the repo.
- **Prebet refresh** — every 15 min 14:00–23:59 Brussels: `maybe-prebet` runs only inside the T−50 window.

Manual trigger: Actions tab → workflow → **Run workflow**.

Agent state files (`data/settled.json`, `data/predictions.json`, `data/metrics.json`, etc.) are committed to git so each CI run picks up where the last left off.

Dashboard (playbook history + diffs, points and Brier charts, manual run buttons with live log):

```bash
.venv/bin/streamlit run app/dashboard.py
```

Gemini model routing is configured in `.env` (`GEMINI_MODEL_SUMMARIZE/ANALYZE/ACT` + fallbacks). The roles map to separate free-tier quota buckets so a single exhausted model can't sink a run.

## Non-negotiables

This is a **for-fun, points-only** game. The agents place play-money predictions inside Cup Clash and nothing else. Do not connect any agent, tool, or browser flow to a real sportsbook, real wagering, or real money. See `AGENTS.md`.
