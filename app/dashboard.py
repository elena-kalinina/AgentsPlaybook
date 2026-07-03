"""Streamlit dashboard: playbook evolution, performance, and manual run controls.

Run: .venv/bin/streamlit run app/dashboard.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load_settings  # noqa: E402
from src.mcp.client import McpClient  # noqa: E402

LOCK_PATH = ROOT / "data" / "run.lock"

st.set_page_config(page_title="AgentsPlaybook", page_icon="⚽", layout="wide")


@st.cache_resource
def _settings():
    return load_settings()


settings = _settings()


@st.cache_data(ttl=120)
def fetch_bets() -> list[dict]:
    mcp = McpClient(settings.mcp_url, settings.mcp_token)
    return mcp.get_my_bets(settings.group_id, include_finished=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def playbook_history() -> list[dict]:
    """Commits touching the playbook, newest first."""
    fmt = "%H%x1f%ad%x1f%s"
    out = subprocess.run(
        ["git", "log", f"--format={fmt}", "--date=format:%Y-%m-%d %H:%M", "--", "playbooks/playbook.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout
    commits = []
    for line in out.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def playbook_diff(commit_hash: str) -> str:
    out = subprocess.run(
        ["git", "show", "--format=", commit_hash, "--", "playbooks/playbook.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout
    return out.strip()


def run_in_progress() -> int | None:
    """Return PID of a live run, cleaning up stale lockfiles."""
    if not LOCK_PATH.exists():
        return None
    try:
        pid = int(LOCK_PATH.read_text().strip())
        os.kill(pid, 0)  # existence check, no signal sent
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        LOCK_PATH.unlink(missing_ok=True)
        return None


def launch_run(command: str) -> None:
    if run_in_progress():
        st.warning("A run is already in progress — wait for it to finish.")
        return
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.live_log_path.parent.mkdir(parents=True, exist_ok=True)
    settings.live_log_path.write_text("", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.cli", command],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,  # output goes to the live log via the tee
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    LOCK_PATH.write_text(str(proc.pid), encoding="utf-8")


st.title("AgentsPlaybook — Cup Clash prediction agent")

tab_playbook, tab_perf, tab_controls = st.tabs(["Playbook", "Performance", "Controls"])


with tab_playbook:
    col_current, col_history = st.columns([1, 1])

    with col_current:
        st.subheader("Current playbook")
        if settings.playbook_path.exists():
            st.markdown(settings.playbook_path.read_text(encoding="utf-8"))
        else:
            st.info("No playbook yet.")

    with col_history:
        st.subheader("Version history")
        commits = playbook_history()
        if not commits:
            st.info("No playbook commits yet.")
        for commit in commits:
            with st.expander(f"{commit['date']} — {commit['subject']}"):
                diff = playbook_diff(commit["hash"])
                st.code(diff or "(no diff)", language="diff")


with tab_perf:
    try:
        bets = fetch_bets()
    except Exception as exc:
        bets = []
        st.error(f"Could not fetch bets from Cup Clash: {exc}")

    finished = [b for b in bets if b.get("status") == "finished"]
    pending = [b for b in bets if b.get("status") != "finished"]

    total_points = sum(b.get("points_awarded") or 0 for b in finished)
    metrics_history = load_json(settings.metrics_path, [])
    brier_scores = [m["brier_score"] for m in metrics_history if m.get("brier_score") is not None]
    rolling = sum(brier_scores[-5:]) / len(brier_scores[-5:]) if brier_scores else None

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total points", total_points)
    m2.metric("Settled bets", len(finished))
    m3.metric("Open bets", len(pending))
    m4.metric("Rolling Brier (last 5)", f"{rolling:.3f}" if rolling is not None else "n/a")

    if finished:
        rows = []
        cumulative = 0
        ordered = sorted(finished, key=lambda b: b.get("kickoff_at") or "")
        for b in ordered:
            cumulative += b.get("points_awarded") or 0
            rows.append(
                {
                    "match": f"{b['home_team']} vs {b['away_team']}",
                    "kickoff": b.get("kickoff_at"),
                    "points": b.get("points_awarded") or 0,
                    "cumulative": cumulative,
                }
            )
        df = pd.DataFrame(rows)
        fig = px.line(
            df, x="match", y="cumulative", markers=True, title="Cumulative points"
        )
        fig.update_layout(xaxis_title="", yaxis_title="points")
        st.plotly_chart(fig, width="stretch")

    if metrics_history:
        mdf = pd.DataFrame(
            [m for m in metrics_history if m.get("brier_score") is not None]
        )
        if not mdf.empty:
            mdf["rolling_5"] = mdf["brier_score"].rolling(5, min_periods=1).mean()
            fig2 = px.line(
                mdf,
                x="match",
                y=["brier_score", "rolling_5"],
                markers=True,
                title="Brier calibration (lower = better, 0 perfect, 2 worst)",
            )
            fig2.update_layout(xaxis_title="", yaxis_title="Brier score")
            st.plotly_chart(fig2, width="stretch")

    if finished:
        st.subheader("Settled bets")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "match": f"{b['home_team']} vs {b['away_team']}",
                        "predicted": f"{b['predicted_home_score']}-{b['predicted_away_score']} ({b['predicted_winner']})",
                        "cards": f"{b['predicted_yellow_cards']}Y/{b['predicted_red_cards']}R",
                        "fav player": b.get("favourite_player", ""),
                        "actual": b.get("actual_score", "?"),
                        "points": b.get("points_awarded") or 0,
                    }
                    for b in sorted(finished, key=lambda x: x.get("kickoff_at") or "")
                ]
            ),
            width="stretch",
            hide_index=True,
        )

    if pending:
        st.subheader("Open bets")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "match": f"{b['home_team']} vs {b['away_team']}",
                        "kickoff": b.get("kickoff_at"),
                        "predicted": f"{b['predicted_home_score']}-{b['predicted_away_score']} ({b['predicted_winner']})",
                        "cards": f"{b['predicted_yellow_cards']}Y/{b['predicted_red_cards']}R",
                        "fav player": b.get("favourite_player", ""),
                    }
                    for b in sorted(pending, key=lambda x: x.get("kickoff_at") or "")
                ]
            ),
            width="stretch",
            hide_index=True,
        )


with tab_controls:
    schedule = load_json(settings.schedule_path, {})
    if schedule.get("matches"):
        st.subheader("Upcoming schedule")
        st.caption(f"Last synced: {schedule.get('updated_at', '?')}")
        future = [
            m for m in schedule["matches"] if m.get("kickoff_at")
        ]
        if future:
            sdf = pd.DataFrame(future)
            st.dataframe(sdf, width="stretch", hide_index=True)
            kickoffs = sorted(m["kickoff_at"] for m in future)
            try:
                earliest = datetime.fromisoformat(kickoffs[0].replace("Z", "+00:00"))
                if earliest > datetime.now(timezone.utc):
                    refresh_at = earliest.astimezone().strftime("%H:%M")
                    st.caption(
                        f"Scheduler will refresh all bets ~50 min before the earliest "
                        f"kickoff ({refresh_at} local − 50 min)."
                    )
            except ValueError:
                pass

    st.subheader("Manual runs")
    pid = run_in_progress()
    if pid:
        st.info(f"Run in progress (pid {pid}) — log below updates live.")

    c1, c2, c3 = st.columns(3)
    if c1.button(
        "Settle + update playbook + bet",
        help="Full daily loop: settle finished bets, reflect, evolve playbook, place next 3 bets",
        disabled=bool(pid),
        width="stretch",
    ):
        launch_run("run-daily-loop")
        st.rerun()
    if c2.button(
        "Refresh bets now (prebet)",
        help="Fresh intel for all upcoming bets and re-place them",
        disabled=bool(pid),
        width="stretch",
    ):
        launch_run("prebet")
        st.rerun()
    if c3.button(
        "Reflect only",
        help="Settle + reflect + evolve playbook, no new bets",
        disabled=bool(pid),
        width="stretch",
    ):
        launch_run("reflect-only")
        st.rerun()

    st.subheader("Live run log")

    @st.fragment(run_every="2s")
    def _log_tail() -> None:
        if settings.live_log_path.exists():
            text = settings.live_log_path.read_text(encoding="utf-8")
            lines = text.splitlines()
            st.code("\n".join(lines[-40:]) or "(empty)", language=None)
        else:
            st.code("(no runs yet)", language=None)
        if run_in_progress() is None and LOCK_PATH.exists():
            LOCK_PATH.unlink(missing_ok=True)

    _log_tail()

    st.subheader("Recent run logs")
    run_logs = sorted(settings.logs_dir.glob("run_*.json"), reverse=True)[:5]
    for path in run_logs:
        data = load_json(path, {})
        label = f"{path.name} — {data.get('mode', '?')}"
        with st.expander(label):
            usage = data.get("model_usage")
            if usage:
                st.caption(f"Model usage: {usage}")
            st.json(data, expanded=False)
