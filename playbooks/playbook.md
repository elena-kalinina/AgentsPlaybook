# Agent — Playbook v14 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Avoid flat/hedged probabilities (e.g., 0.36/0.32/0.32). If predicting a regulation win, assign the winner a minimum probability of 0.45.
- Ensure logical alignment: The predicted winner must never have the lowest probability. If predicting a 90-minute draw, the 'draw' probability must be the highest or tied-highest.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Target 3 yellow cards for high-stakes physical matches to capture the ±1 margin, but strictly cap at 0-1 under lenient officials (e.g., Barton, Turpin, Pinheiro). Avoid speculative red cards (default to 0).
- **Standout Players:** Prioritize talismanic, penalty-taking strikers (e.g., Kane) in late knockout rounds where goal-scoring is concentrated. Revert to transitional midfielders (e.g., Bellingham) only when strikers lack service.
- **Exact Scores:** Avoid blind clean sheets for favorites against high-threat opponents. Expect tight, competitive scorelines (e.g., 2-1, 1-1) reflecting high-stakes tension.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **No Flat Hedging:** Never assign a regulation winner a probability below 0.45, which severely penalizes Brier calibration.
- **Elite Parity:** Never assign an elite semifinalist/finalist a win probability below 0.30; keep probabilities anchored close to parity to protect rolling Brier.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v12: Suppressed yellow cards to 0-1 under lenient referees; prioritized transitional midfielders over legacy forwards.
- v13: Mandated logical alignment validation; prohibited under 0.30 probability for elite semifinalists; integrated Ivan Barton to lenient referee list.
- v14: Enforced a 0.45 minimum probability floor for predicted regulation winners to eliminate flat hedging; prioritized talismanic strikers over transitional midfielders in late knockouts; adjusted default yellow card targets to 3 for high-stakes matches.
