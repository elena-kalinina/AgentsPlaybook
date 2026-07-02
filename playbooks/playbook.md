# Agent — Playbook v3 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Market odds are a strong prior; deviate only with clear tactical reasons.
- In 90-minute draws, break ties by favoring squad depth and tournament pedigree to advance.

## Knockout rules
- Every prediction must select a winner (`home` or `away`). `draw` is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Aggressively lower yellow card baseline to 1–2 per match. Do not default to 3-4 yellows; modern knockout discipline often leads to clean games (0-1 bookings).
- **Red Cards:** Anticipate late, high-stakes defensive desperation. Straight reds can occur without prior yellow card accumulation.
- **Exact Scores:** Avoid predicting consolation goals for weaker sides against elite defensive teams (e.g., prefer 3-0 over 3-1). Conversely, expect late offensive desperation from underdogs against favorites who sit back (e.g., 2-1 over 2-0).
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts.
- **Yellow Card Over-prediction:** Stop anchoring on high booking counts.
- **Consolation Goal Bias:** Do not award "courtesy" goals to losers when a clean sheet is tactically likely.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v1: Seeded from human workbook.
- v2: Tightened card estimates (2-3Y), added red-card watch, enforced no-draw rule.
- v3: Aggressively lowered yellow baseline to 1-2Y, added draw-breaker pedigree heuristic, and removed consolation goal bias for elite defenses.
