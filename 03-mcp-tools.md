# 03 — MCP Tools (the agent's only interface to the world)

The MCP server is the contract between the brain and everything else. Agents never touch Supabase or the APIs directly — they call these tools. This keeps autonomous runs reliable and every action auditable.

Build the server with `@modelcontextprotocol/sdk`. Each tool validates inputs, performs the action with the service-role key, logs to `agent_runs`, and returns structured JSON. Start with a **fake-data stub** of every tool (Phase 2) so the loop can be wired before real data is connected.

## Read tools

### `list_matches`
Input: `{ window: "upcoming" | "finished", limit?: number, from?: ISODate, to?: ISODate }`
Returns matches from the DB: `id, home_team, away_team, kickoff_at, status`, and for finished matches the score/cards. 
**Hides** `is_hard_to_predict` and the probabilities for non-finished matches (Option B). Use this to pick the next ~2 targets.

### `get_match_intel`
Input: `{ match_id }`
Returns the aggregated, cached research bundle (see `intel/`):
```json
{
  "teams": { "home": {...form, ranking, recent results, key injuries}, "away": {...} },
  "head_to_head": [...],
  "market_odds": { "home": 2.10, "draw": 3.40, "away": 3.50, "implied_devigged": {...} },
  "news": [ { "headline": "...", "source": "...", "summary": "..." } ],
  "context": "dead rubber / must-win / etc."
}
```
Odds are provided as intel; the app's hard-to-predict label is NOT. Cached in `intel_cache`; a `refresh: true` flag forces a re-fetch.

### `get_playbook`
Input: `{ agent_id }`
Returns the agent's current playbook content + version number. The agent reads this as its strategy memory before reasoning.

### `get_results`
Input: `{ match_id }`
Returns final score, card counts, and scorer list — **only if the match status is finished**, else an explicit "not finished" response. Used in the settle/reflect phase.

### `get_leaderboard`
Input: `{ group_id }`
Returns standings incl. `total_points` and `hard_points` per member. Used for trash-talk/context and the demo.

## Write tools

### `submit_prediction`
Input:
```json
{
  "agent_id": "...", "match_id": "...",
  "predicted_winner": "home|draw|away",
  "prob_home": 0.45, "prob_draw": 0.28, "prob_away": 0.27,
  "predicted_score_home": 1, "predicted_score_away": 1,
  "predicted_yellows": 4, "predicted_reds": 0,
  "favourite_player": "…",
  "reasoning": "…", "intel_snapshot": {…}, "playbook_version_id": "…"
}
```
Writes an `agent_predictions` row. Probabilities must sum to ~1 (validate). Returns the prediction id.

### `place_bet`
Input: `{ agent_id, match_id, prediction_id }`
Writes a row to the **existing `bets` table** as that agent's `user_id`, copying the picks from the prediction (winner, score, yellows, reds, favourite player). Links the bet back onto the prediction (`bet_id`). Enforces the kickoff lock (no bets after `kickoff_at`). This is the real in-app action; the showpiece module can swap this for a UI click but defaults back to this on failure.

### `record_reflection`
Input: `{ agent_id, match_id, prediction_id, lesson, brier_score? }`
Pulls the actual result + `points_awarded` from the app, computes/accepts the Brier score, writes an `agent_reflections` row. Returns it.

### `update_playbook`
Input: `{ agent_id, new_content, change_summary, created_from_reflection? }`
Writes a new `playbook_versions` row (version = previous + 1). Returns the new version. This is how the agent "learns."

## Logging

Every tool wraps its work in an `agent_runs` entry (`phase`, `status`, `detail` incl. token usage where relevant). The demo's live log and the post-hoc story both read from this table.

## Safety in tools

- `place_bet` only ever writes play-money in-app bets. There is no tool that touches money, payments, or external sites.
- Tools never accept a raw SQL string or arbitrary URL from the model. Inputs are typed and validated.
- Write tools are scoped to agent identities in the demo group; they cannot modify human members' rows.
