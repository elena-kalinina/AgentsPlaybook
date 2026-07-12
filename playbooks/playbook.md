# Agent — Playbook v12 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Avoid flat/hedged probabilities. Anchor probabilities consistently to stabilize rolling Brier. Confidently back elite favorites (up to 0.80) against depleted opponents, while maintaining the 0.80 cap to hedge against extreme underdog resilience.
- Ensure logical alignment: The predicted winner must never have the lowest probability. If predicting a 90-minute draw, the 'draw' probability must be the highest or tied-highest.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Cards:** Strictly cap yellow cards at 0-1 in matches managed by known lenient officials (e.g., Turpin, Pinheiro) or in elite matchups where tactical discipline prevents fouling.
- **Red Cards:** Avoid predicting speculative red cards unless there is a clear history of high-stakes aggression or strict refereeing.
- **Draw Calibration:** When predicting a 90-minute draw, assign the highest probability to the 'draw' outcome to protect the Brier score.
- **Exact Scores:** Avoid defaulting to blind clean sheets for favorites against high-threat opponents. Expect tight, competitive scorelines (e.g., 2-1) when both sides possess elite attackers.
- **Standout Players:** Prioritize in-form transitional midfielders and active starters (e.g., Bellingham, Álvarez) over legacy superstar forwards (e.g., Messi, Haaland).

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Draw Probability Alignment:** Never assign a regulation win the highest probability if predicting a 90-minute draw scoreline.
- **Lenient Referees:** Do not default to tournament-average card baselines; heavily weight referee profiles.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?

## Changelog
- v11: Suppressed yellow cards (0-1) in elite-vs-elite matches under lenient referees; refined exact score heuristics to account for elite opponent attack; emphasized consistent probability anchoring to stabilize rolling Brier.
- v12: Suppressed yellow cards to 0-1 under lenient referees (e.g., Turpin, Pinheiro); mandated prioritizing in-form transitional midfielders over legacy forwards for standout players; reinforced draw-calibration anchoring to protect rolling Brier.
