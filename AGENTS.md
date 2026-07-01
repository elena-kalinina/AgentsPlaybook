# AGENTS.md — instructions for the coding agent

Operating rules for whoever (human or AI) builds this project. Read this before writing code.

## Mission

Build the AI bettor league described in `README.md` and the `docs/` specs. Build it incrementally, testing each phase against `docs/10-build-plan.md` before moving on.

## Guardrails (hard)

1. **Play-money only.** The agents place predictions inside the Cup Clash app for points. Never integrate real betting, real money, payment rails, or external sportsbooks. The word "bet" here means a fun in-app prediction. If a task seems to push toward real wagering, stop and flag it.
2. **Additive to the existing app.** The Cup Clash Supabase project is live and working. Only ADD tables/columns/functions. Never drop, rename, or alter existing columns, the existing `bets` scoring, or existing RLS. New tables get their own RLS.
3. **Secrets via env only.** Never hardcode or commit API keys / service-role keys. Use a `.env` (gitignored) and read from the environment. The Supabase service-role key runs server-side only.
4. **Don't break the humans' game.** Agents are additional participants in a dedicated demo group. They must not write to other users' rows, alter human bets, or change the leaderboard math.

## Tech stack (recommended)

- **Language:** TypeScript / Node 20+. (Python 3.11+ is an acceptable alternative; if chosen, mirror the same module boundaries.)
- **MCP server:** `@modelcontextprotocol/sdk`.
- **DB:** `@supabase/supabase-js` with the service-role key (server-side).
- **Models:** Anthropic SDK (`@anthropic-ai/sdk`) and/or Google Gemini SDK. Make the model provider swappable per agent (see personas).
- **Research/intel:** the model's web-search/tool use for news + the existing API-FOOTBALL and The Odds API for structured data.
- **Computer-use showpiece:** Playwright (primary, deterministic) with an optional Claude computer-use variant. Isolated in its own module.

## Module boundaries

```
src/
  mcp/            # the MCP server: tool definitions -> Supabase/APIs
  intel/          # research aggregation (stats, odds, news) + caching
  agents/         # persona configs, system prompts, model wiring
  loop/           # the prediction/settlement/reflection state machine
  playbook/       # read/version/diff/evolve the strategy docs
  metrics/        # accuracy + Brier calibration computation
  replay/         # deterministic demo harness over finished matches
  showpiece/      # Playwright / computer-use single live bet (+ MCP fallback)
  cli.ts          # entry points: `run-autonomous`, `run-replay`, `showpiece`
```

Keep the **brain** (intel + agents + loop + playbook) independent of the **hands** (showpiece). The loop must work fully through MCP tools with no browser involved.

## Coding conventions

- Every tool call and model call is logged to `agent_runs` (see data model) for observability and the demo.
- All intel fetches are cached by `(match_id, source)` so replays are deterministic and re-runs are free.
- Fail loud in dev, fail soft on stage: the loop should catch a tool error, log it, and continue with the other agents rather than crash a demo.
- Make pacing configurable (a `--speed` flag) so replay can be slowed for narration or sped up for testing.

## Definition of done per phase

See `docs/10-build-plan.md`. Do not start a phase until the previous phase's checkpoint passes. The single most important checkpoint: **one agent completes predict → place (via MCP) → settle → reflect → playbook-update on one real finished match, with all artifacts visible in the DB.**
