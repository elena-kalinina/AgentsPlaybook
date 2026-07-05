"""Scheduler daemon: daily 10:00 Brussels loop + one pre-kickoff intel refresh.

Two jobs:
- Cron 10:00 Europe/Brussels → full daily loop (settle → reflect → evolve →
  place provisional bets on the next 3 matches).
- One-shot at (earliest upcoming kickoff − 50 min) → `prebet` refresh of ALL
  upcoming bets in a single batch, so the laptop only needs one wake window.

The refresh job is (re)computed after each daily run and on daemon startup.
A 30-minute misfire grace means a slightly-late laptop wake still fires a
recently missed job; beyond that, the morning's provisional bets stand.

Run: .venv/bin/python -m src.scheduler
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from src.config import load_settings
from src.loop.daily import run_daily_loop, run_place_bets_only, run_prebet_refresh
from src.loop.livelog import live_log
from src.mcp.client import McpClient

BRUSSELS = ZoneInfo("Europe/Brussels")
REFRESH_LEAD = timedelta(minutes=50)
MISFIRE_GRACE_SEC = 30 * 60
REFRESH_JOB_ID = "prebet-refresh"

scheduler = BlockingScheduler(timezone=BRUSSELS)


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


def _load_schedule_matches() -> list[dict[str, Any]]:
    """Upcoming matches: prefer live MCP, fall back to data/schedule.json."""
    settings = load_settings()
    try:
        mcp = McpClient(settings.mcp_url, settings.mcp_token)
        return mcp.list_upcoming_matches(settings.group_id, limit=10)
    except Exception as exc:
        print(f"[scheduler] MCP unavailable ({exc}); falling back to schedule.json")
        if settings.schedule_path.exists():
            data = json.loads(settings.schedule_path.read_text(encoding="utf-8"))
            return data.get("matches", [])
        return []


def sync_refresh_job() -> None:
    """Schedule (or replace) the one-shot refresh at earliest future kickoff − 50 min."""
    matches = _load_schedule_matches()
    kickoffs = sorted(
        ko for m in matches if (ko := _parse_kickoff(m.get("kickoff_at"))) and ko > _now()
    )
    existing = scheduler.get_job(REFRESH_JOB_ID)

    if not kickoffs:
        if existing:
            existing.remove()
        print("[scheduler] no future kickoffs — refresh job not scheduled")
        return

    refresh_at = kickoffs[0] - REFRESH_LEAD
    if refresh_at <= _now():
        # Inside the T-50 window already (or past it): let the existing job /
        # provisional bets stand rather than firing repeatedly on every sync.
        print(
            f"[scheduler] earliest kickoff {kickoffs[0].astimezone(BRUSSELS):%Y-%m-%d %H:%M} "
            f"is < 50 min away — no refresh scheduled (provisional bets stand)"
        )
        return

    scheduler.add_job(
        _prebet_job,
        DateTrigger(run_date=refresh_at),
        id=REFRESH_JOB_ID,
        replace_existing=True,
        misfire_grace_time=MISFIRE_GRACE_SEC,
    )
    print(
        f"[scheduler] refresh scheduled for {refresh_at.astimezone(BRUSSELS):%Y-%m-%d %H:%M} "
        f"Brussels (50 min before {kickoffs[0].astimezone(BRUSSELS):%H:%M} kickoff)"
    )


def _daily_job() -> None:
    print(f"\n[scheduler] daily loop starting @ {datetime.now(BRUSSELS):%Y-%m-%d %H:%M}")
    settings = load_settings()
    try:
        with live_log(settings.live_log_path):
            run_daily_loop(settings)
    except Exception as exc:
        print(f"[scheduler] daily loop FAILED: {exc}")
    sync_refresh_job()


def _prebet_job() -> None:
    print(f"\n[scheduler] prebet refresh starting @ {datetime.now(BRUSSELS):%Y-%m-%d %H:%M}")
    settings = load_settings()
    try:
        with live_log(settings.live_log_path):
            run_prebet_refresh(settings)
    except Exception as exc:
        print(f"[scheduler] prebet refresh FAILED: {exc}")


def _todays_daily_log() -> dict[str, Any] | None:
    settings = load_settings()
    today = datetime.now(BRUSSELS).date()
    for log_path in sorted(settings.logs_dir.glob("run_*.json"), reverse=True):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("mode") != "daily-loop":
            continue
        started = data.get("started_at")
        if not started:
            continue
        dt = _parse_kickoff(started)
        if dt and dt.astimezone(BRUSSELS).date() == today:
            return data
    return None


def _bets_placed_in_log(run_log: dict[str, Any]) -> bool:
    for phase in run_log.get("phases", []):
        if phase.get("phase") == "place" and phase.get("bets"):
            return True
    return False


def _place_bets_job() -> None:
    print(f"\n[scheduler] place-bets resume starting @ {datetime.now(BRUSSELS):%Y-%m-%d %H:%M}")
    settings = load_settings()
    try:
        with live_log(settings.live_log_path):
            run_place_bets_only(settings)
    except Exception as exc:
        print(f"[scheduler] place-bets FAILED: {exc}")
    sync_refresh_job()


def _upcoming_without_bets() -> list[dict[str, Any]]:
    settings = load_settings()
    mcp = McpClient(settings.mcp_url, settings.mcp_token)
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    return [m for m in upcoming if not m.get("my_bet")][: settings.bet_batch_size]


def catch_up_missed_daily() -> None:
    """Catch up after a missed or partial daily loop.

    - No daily log today → full daily loop
    - Daily log with reflection but no placed bets → place-bets only (resume phase 5)
    - No log but upcoming matches still need bets (common after a crash) → place-bets
    - Daily log with bets placed → skip
    """
    now = datetime.now(BRUSSELS)
    if now.hour < 10:
        return

    todays = _todays_daily_log()
    if todays and _bets_placed_in_log(todays):
        print("[scheduler] daily loop completed today — catch-up skipped")
        return

    if todays and todays.get("reflection") and not _bets_placed_in_log(todays):
        print(
            f"[scheduler] daily loop partial (playbook updated, bets missing) — "
            f"resuming place-bets ({now:%Y-%m-%d %H:%M} Brussels)"
        )
        _place_bets_job()
        return

    needs_bets = _upcoming_without_bets()
    if needs_bets and not todays:
        print(
            f"[scheduler] upcoming matches need bets ({len(needs_bets)}) — "
            f"running place-bets ({now:%Y-%m-%d %H:%M} Brussels)"
        )
        _place_bets_job()
        return

    if todays:
        print("[scheduler] daily loop already ran today — catch-up skipped")
        return

    print(
        f"[scheduler] missed 10:00 daily loop — catching up now "
        f"({now:%Y-%m-%d %H:%M} Brussels)"
    )
    _daily_job()


def main() -> None:
    scheduler.add_job(
        _daily_job,
        CronTrigger(hour=10, minute=0, timezone=BRUSSELS),
        id="daily-loop",
        misfire_grace_time=MISFIRE_GRACE_SEC,
    )
    catch_up_missed_daily()
    sync_refresh_job()
    print("[scheduler] running — daily loop at 10:00 Europe/Brussels, Ctrl-C to stop")
    for job in scheduler.get_jobs():
        next_run = getattr(job, "next_run_time", None) or job.trigger
        print(f"[scheduler]   job {job.id}: next run {next_run}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[scheduler] stopped")


if __name__ == "__main__":
    main()
