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

REFLECT_CRITICAL_INSTRUCTIONS = """
Reflection tone: be **critical and precise**, not congratulatory.
- Correct winner with wrong score or cards is a **partial miss**, not a triumph.
- Always compare predicted vs actual on: winner, exact 90-min score, yellow cards, red cards, favourite player.
- Identify patterns (e.g. over-counting yellows, missing reds, picking veterans over in-form scorers).
- This playbook is for **knockouts** — fold in knockout-specific lessons (no draw picks, 90-min scores).
- Recommend playbook update (`should_update_playbook: true`) whenever there is a durable lesson,
  even after a good points day. Do not skip evolution just because winners were correct.
"""

PREDICT_KNOCKOUT_INSTRUCTIONS = """
Match is a **knockout** fixture. Follow knockout betting rules:
- `winner` must be `home` or `away` (never `draw`).
- Scores are 90-minute regulation. Use level scores (0-0, 1-1, etc.) when you expect ET/pens.
- Aim for the **closest realistic** score, card count, and favourite player — every field is scored.
"""
