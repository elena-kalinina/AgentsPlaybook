# 07 — Replay Mode (the demo's backbone)

Replay runs the full loop over matches that have **already finished**, so the "predict → settle → reflect → evolve" arc plays out in two minutes instead of two days, controllably and reproducibly. This is what you actually demo. Don't depend on a live 90-minute match resolving on stage.

## The core trick: blind the results

For each replay match, the harness knows the final result (it's finished) but **withholds it** from the agent until the SETTLE phase. So the agent predicts as if the match were upcoming, then "the match ends" on your cue and reflection runs against the real outcome.

Implement by giving the intel/results tools a **replay clock**: while a match is in the "pre-kickoff" state of the replay, `get_results` returns "not finished" and `get_match_intel` returns only pre-match information. When the harness advances the clock past that match, results unlock.

## Determinism

- **Cached intel.** All intel for replay matches is fetched once and stored in `intel_cache`. Replays read only the cache → identical inputs every rehearsal, zero API calls on stage, no rate-limit risk.
- **Pinned model settings.** Use low/zero temperature for replay so reasoning is stable across rehearsals. (Keep a non-zero option for the "watch it think live" moment if you want variety.)
- **Fixed match set.** Curate an ordered list of finished group-stage matches (config: `replay_matches = [matchId, ...]`). Pick matches where the personas *disagree* and where at least one upset happened, so the Contrarian gets a moment.

## Pacing

A `--speed` flag and a `step` mode:
- `step` — advance one phase per keypress, for narrated walk-throughs.
- `--speed=slow|normal|fast` — auto-advance with delays for an unattended run.

The harness emits clear phase banners ("🔍 The Quant is researching Panama vs England…") so the audience can follow without reading code.

## Isolation from the live group

Replay writes to a **separate replay group / run id**, or tags rows with a `replay_run` id, so demo runs don't pollute the real leaderboard or the live autonomous data. Provide a `reset-replay` command that clears a given replay run's predictions/reflections/bets so you can rehearse repeatedly from a clean slate.

## Suggested replay script (≈2–3 min)

1. Show the league standing at zero.
2. Match A (a clear-favourite game): all agents predict; reveal they mostly agree; settle; small point moves. Establishes the loop.
3. Match B (a near coin-flip / actual upset): personas diverge; the Contrarian breaks from the Quant; settle to show the upset landing; Giant-Killer points move. The story beat.
4. Trigger EVOLVE for one agent: show the v1→v2 **playbook diff** live.
5. Show the rolling-Brier / points chart updating across A→B.
6. Cut to the live showpiece (`08`) for the finale.

## Outputs the harness should expose

- A console/log stream of phases (also written to `agent_runs`).
- The standings + metrics after each match (for the on-screen dashboard).
- The playbook diff for the evolved agent.
