# Agent — Playbook v2 (Knockout phase)

> Strategy playbook for **World Cup 2026 knockout matches** (Round of 16 onward).

## Principles
- Predict honestly first, then apply knockout strategy to the pick.
- Market odds are a strong prior; deviate only with a stated reason.
- Recent form and availability beat reputation — but knockout pressure tightens games.
- **Every bet must pick a winner** (`home` or `away`). Draw is never valid in knockouts.

## Knockout rules
- Scores are **90-minute regulation only**. Extra time and penalties are not scored.
- If you expect ET/pens: predict the 90-min score (0-0, 1-1, 2-2) **and** pick the tie winner.
- Do not pick open, high-scoring games by default — knockouts often compress after 60'.
- A correct winner with wrong score or cards is a **partial miss**; aim for every field.

## Heuristics
- Start from de-vigged market odds; adjust for absences and knockout caution.
- **Cards:** use recent tournament booking rates — do **not** default to 4 yellows. Round-of-32 data suggests ~2–3 yellows is more typical; watch for late desperation fouls (red card risk in tight games).
- **Exact score:** worth pursuing when intel is strong (+5 bonus). Avoid assuming a consolation goal for the loser (e.g. 3-1 when a clean sheet is likely).
- **Favourite player:** verify likely starters and recent scorers — not just big names (e.g. Jiménez vs in-form Quiñones).

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts (predict 2-2 + pick a side instead).
- We over-count yellows: stop anchoring on 4Y without match-specific evidence.
- We under-count reds: tight knockout games can produce late straight reds.
- Don't assume losers score in comfortable favourite wins (3-0 > 3-1 when defence is solid).

## Open questions
- How to predict late red cards from match state (level score, last 15')?
- When to predict level 90-min scores vs. regulation winner?

## Changelog
- v1: seeded from human workbook, scoped to knockout phase.
- v2: after Round-of-32 review — tighten card estimates (2–3Y baseline), add red-card watch, enforce no-draw rule, chase exact scores not just winners.
