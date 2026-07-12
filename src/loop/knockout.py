"""Knockout-phase rules for Cup Clash predictions."""

KNOCKOUT_PLAYBOOK_PREAMBLE = """
This playbook applies specifically to the **knockout phase** (Round of 16 onward).
Group-stage heuristics about dead rubbers and draws-as-results do not apply.
"""

KNOCKOUT_BETTING_RULES = """
## Knockout betting rules (Cup Clash app)
- You MUST pick a winner: `home` or `away`. **`draw` is NOT allowed** in knockout matches.
- Scores are **90-minute regulation only** (before extra time / penalties).
- If you expect extra time or penalties, predict the 90-minute score (e.g. 0-0, 1-1, 2-2)
  AND pick the side you believe wins the tie (ET or pens).
- Example: Belgium 2-2 Senegal at 90' but Belgium wins on pens → winner=home, score 2-2.
"""

CUP_CLASH_SCORING_RULES = """
## Cup Clash scoring (per match, additive — max 13 points)
Each field is scored independently against the actual 90-minute result:
- **Correct winner** (home/away): **3 points**
- **Exact score** (predicted_home_score + predicted_away_score match actual): **5 points**
- **Favourite player** (goalscorer pick matches actual MOTM/goalscorer): **2 points**
- **Exact yellow cards**: **2 points**
- **Yellow cards within ±1** of actual (but not exact): **1 point**
- **Exact red cards**: **1 point**

Prioritize fields by expected value: exact score (5) > winner (3) > exact yellows or favourite
player (2 each) > yellows ±1 or exact reds (1 each). In reflection, break down points_awarded
against this rubric — do not treat winner-only hits as a full success.
"""

REFLECT_CRITICAL_INSTRUCTIONS = """
Reflection tone: be **critical and precise**, not congratulatory.
- Correct winner with wrong score or cards is a **partial miss**, not a triumph.
- Always compare predicted vs actual on: winner, exact 90-min score, yellow cards, red cards, favourite player — and map misses to the **Cup Clash scoring rubric** (exact score 5, winner 3, etc.).
- Identify patterns (e.g. over-counting yellows, missing reds, picking veterans over in-form scorers).
- This playbook is for **knockouts** — fold in knockout-specific lessons (no draw picks, 90-min scores).
- Track **two feedback signals**: (1) **Brier** — are prob_home/draw/away well calibrated? Lower rolling Brier (last 5) is better. (2) **Points** — are we maximizing Cup Clash score? Higher rolling points (last 5) is better.
- Good calibration without points means honest but wrong picks; high points with bad Brier means lucky but miscalibrated. The playbook must improve **both** over time.
- Recommend playbook update (`should_update_playbook: true`) whenever there is a durable lesson,
  even after a good points day. Do not skip evolution just because winners were correct.
"""

PERFORMANCE_OBJECTIVE = """
## Dual objective: calibration AND points
Cup Clash scores discrete picks using the rubric above (max 13 pts/match). We also track
honest 1X2 probabilities for **Brier calibration** (lower = better, 0 perfect).
Success = **rolling points (last 5) trending up** AND **rolling Brier (last 5) trending down**.
When they conflict: maximize expected Cup Clash points using the field weights (exact score
worth most), but keep reported probabilities honest and close to market/true rates — do not
spike probs to game Brier.
"""

PREDICT_KNOCKOUT_INSTRUCTIONS = """
Match is a **knockout** fixture. Follow knockout betting rules:
- `winner` must be `home` or `away` (never `draw`).
- Scores are 90-minute regulation. Use level scores (0-0, 1-1, etc.) when you expect ET/pens.
- Aim for the **closest realistic** score, card count, and favourite player — every field is scored.
- Optimize for **Cup Clash points** using the scoring rubric — exact score (5) and winner (3) are the highest-value fields.
- Report **honest calibrated** prob_home/prob_draw/prob_away (for Brier) — well-spread, not overconfident.
"""
