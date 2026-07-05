# Agent — Playbook v6 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Cap maximum regulation win probability at 0.80 to hedge against underdog resilience.
- Avoid over-hedging with draws when there is a significant class or form differential. Maintain high-confidence win probabilities (0.70-0.80) for elite favorites to avoid severe Brier penalties.
- If predicting a 90-minute draw, ensure the draw probability is the highest assigned probability.

## Knockout rules
- Every prediction must select a winner (`home` or `away`). `draw` is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Raise yellow card baseline to 2-3. Adjust upward based on high-stakes knockout intensity and referee-specific carding history.
- **Red Cards:** Anticipate late, high-stakes defensive desperation. Straight reds can occur without prior yellow card accumulation.
- **Exact Scores:** Avoid defaulting to draws for underdogs against elite favorites. Expect tight 1-0/2-0 grinds or decisive multi-goal wins for in-form favorites.
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts.
- **Mismatched Draw Hedging:** Do not hedge with high draw probabilities on mismatched games to protect Brier scores.
- **Yellow Card Under-prediction:** Do not use a 0-1 baseline; knockout intensity naturally drives bookings.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v5: Capped max regulation win probability at 0.80, allowed 0-yellow card predictions, mandated draw probability as highest when predicting level scores, and adjusted score heuristics to favor tight 1-0 grinds and underdog draws.
- v6: Raised yellow card baseline to 2-3, integrated referee-specific carding heuristics, and restricted draw-hedging on mismatched games to protect Brier scores.
