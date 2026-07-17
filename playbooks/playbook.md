# Agent — Playbook v14 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Eliminate home-field bias in neutral-venue matches. Keep probabilities anchored close to parity in elite matchups.
- Ensure logical alignment: The predicted winner must never have the lowest probability.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Aggressively scale down yellow cards (target 0-2) in semifinals and finals. Players actively avoid suspensions, and referees let high-stakes games flow.
- **Standout Players:** In late-stage knockouts, prioritize clutch legacy superstars and primary goalscorers (e.g., Messi, Mbappe) over transitional midfielders, as they dominate MOTM narratives in decisive games.
- **Exact Scores:** Avoid defaulting to clean sheets for favorites against high-threat opponents. Expect tight, competitive scorelines (e.g., 2-1, 1-2) when both sides possess elite attackers.
- **Calibration:** Eliminate home-field bias for neutral-venue matches. Anchor elite parity matchups close to 33-33-33 to protect Brier.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Draw Probability Alignment:** Never assign a regulation win the highest probability if predicting a 90-minute draw scoreline.
- **Elite Parity:** Never assign an elite semifinalist/finalist a win probability below 0.30.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v12: Suppressed yellow cards to 0-1 under lenient referees; prioritized transitional midfielders.
- v13: Mandated strict logical alignment validation; prohibited under 0.30 probability for elite teams.
- v14: Aggressively scaled down yellow cards (0-2) in semis/finals due to suspension-avoidance; pivoted standout player priority back to clutch legacy superstars in late stages; eliminated neutral-venue home bias to protect Brier.
