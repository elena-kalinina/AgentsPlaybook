# 06 — The Evolving Playbook (the "learning")

The playbook is each agent's externalized strategy and memory. It's the star of the demo: agents start from a human-written methodology and, over a few matches, rewrite it into something of their own. Because it's plain markdown and versioned, you can **diff it on screen** — the most concrete "the AI is learning" artifact you can show.

## Format

Each playbook is a markdown doc with stable sections so diffs are readable:

```markdown
# <Agent name> — Playbook v<N>

## Principles
High-level beliefs about how to predict (rarely change).

## Heuristics
Concrete rules currently in use, e.g.:
- "Discount home advantage in neutral-venue World Cup knockouts."
- "If a group game is a dead rubber for one side, widen the draw/upset probability."

## Watch-outs
Mistakes to avoid, learned from reflections:
- "v2: I over-trusted FIFA ranking for African sides — regress toward recent form."

## Open questions
Things the agent is still unsure about and is testing.

## Changelog
- v2 (from match X): <what changed and why>
```

## Lifecycle

1. **Seed (v1).** Created from `playbooks/seed-playbook.md` — our compiled workbook methodology — per agent, lightly flavored by persona. This is the human starting point.
2. **Read every prediction.** The current version is loaded into the REASON phase as strategy context.
3. **Append-on-reflect (lightweight).** Each reflection's `lesson` is stored in `agent_reflections`; it does NOT immediately rewrite the playbook.
4. **Rewrite-on-evolve (heavyweight).** Every N settled matches, the EVOLVE phase feeds the current playbook + the recent reflections to the model and asks it to produce a *new full version* — integrating lessons into Heuristics/Watch-outs, updating the Changelog, keeping it concise. → new `playbook_versions` row.

Keep the playbook short (a page or so). The evolve prompt should instruct the model to consolidate, not endlessly append — pruning stale heuristics is part of learning.

## Evolve-prompt sketch

> *"Here is your current playbook (v{N}) and your last {N} match reflections (prediction, result, points, what you learned). Rewrite the playbook into v{N+1}: fold the durable lessons into Heuristics and Watch-outs, drop anything contradicted by results, keep it under ~400 words, and add a one-line Changelog entry explaining the most important change. Return the full markdown."*

## Calibration & the learning chart

Confidence honesty matters more than raw wins for the "is it learning?" story. Track per agent:

- **Brier score** for the 1X2 prediction: `Σ_o (p_o − y_o)²` over outcomes {home, draw, away}, where `y` is one-hot actual. Lower = better calibrated. Range 0 (perfect) to 2 (worst).
- **Accuracy:** % of matches where `predicted_winner` matched.
- **Points** and **hard_points** over time (from the existing leaderboard).

Compute a **rolling Brier** (e.g. last-5) and chart it per agent. The demo narrative: "Match 1 it was wildly overconfident; by match 5, after rewriting its playbook twice, its calibration has improved" — shown as a line trending down. Surface these via the metrics view from `02-data-model.md`.

> Honesty note for the demo: over a handful of group-stage matches, improvement may be noisy. Frame it as *directional* evidence and let the playbook *diff* (a qualitative, unmistakable change) carry the "learning" claim, with Brier as supporting color. Don't overclaim statistical significance from 5 games.

## What to show on stage

- The **v1 → vN playbook diff** for one agent (ideally the Contrarian or Pundit — their changes read well).
- The agent's **reasoning text** for one match next to the **actual result** and the **lesson** it wrote.
- The **rolling Brier / points** chart for the league.
