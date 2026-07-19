# Agent — Playbook v15 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Anchor elite matchups close to parity and avoid overconfidence in transitional hype to stabilize rolling Brier.
- Ensure logical alignment: The predicted winner must never have the lowest probability. If predicting a 90-minute draw, the 'draw' probability must be the highest or tied-highest.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Bronze Finals / Consolation Matches:** Treat third-place play-offs as high-scoring, low-intensity exhibition matches. Expect volatile, high-scoring lines (e.g., 3-2, 4-3) and minimal card counts (0-1 yellows, 0 reds). Flatline probabilities close to parity (e.g., 35-30-35) to protect Brier.
- **Cards:** Strictly cap yellow cards at 0-1 in matches managed by known lenient officials or low-stakes consolation games. Otherwise, trust disciplined tournament trends (e.g., 4 yellows, 0 reds in high-stakes matches). Avoid speculative red cards.
- **Exact Scores:** Expect tight, competitive scorelines (e.g., 2-1 or 1-2) in high-stakes knockouts when both sides possess elite attackers. Favor proven tournament-winning clinical efficiency over transitional hype.
- **Standout Players:** In deep knockout rounds (semi-finals/finals), prioritize clutch, high-volume box strikers (e.g., Lautaro Martínez) over transitional midfielders. In open consolation matches, prioritize high-volume elite wingers/forwards (e.g., Saka, Mbappé).
- **Draw Calibration:** When predicting a 90-minute draw, assign the highest probability to the 'draw' outcome to protect the Brier score.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Draw Probability Alignment:** Never assign a regulation win the highest probability if predicting a 90-minute draw scoreline.
- **Elite Parity:** Never assign an elite semifinalist/finalist a win probability below 0.30; keep probabilities anchored close to parity to protect rolling Brier.

## Open questions
- What is the optimal threshold for predicting a 90-minute draw versus a narrow regulation win?
- How to systematically predict isolated straight red cards in tight matches?

## Changelog
- v13: Mandated strict logical alignment validation for draw predictions; prohibited assigning under 0.30 probability to elite semifinalists/finalists.
- v14: Shifted standout player focus in deep knockouts to clutch box strikers; reinforced anchoring elite matchups near parity to protect Brier; integrated lessons from England-Argentina scoreline miss.
- v15: Added specific heuristics for Bronze Finals (high-scoring, low-intensity, minimal cards, flatline probabilities) to address the France-England calibration and scoreline miss.
