"""Track when the morning daily cycle (reflect + place-bets) last completed."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import Settings

BRUSSELS = ZoneInfo("Europe/Brussels")
DAILY_HOUR = 10
STATE_FILE = "daily_state.json"


def load(settings: Settings) -> dict:
    path = settings.data_dir / STATE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def mark_complete(settings: Settings) -> None:
    """Call after reflect + place-bets finish (morning daily cycle)."""
    path = settings.data_dir / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(BRUSSELS)
    path.write_text(
        json.dumps(
            {
                "completed_at": datetime.now().astimezone().isoformat(),
                "brussels_date": now.date().isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def ready_for_prebet(settings: Settings) -> tuple[bool, datetime | None, str]:
    """Prebet may run after the morning daily cycle has completed."""
    state = load(settings)
    completed_at = state.get("completed_at")
    brussels_date = state.get("brussels_date")
    now = datetime.now(BRUSSELS)

    if not completed_at or not brussels_date:
        return False, None, "daily loop has not completed yet"

    try:
        done_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00")).astimezone(BRUSSELS)
    except ValueError:
        return False, None, "invalid daily_state timestamp"

    if now.hour >= DAILY_HOUR:
        if brussels_date != now.date().isoformat():
            return False, None, f"waiting for today's daily loop (last: {brussels_date})"
        return True, done_at, "ok"

    # Before 10:00: only allow T-50 refresh for an early kickoff today, using
    # yesterday's daily (e.g. USA 02:00 after bets placed yesterday morning).
    if done_at.date() >= now.date():
        return False, None, "prebet starts after 10:00 daily loop"

    return True, done_at, "ok (early kickoff window before 10:00)"
