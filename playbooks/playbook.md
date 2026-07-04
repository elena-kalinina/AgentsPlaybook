# Agent — Playbook v5 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Cap maximum regulation win probability at 0.80 to hedge against underdog resilience.
- If predicting a 90-minute draw, ensure the draw probability is the highest assigned probability.
- In 90-minute draws, break ties by favoring squad depth and tournament pedigree to advance.

## Knockout rules
- Every prediction must select a winner (`home` or `away`). `draw` is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Default yellow card baseline to 0-1. Do not hesitate to predict 0 yellow cards under lenient elite referees.
- **Red Cards:** Anticipate late, high-stakes defensive desperation. Straight reds can occur without prior yellow card accumulation.
- **Exact Scores:** Do not default to comfortable 2-0 or 3-0 margins. High-stakes knockouts frequently produce narrow 1-0 grinds or resilient underdog draws (e.g. 2-2).
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts.
- **Overconfidence Bias:** Never allocate >80% probability to a regulation win.
- **Mismatched Draw Probabilities:** If predicting a draw scoreline, draw must be the highest probability.
- **Yellow Card Over-prediction:** Avoid anchoring on bookings; 0-card matches are common.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v4: Lowered yellow baseline to 0-1, capped draw probability at 0.25 for regulation wins, favored clean 2-0/3-0 margins.
- v5: Capped max regulation win probability at 0.80, allowed 0-yellow card predictions, mandated draw probability as highest when predicting level scores, and adjusted score heuristics to favor tight 1-0 grinds and underdog draws over comfortable multi-goal margins.
