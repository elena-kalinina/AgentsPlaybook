"""Decide whether the prebet refresh should run (for GitHub Actions polling)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from src.config import Settings
from src.loop import daily_state
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


def _save_state(settings: Settings, *, cycle_date: str, refreshed: list[str]) -> None:
    path = settings.data_dir / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cycle_date": cycle_date,
                "refreshed_kickoffs": refreshed,
                "last_ran_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def reset_for_daily_cycle(settings: Settings, cycle_date: str) -> None:
    """Clear refresh tracking when a new morning daily cycle completes."""
    _save_state(settings, cycle_date=cycle_date, refreshed=[])


def prebet_window_status(settings: Settings) -> dict[str, Any]:
    """Return whether we should refresh bets now.

    Rules:
    - Today's daily loop (reflect + place-bets) must have finished (after 10:00 Brussels).
    - Refresh at T-50 before each upcoming bet's kickoff (not before daily finished).
    - Polling stays active until the last bet's kickoff has passed (then no-ops).
    """
    daily_ok, daily_done_at, daily_reason = daily_state.ready_for_prebet(settings)
    if not daily_ok:
        return {"in_window": False, "reason": daily_reason}

    mcp = McpClient(settings.mcp_url, settings.mcp_token)
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    now = datetime.now(timezone.utc)
    today = datetime.now(daily_state.BRUSSELS).date().isoformat()

    with_bets = [m for m in upcoming if m.get("my_bet")]
    kickoffs = sorted(
        ko for m in with_bets if (ko := _parse_kickoff(m.get("kickoff_at")))
    )
    future = [ko for ko in kickoffs if ko > now]

    if not kickoffs:
        return {"in_window": False, "reason": "no open bets to refresh"}

    latest = kickoffs[-1]
    if not future:
        return {
            "in_window": False,
            "reason": "all scheduled games have kicked off",
            "latest_kickoff": latest.isoformat(),
        }

    state = _load_state(settings)
    if state.get("cycle_date") != today:
        refreshed: list[str] = []
    else:
        refreshed = list(state.get("refreshed_kickoffs") or [])

    for ko in future:
        ko_iso = ko.isoformat()
        if ko_iso in refreshed:
            continue

        now_bru = now.astimezone(daily_state.BRUSSELS)
        ko_bru = ko.astimezone(daily_state.BRUSSELS)

        # Before 10:00 only refresh early kickoffs today (e.g. 02:00 after yesterday's daily).
        if now_bru.hour < daily_state.DAILY_HOUR:
            if ko_bru.date() != now_bru.date() or ko_bru.hour >= daily_state.DAILY_HOUR:
                continue

        refresh_at = ko - REFRESH_LEAD
        effective = max(refresh_at, daily_done_at.astimezone(timezone.utc))
        if now < effective:
            return {
                "in_window": False,
                "reason": "before refresh window",
                "target_kickoff": ko_iso,
                "refresh_at": effective.isoformat(),
                "latest_kickoff": latest.isoformat(),
            }
        return {
            "in_window": True,
            "target_kickoff": ko_iso,
            "refresh_at": effective.isoformat(),
            "latest_kickoff": latest.isoformat(),
        }

    return {
        "in_window": False,
        "reason": "all kickoffs already refreshed today",
        "latest_kickoff": latest.isoformat(),
    }


def mark_prebet_done(settings: Settings, kickoff_iso: str) -> None:
    today = datetime.now(daily_state.BRUSSELS).date().isoformat()
    state = _load_state(settings)
    refreshed = list(state.get("refreshed_kickoffs") or []) if state.get("cycle_date") == today else []
    if kickoff_iso not in refreshed:
        refreshed.append(kickoff_iso)
    _save_state(settings, cycle_date=today, refreshed=refreshed)
