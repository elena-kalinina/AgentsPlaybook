"""Decide whether the prebet refresh should run (for GitHub Actions polling)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from src.config import Settings
from src.mcp.client import McpClient

REFRESH_LEAD = timedelta(minutes=50)
STATE_FILE = "prebet_state.json"


def _parse_kickoff(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _load_state(settings: Settings) -> dict[str, Any]:
    path = settings.data_dir / STATE_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_state(settings: Settings, earliest_kickoff: str) -> None:
    path = settings.data_dir / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "earliest_kickoff": earliest_kickoff,
                "ran_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def prebet_window_status(settings: Settings) -> dict[str, Any]:
    """Return whether we are in the T-50 window and if prebet already ran for it."""
    mcp = McpClient(settings.mcp_url, settings.mcp_token)
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    now = datetime.now(timezone.utc)
    kickoffs = sorted(
        ko for m in upcoming if (ko := _parse_kickoff(m.get("kickoff_at"))) and ko > now
    )
    if not kickoffs:
        return {"in_window": False, "reason": "no upcoming kickoffs"}

    earliest = kickoffs[0]
    refresh_at = earliest - REFRESH_LEAD
    earliest_iso = earliest.isoformat()
    state = _load_state(settings)
    already = state.get("earliest_kickoff") == earliest_iso

    if now < refresh_at:
        return {
            "in_window": False,
            "reason": "before refresh window",
            "refresh_at": refresh_at.isoformat(),
            "earliest_kickoff": earliest_iso,
        }
    if now >= earliest:
        return {
            "in_window": False,
            "reason": "kickoff started or passed",
            "earliest_kickoff": earliest_iso,
        }
    if already:
        return {
            "in_window": False,
            "reason": "prebet already ran for this kickoff",
            "earliest_kickoff": earliest_iso,
        }
    return {
        "in_window": True,
        "refresh_at": refresh_at.isoformat(),
        "earliest_kickoff": earliest_iso,
    }


def mark_prebet_done(settings: Settings, earliest_kickoff: str) -> None:
    _save_state(settings, earliest_kickoff)
