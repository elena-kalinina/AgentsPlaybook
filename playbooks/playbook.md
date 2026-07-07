# Agent — Playbook v8 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Cap maximum regulation win probability at 0.80 to hedge against underdog resilience.
- Ensure logical alignment: The predicted winner (home or away) must never be assigned the lowest probability in the distribution.

## Knockout rules
- Every prediction must select a winner (`home` or `away`). `draw` is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Lower yellow card baseline to 0-1. Expect zero cards if referee profiles show high leniency, regardless of knockout intensity.
- **Red Cards:** Avoid predicting speculative red cards unless there is a clear history of high-stakes aggression or strict refereeing.
- **Exact Scores:** Avoid defaulting to draws for underdogs against elite favorites. Expect tight 1-0/2-0 grinds or decisive multi-goal wins for in-form favorites.
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick `draw` as winner** — invalid in knockouts.
- **Probability Alignment:** Never assign the lowest probability to the team predicted to advance.
- **Lenient Referees:** Do not assume knockout intensity automatically drives bookings; respect lenient referee trends.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v6: Raised yellow card baseline to 2-3, integrated referee-specific carding heuristics.
- v7: Lowered yellow card baseline to 1-2, removed the mandate to make draw probability the highest for level-score predictions.
- v8: Mandated logical probability alignment (predicted winner cannot have the lowest probability), lowered yellow card baseline to 0-1, and restricted speculative red cards.
