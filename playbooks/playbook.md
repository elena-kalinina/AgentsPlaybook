# Agent — Playbook v4 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Market odds are a strong prior; deviate only with clear tactical reasons.
- In 90-minute draws, break ties by favoring squad depth and tournament pedigree to advance.
- Protect Brier calibration: Cap draw probability at 0.25 when expecting a regulation-time winner.

## Knockout rules
- Every prediction must select a winner (`home` or `away`). `draw` is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Default yellow card baseline to 0–1 per match. Elite knockout referees maintain extremely high booking thresholds.
- **Red Cards:** Anticipate late, high-stakes defensive desperation. Straight reds can occur without prior yellow card accumulation.
- **Exact Scores:** Avoid predicting consolation goals for weaker sides against elite defensive teams (prefer 3-0 over 3-1). Do not default to narrow 1-0 grinds; clean 2-0 or 3-0 margins are common.
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts.
- **Yellow Card Over-prediction:** Do not anchor on bookings. Default to 0-1.
- **Consolation Goal Bias:** Do not award "courtesy" goals to losers when a clean sheet is tactically likely.
- **Draw Over-hedging:** Avoid allocating high draw probability (keep <= 0.25) when predicting a regulation win to protect Brier scores.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v1: Seeded from human workbook.
- v2: Tightened card estimates (2-3Y), added red-card watch, enforced no-draw rule.
- v3: Aggressively lowered yellow baseline to 1-2Y, added draw-breaker pedigree heuristic, and removed consolation goal bias for elite defenses.
- v4: Lowered yellow baseline to 0-1, capped draw probability at 0.25 for regulation wins to protect Brier calibration, and favored clean 2-0/3-0 margins over 1-0 grinds.
