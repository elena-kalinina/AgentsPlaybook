# Agent — Playbook v9 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Cap maximum regulation win probability at 0.80 to hedge against underdog resilience.
- Ensure logical alignment: The predicted winner (home or away) must never be assigned the lowest probability. If predicting a 90-minute draw scoreline, the 'draw' probability must be the highest or tied-highest in the distribution to prevent severe Brier penalties.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Do not default to a flat baseline. Align cards strictly with referee profiles and match context. Expect 0-1 yellows for lenient referees, but raise to 4+ yellows for strict referees or high-stakes matches with aggressive underdogs.
- **Red Cards:** Avoid predicting speculative red cards unless there is a clear history of high-stakes aggression or strict refereeing.
- **Draw Calibration:** When predicting a 90-minute draw, assign the highest probability to the 'draw' outcome to protect the Brier score.
- **Exact Scores:** Avoid defaulting to draws for underdogs against elite favorites. Expect tight 1-0/2-0 grinds or decisive multi-goal wins for in-form favorites.
- **Standout Players:** Prioritize in-form transitional strikers and verified starters over reputation alone.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Draw Probability Alignment:** Never assign a regulation win the highest probability if predicting a 90-minute draw scoreline.
- **Referee Profiles:** Actively check referee historical carding rates before setting card thresholds.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v7: Lowered yellow card baseline to 1-2, removed the mandate to make draw probability the highest for level-score predictions.
- v8: Mandated logical probability alignment (predicted winner cannot have the lowest probability), lowered yellow card baseline to 0-1, and restricted speculative red cards.
- v9: Mandated that draw probability must be highest/tied-highest when predicting a 90-minute draw to protect Brier score, and tied card heuristics directly to referee profiles and underdog intensity.
