"""Brier score for 1X2 (home/draw/away) prediction calibration.

Brier = Σ_o (p_o − y_o)² over outcomes {home, draw, away}, where y is one-hot
actual. Range 0 (perfect) to 2 (worst). Lower is better calibrated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUTCOMES = ("home", "draw", "away")


def compute_brier(probs: dict[str, float], actual_outcome: str) -> float:
    if actual_outcome not in OUTCOMES:
        raise ValueError(f"actual_outcome must be one of {OUTCOMES}, got {actual_outcome!r}")
    return sum(
        (float(probs.get(o, 0.0)) - (1.0 if o == actual_outcome else 0.0)) ** 2
        for o in OUTCOMES
    )


def load_metrics(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_metrics(path: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    history = load_metrics(path)
    history.extend(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return history


def rolling_brier(history: list[dict[str, Any]], n: int = 5) -> float | None:
    scores = [h["brier_score"] for h in history if h.get("brier_score") is not None]
    if not scores:
        return None
    window = scores[-n:]
    return sum(window) / len(window)
