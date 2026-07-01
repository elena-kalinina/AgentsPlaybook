# 10 — Build Plan (phased, with checkpoints)

Build in this order. Do not start a phase until the previous checkpoint passes. Each phase is independently demoable, so even a partial build has something to show.

## Phase 0 — Scaffold
- Repo per `AGENTS.md` module layout. `.env.example` with all required vars. `.env` gitignored.
- Connect to the existing Supabase project (service role, server-side). Confirm read access to `matches` and `bets`.
- **Checkpoint:** `cli.ts` runs and can print the next 2 upcoming matches from the live DB.

## Phase 1 — Data model + seed
- Apply the additive schema from `02-data-model.md` (new tables + metrics view). Touch nothing existing.
- Seed script: demo group, one profile + group_member per agent, `ai_agents` rows, `playbook_versions` v1 per agent from `playbooks/seed-playbook.md`.
- **Checkpoint:** the four agents appear on the demo group's leaderboard at 0 points; each has a v1 playbook.

## Phase 2 — MCP tools with a stub
- Implement all tools from `03-mcp-tools.md`, first returning **fake/sample data** so the loop can be built without live APIs.
- **Checkpoint:** an MCP client can call every tool and get well-formed responses; every call writes an `agent_runs` row.

## Phase 3 — Single agent, end-to-end, one finished match
- Wire the loop (`04`) for ONE agent over ONE already-finished match, still on stubbed intel if needed.
- Implement `submit_prediction` → `place_bet` (real `bets` write) → `get_results` → `record_reflection`.
- **Checkpoint (the critical one):** one agent completes predict → place → settle → reflect on a real finished match; the bet shows on the leaderboard, points match the app's scoring, a reflection with a Brier score exists.

## Phase 4 — Real intel
- Implement the `intel/` aggregator: API-FOOTBALL (by date), The Odds API, and model web-search for news; normalize; cache in `intel_cache`.
- Swap the stub `get_match_intel` for the real one.
- **Checkpoint:** intel bundles look sane for 3 sample matches and are cached; a second run hits cache (no API calls).

## Phase 5 — Playbook evolution + metrics
- Implement EVOLVE (`06`) and the calibration metrics view; wire the rolling-Brier/points computation.
- **Checkpoint:** after N reflections, a v2 playbook is written with a sensible diff vs v1; the metrics view returns per-agent points + rolling Brier.

## Phase 6 — Multi-agent league
- Run all four personas (`05`); stagger to respect rate limits; add the optional trash-talk → WhatsApp share.
- **Checkpoint:** on one match, the four agents produce visibly different predictions and reasoning; standings update with the Contrarian leading Giant-Killer.

## Phase 7 — Replay harness
- Implement the replay clock, result-blinding, `--speed`/`step`, isolated replay run, and `reset-replay` (`07`).
- Curate the replay match list (disagreement + an upset).
- **Checkpoint:** a full replay over the curated matches runs offline from cache, reproducibly, in ~2–3 min, with phase banners and a playbook diff.

## Phase 8 — Computer-use showpiece
- Add `data-testid` hooks to the Cup Clash bet UI (additive). Build the Playwright flow (`08`) + MCP fallback. Optionally add the computer-use variant.
- **Checkpoint:** the showpiece places one live bet visibly; deliberately breaking a selector triggers the API fallback with no crash.

## Phase 9 — Demo rehearsal
- Run the full `09` runbook end to end on the actual demo hardware/projector. Record the backup clip. Time it.
- **Checkpoint:** two clean back-to-back rehearsals (with `reset-replay` between), under time, with the network unplugged for everything except the live showpiece.

## Cut lines (if time is short)

Ship in this priority: Phases 0–5 (single learning agent) → Phase 7 (replay) → Phase 6 (full league) → Phase 8 (showpiece). The showpiece is the most cuttable; a recorded clip can stand in. The learning loop + replay is the irreducible core of the demo.
