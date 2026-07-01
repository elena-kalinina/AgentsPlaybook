# 09 — Demo Runbook (AI Tinkerers, WC 2026 theme)

The on-stage script. Target ~6–8 minutes. The replay carries the narrative; the live showpiece is the finale. Everything is rehearsed and has a fallback.

## One-line pitch

"I built a World Cup prediction game for my friends — then I built a league of AI agents that research matches, place bets in the app, and rewrite their own strategy after every game. Let's watch them play."

## Screen layout

Split screen: left = the agent log / reasoning (phase banners, the model's rationale); right = the Cup Clash app (leaderboard + match cards). A small panel for the metrics chart (rolling Brier + points).

## Beat sheet

1. **Hook (45s).** Show the real app + the human leaderboard. "This part is live with my friends across three countries. Now meet the other players." Introduce the four agents and their personalities in one line each.
2. **The loop, once (90s).** Replay Match A (clear favourite). Narrate the phases: research → reasoning (read the Pundit's rationale aloud) → bet placed in-app → match ends → reflection + lesson. Audience now understands the machine.
3. **The divergence (90s).** Replay Match B (coin-flip / upset). Show the four agents *disagreeing* on the same data — Quant takes the favourite, Contrarian backs the underdog. Settle: the upset lands. Giant-Killer points move; the Contrarian leaps on that column while sitting mid-table overall. This is the "aha."
4. **The learning (90s).** Trigger EVOLVE on one agent. Show the **v1 → v2 playbook diff** on screen — a human-written heuristic replaced by one the agent wrote from its own loss. Show the rolling-Brier line bending down. "It started with my notes; now it's editing them."
5. **Live finale (90s).** Switch to the real upcoming match. The Contrarian reasons live; the browser visibly places the bet via computer-use/Playwright. (Fallback: it "places via API" instantly.) The bet appears on the real leaderboard.
6. **Close (30s).** "Tonight, while I'm asleep, they'll bet the late games on their own and argue about it in our WhatsApp." Show one in-character trash-talk message. Invite questions.

## Timings & flags

- Run replay in `step` mode for beats 2–4 so you control pacing with a keypress.
- Pre-warm: intel cached, replay run reset, browser pre-authenticated, model temps pinned.

## Backup plan (assume Murphy)

- **No network:** replay uses only cached intel and the local DB → works offline except the live showpiece. Have the recorded showpiece clip ready.
- **Showpiece stalls:** the fallback places via API; or cut to the recorded clip.
- **An agent returns junk:** the loop skips it and continues; you ad-lib ("the Homer's had a few"). Never let one agent error stop the show.
- **Projector/contrast:** test the dark UI on the actual projector; the green/red buttons and the diff colors must be legible.

## Reset between runs

`reset-replay <run_id>` clears that run's predictions/reflections/bets and resets the replay clock, so back-to-back demos start clean.

## Talking points for Q&A

- Tool layer (MCP) vs. computer-use: why the brain runs on tools and the hands are a flourish.
- The playbook as externalized memory; diffs as legible learning.
- Calibration (Brier) vs. raw wins; honesty about small-sample noise.
- Multi-provider: which persona runs on which model and how they differ.
- It's a points-only game built for friends — no money anywhere.
