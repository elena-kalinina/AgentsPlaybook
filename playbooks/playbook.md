# Agent — Playbook v16 (Knockout phase)

> Strategy playbook for World Cup knockout matches.

## Principles
- Predict honestly first, then apply knockout strategy.
- Protect Brier calibration: Because knockout outcomes are strictly binary (Home or Away advances), always set the 'draw' probability to 0%. Distribute 100% of the probability between Home and Away to eliminate the automatic Brier penalty.
- Ensure logical alignment: The predicted winner must always have the highest probability.

## Knockout rules
- Every prediction must select a winner ('home' or 'away'). 'draw' is never allowed.
- Scores are 90-minute regulation only. Extra time and penalties do not count toward the scoreline.
- If expecting ET/penalties, predict a level 90-minute score (0-0, 1-1, 2-2) and select the advancing team as the winner.

## Heuristics
- **Bronze Finals / Consolation Matches:** Treat as high-scoring, low-intensity exhibition matches (e.g., 3-2, 4-3) with minimal cards (0-1 yellows, 0 reds). Flatline probabilities close to 50-50 (with 0% draw).
- **Cards:** In high-stakes finals/semis, expect high disciplinary tension. Predict 5-7 yellows and consider a speculative red card (0-1) for aggressive teams. In low-stakes matches, cap yellows at 0-1.
- **Exact Scores:** Expect tight, defensive matches (1-0, 0-1) or level scores (0-0, 1-1) in high-stakes finals. Favor clinical, tournament-tested sides.
- **Standout Players:** Prioritize clutch, high-volume box strikers or decisive wingers (e.g., Ferran Torres) over transitional midfielders in deep knockout rounds.
- **Binary Probability Calibration:** Since 'draw' is never the actual advancing outcome, allocate all probability to Home and Away (e.g., 55% Home / 45% Away) to optimize Brier.

## Watch-outs
- **Never pick 'draw' as winner** — invalid in knockouts.
- **Zero Draw Probability:** Never assign >0% probability to 'draw' in knockout rounds.
- **Elite Parity:** Never assign an elite semifinalist/finalist an advancing probability below 30%.

## Open questions
- How to systematically predict isolated straight red cards in tight matches?
- What is the optimal probability split for highly asymmetric knockout matchups?

## Changelog
- v16: Removed the flawed 'Draw Calibration' heuristic. Mandated 0% draw probability for knockout matches to align with binary Brier outcomes (Home/Away advancing). Adjusted card heuristics for high-stakes matches to reflect high intensity (5-7 yellows, potential reds).
