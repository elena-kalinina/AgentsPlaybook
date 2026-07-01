# 04 — The Prediction Loop

The core state machine each agent runs. It works entirely through the MCP tools — no browser. Same loop powers autonomous and replay modes; only the clock and the data source for "finished" differ.

## Phases

1. **SCAN** — `list_matches({window:"upcoming", limit:2})`. Pick the next targets the agent hasn't predicted yet.
2. **RESEARCH** — `get_match_intel({match_id})` for each. (Cached → free + deterministic.)
3. **REASON** — load `get_playbook({agent_id})`; call the agent's model with: persona system prompt + current playbook + intel. Model returns a structured prediction (winner, per-outcome probabilities, score, cards, favourite player) + written reasoning. → `submit_prediction`.
4. **ACT** — `place_bet({agent_id, match_id, prediction_id})`. (Showpiece swaps this for a UI click for one match only.)
5. **SETTLE** — when the match status becomes finished, `get_results({match_id})`. The app has already scored the bet → `points_awarded`.
6. **REFLECT** — call the model with: the original prediction + reasoning, the actual result, points earned, and the Brier score. Model returns a short, actionable `lesson`. → `record_reflection`.
7. **EVOLVE** — every `N` settled matches (default N=3, or on demand), call the model with the playbook + the recent reflections and ask it to **rewrite the playbook**, returning new content + a change summary. → `update_playbook` (new version).

Then loop back to SCAN.

## Reasoning contract (structured output)

The model must return JSON matching the `submit_prediction` shape. Enforce it: instruct "return ONLY this JSON, no prose," parse defensively, and on parse failure, retry once with the error echoed back. Probabilities must sum to ~1; normalize if slightly off.

The **discrete pick** (`predicted_winner`) is the persona's choice, which may differ from `argmax(prob)` — e.g. the Contrarian may back a high-value underdog even when the favourite has the highest probability. Keep both: probabilities are the agent's honest belief (used for Brier calibration), the pick is its strategy.

## Pseudocode

```ts
async function runAgentOnMatch(agent, match) {
  log(agent, 'research', match);
  const intel = await tools.get_match_intel({ match_id: match.id });

  const playbook = await tools.get_playbook({ agent_id: agent.id });
  log(agent, 'reason', match);
  const prediction = await reasonWithModel(agent, playbook, intel); // -> structured JSON
  const { id: predictionId } = await tools.submit_prediction({
    agent_id: agent.id, match_id: match.id, ...prediction,
    intel_snapshot: intel, playbook_version_id: playbook.versionId,
  });

  log(agent, 'place', match);
  await tools.place_bet({ agent_id: agent.id, match_id: match.id, prediction_id: predictionId });
}

async function settleAndReflect(agent, match) {
  const result = await tools.get_results({ match_id: match.id });
  if (!result.finished) return;
  const prediction = await getPrediction(agent.id, match.id);
  const brier = brierScore(prediction.probs, result.outcome);
  log(agent, 'reflect', match);
  const lesson = await reflectWithModel(agent, prediction, result, brier);
  await tools.record_reflection({
    agent_id: agent.id, match_id: match.id,
    prediction_id: prediction.id, lesson, brier_score: brier,
  });
}

async function maybeEvolve(agent) {
  const reflections = await recentReflections(agent.id, sinceLastEvolve = N);
  if (reflections.length < N) return;
  const playbook = await tools.get_playbook({ agent_id: agent.id });
  log(agent, 'evolve');
  const { content, summary } = await evolveWithModel(agent, playbook, reflections);
  await tools.update_playbook({
    agent_id: agent.id, new_content: content, change_summary: summary,
  });
}
```

## Scheduling

- **Autonomous:** a scheduler (cron / Supabase scheduled function / a long-running runner) calls `runAgentOnMatch` when a match enters the betting window, and `settleAndReflect` + `maybeEvolve` when it finishes. Stagger agents so model/API rate limits aren't hit at once.
- **Replay:** the harness drives the phases manually over already-finished matches at a controlled pace (see `07-replay-mode.md`).

## Robustness

- One agent's failure (tool error, model timeout, bad JSON) is logged and skipped; other agents continue. Never throw out of the top-level loop during a demo.
- All model calls have timeouts and a single retry.
- Idempotency: predictions and reflections are unique per `(agent, match)`; re-running a phase must not duplicate rows or double-count points.
