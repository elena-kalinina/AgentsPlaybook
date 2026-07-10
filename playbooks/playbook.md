# Agent — Playbook v10 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Avoid overly flat/hedged probabilities on clear favorites. Confidently back elite favorites (up to 0.80 win probability) against depleted or exhausted opponents, while maintaining the 0.80 cap to hedge against extreme underdog resilience.
- Ensure logical alignment: The predicted winner (home or away) must never have the lowest probability. If predicting a 90-minute draw, the 'draw' probability must be the highest or tied-highest.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Align cards with referee profiles, stakes, and physical condition. Heavily depleted or exhausted underdogs in late-stage knockouts often lack the physical energy to commit high-intensity, card-worthy fouls; suppress yellow card predictions (0-1) in these scenarios.
- **Red Cards:** Avoid predicting speculative red cards unless there is a clear history of high-stakes aggression or strict refereeing.
- **Draw Calibration:** When predicting a 90-minute draw, assign the highest probability to the 'draw' outcome to protect the Brier score.
- **Exact Scores:** Avoid defaulting to BTTS (both teams to score) or draws for exhausted underdogs against elite favorites. Expect tight, clean-sheet grinds (1-0, 2-0) for in-form favorites.
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Draw Probability Alignment:** Never assign a regulation win the highest probability if predicting a 90-minute draw scoreline.
- **Physical Exhaustion:** Actively discount underdog goal-scoring and card frequencies when squads are physically spent from previous extra-time matches.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v8: Mandated logical probability alignment, lowered yellow card baseline to 0-1, restricted speculative red cards.
- v9: Mandated draw probability must be highest/tied-highest for level-score predictions, tied card heuristics to referee profiles.
- v10: Allowed aggressive win probabilities (up to 0.80) for elite favorites, suppressed yellow cards and underdog goals for physically exhausted squads.
