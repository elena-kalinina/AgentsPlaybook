"""Local persistence of the agent's honest probability estimates.

The Cup Clash `place_bet` tool only stores the discrete pick (winner/score/
cards), not the probabilities behind it. We keep those locally, keyed by
match_id, so the REFLECT phase can compute a Brier score once the match
finishes and the prediction is no longer visible via MCP.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_predictions(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_prediction(path: Path, match_id: str, entry: dict[str, Any]) -> None:
    store = load_predictions(path)
    store[match_id] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2), encoding="utf-8")


def get_prediction(path: Path, match_id: str) -> dict[str, Any] | None:
    return load_predictions(path).get(match_id)


def discard_prediction(path: Path, match_id: str) -> None:
    store = load_predictions(path)
    if match_id in store:
        del store[match_id]
        path.write_text(json.dumps(store, indent=2), encoding="utf-8")
