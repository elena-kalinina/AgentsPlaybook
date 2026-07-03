"""Track finished bets that have already been researched + reflected on.

Without this, every run re-researches ALL finished bets (Tavily + LLM cost
grows with history). A match_id lands here once a reflection covering it
completes; subsequent settle phases skip it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def mark(path: Path, bets: list[dict[str, Any]]) -> None:
    store = load(path)
    for bet in bets:
        store[bet["match_id"]] = {
            "match": f"{bet['home_team']} vs {bet['away_team']}",
            "points_awarded": bet.get("points_awarded"),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2), encoding="utf-8")
