"""Daily agent loop: settle → reflect (with Brier) → evolve → research → bet."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.agents.gemini import ModelRouter
from src.config import ROOT, Settings
from src.intel.summarize import summarize_finished_matches, summarize_upcoming_matches
from src.intel.tavily import PRE_MATCH_TTL_SEC, TavilySearch
from src.loop.knockout import (
    KNOCKOUT_BETTING_RULES,
    PREDICT_KNOCKOUT_INSTRUCTIONS,
    REFLECT_CRITICAL_INSTRUCTIONS,
)
from src.mcp.client import McpClient
from src.loop import settled
from src.metrics.brier import append_metrics, compute_brier, rolling_brier
from src.loop.prebet_gate import mark_prebet_done, prebet_window_status
from src.playbook import store as playbook_store

SYSTEM_PROMPT = """You are a Cup Clash prediction agent specializing in **knockout-phase**
World Cup matches. You analyze results critically, maintain a knockout playbook, and place
in-app play-money predictions. Return ONLY valid JSON when asked — no markdown fences, no extra prose."""


def run_reflect_only(settings: Settings, *, force_evolve: bool = False) -> dict[str, Any]:
    """Settle → research → summarize → reflect (+Brier) → evolve. No new bets."""
    mcp, router, tavily = _clients(settings)
    playbook = playbook_store.read_playbook(settings.playbook_path)
    run_log: dict[str, Any] = {
        "mode": "reflect-only",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": [],
    }

    fixed = fix_knockout_bets(settings, mcp, router, tavily)
    if fixed:
        run_log["phases"].append({"phase": "fix_knockout_bets", "fixes": fixed})

    finished = _settle_phase(mcp, settings, run_log)
    if not finished:
        run_log["reflection"] = None
        run_log["model_usage"] = router.usage_summary()
        _finish_run(settings, run_log)
        return run_log

    raw_intel = _research_phase(tavily, finished, run_log)
    intel = _summarize_finished_phase(router, finished, raw_intel, run_log)
    scheduled = _scheduled_knockout_violations(mcp, settings)
    reflection, playbook = _reflect_phase(
        router, playbook, settings, finished, intel, scheduled, run_log
    )
    _evolve_phase(router, playbook, settings, reflection, intel, run_log, force=force_evolve)
    settled.mark(settings.settled_path, finished)
    run_log["model_usage"] = router.usage_summary()
    _finish_run(settings, run_log)
    print("\n==> Reflect-only complete.")
    return run_log


def run_daily_loop(settings: Settings) -> dict[str, Any]:
    mcp, router, tavily = _clients(settings)
    playbook = playbook_store.read_playbook(settings.playbook_path)
    run_log: dict[str, Any] = {
        "mode": "daily-loop",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": [],
    }

    fixed = fix_knockout_bets(settings, mcp, router, tavily)
    if fixed:
        run_log["phases"].append({"phase": "fix_knockout_bets", "fixes": fixed})

    finished = _settle_phase(mcp, settings, run_log)
    if finished:
        raw_intel = _research_phase(tavily, finished, run_log)
        intel = _summarize_finished_phase(router, finished, raw_intel, run_log)
        scheduled = _scheduled_knockout_violations(mcp, settings)
        reflection, playbook = _reflect_phase(
            router, playbook, settings, finished, intel, scheduled, run_log
        )
        playbook = _evolve_phase(router, playbook, settings, reflection, intel, run_log)
        settled.mark(settings.settled_path, finished)

    _scan_and_bet_phase(mcp, router, tavily, settings, playbook, run_log)
    run_log["model_usage"] = router.usage_summary()
    _finish_run(settings, run_log)
    print("\n==> Daily loop complete.")
    return run_log


def fix_knockout_bets(
    settings: Settings,
    mcp: McpClient,
    router: ModelRouter,
    tavily: TavilySearch,
) -> list[dict[str, Any]]:
    """Fix scheduled knockout bets that illegally picked draw as winner."""
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=50)
    stage_by_id = {m["match_id"]: m.get("stage", "") for m in upcoming}
    bets = mcp.get_my_bets(settings.group_id, include_finished=False)
    fixes: list[dict[str, Any]] = []

    for bet in bets:
        if bet.get("predicted_winner") != "draw":
            continue
        if stage_by_id.get(bet["match_id"]) != "knockout":
            continue

        print(
            f"\n==> FIX: {bet['home_team']} vs {bet['away_team']} — "
            f"invalid knockout draw pick ({bet['predicted_home_score']}-"
            f"{bet['predicted_away_score']})"
        )
        hits = tavily.search_match(
            bet["home_team"],
            bet["away_team"],
            context="knockout preview odds who wins extra time penalties",
        )
        fix_prompt = f"""
{KNOCKOUT_BETTING_RULES}

This knockout bet incorrectly picked winner=draw. Fix it.

Current bet:
{json.dumps(bet, indent=2)}

Web intel:
{tavily.format_hits(hits)}

Keep the 90-minute score if it represents a level game going to ET/pens, but pick home or away
as the tie winner. Return JSON:
{{
  "reasoning": "why this winner and 90-min score",
  "winner": "home|away",
  "predicted_home_score": 0,
  "predicted_away_score": 0,
  "predicted_yellow_cards": {bet['predicted_yellow_cards']},
  "predicted_red_cards": {bet['predicted_red_cards']},
  "favourite_player": "{bet.get('favourite_player', '')}"
}}
"""
        corrected = router.act_json(fix_prompt, system=SYSTEM_PROMPT, phase="fix_bet")
        if corrected.get("winner") == "draw":
            corrected["winner"] = "home"

        result = mcp.place_bet(
            group_id=settings.group_id,
            match_id=bet["match_id"],
            winner=corrected["winner"],
            predicted_home_score=corrected["predicted_home_score"],
            predicted_away_score=corrected["predicted_away_score"],
            predicted_yellow_cards=corrected["predicted_yellow_cards"],
            predicted_red_cards=corrected["predicted_red_cards"],
            favourite_player=corrected.get("favourite_player", ""),
        )
        fixes.append(
            {
                "match": f"{bet['home_team']} vs {bet['away_team']}",
                "before": bet,
                "after": corrected,
                "mcp_result": result,
            }
        )
        print(
            f"    corrected → {corrected['predicted_home_score']}-"
            f"{corrected['predicted_away_score']} ({corrected['winner']})"
        )
    return fixes


def run_prebet_refresh(settings: Settings) -> dict[str, Any]:
    """Refresh intel and re-place bets for ALL upcoming matches we already bet on.

    Runs ~50 min before the earliest kickoff (scheduler) or on demand (CLI/dashboard).
    The morning's provisional bets stay in place if anything here fails.
    """
    mcp, router, tavily = _clients(settings)
    playbook = playbook_store.read_playbook(settings.playbook_path)
    run_log: dict[str, Any] = {
        "mode": "prebet-refresh",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": [],
    }

    print("\n==> PREBET: refreshing all upcoming bets with latest intel")
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    _write_schedule(settings, upcoming)
    targets = [m for m in upcoming if m.get("my_bet")]
    if not targets:
        # Fallback: morning run didn't happen — bet on the next batch without existing bets.
        targets = [m for m in upcoming if not m.get("my_bet")][: settings.bet_batch_size]
    run_log["phases"].append({"phase": "scan", "targets": targets})

    if not targets:
        print("    No upcoming matches to refresh.")
    else:
        for match in targets:
            print(f"    • {match['home_team']} vs {match['away_team']} @ {match['kickoff_at']}")
        _research_predict_place(
            mcp, router, tavily, settings, playbook, targets, run_log, fresh_intel=True
        )

    run_log["model_usage"] = router.usage_summary()
    _finish_run(settings, run_log)
    if targets:
        earliest = min(
            (m.get("kickoff_at") for m in targets if m.get("kickoff_at")),
            default=None,
        )
        if earliest:
            mark_prebet_done(settings, earliest)
    print("\n==> Prebet refresh complete.")
    return run_log


def run_maybe_prebet(settings: Settings) -> dict[str, Any]:
    """Run prebet only if inside the T-50 window and not already done for this kickoff."""
    status = prebet_window_status(settings)
    print(f"Prebet gate: {status}")
    if not status.get("in_window"):
        return {"mode": "maybe-prebet", "skipped": True, "status": status}
    return run_prebet_refresh(settings)


def run_place_bets_only(settings: Settings) -> dict[str, Any]:
    """Resume from phase 5: scan → research (cached if available) → summarize → bet.

    Skips settle / reflect / evolve — use when the morning daily loop updated the
    playbook but failed during upcoming-match intel or placement.
    """
    mcp, router, tavily = _clients(settings)
    playbook = playbook_store.read_playbook(settings.playbook_path)
    run_log: dict[str, Any] = {
        "mode": "place-bets",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": [],
    }

    print("\n==> PLACE-BETS: resuming from scan (no reflection, no playbook update)")
    _scan_and_bet_phase(mcp, router, tavily, settings, playbook, run_log)
    run_log["model_usage"] = router.usage_summary()
    _finish_run(settings, run_log)
    print("\n==> Place-bets complete.")
    return run_log


def _clients(settings: Settings) -> tuple[McpClient, ModelRouter, TavilySearch]:
    return (
        McpClient(settings.mcp_url, settings.mcp_token),
        ModelRouter.from_settings(settings),
        TavilySearch(settings.tavily_api_key, cache_path=settings.intel_cache_path),
    )


def _settle_phase(
    mcp: McpClient, settings: Settings, run_log: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return only finished bets that haven't been reflected on in a previous run."""
    print("\n==> Phase 1: SETTLE — checking bet results")
    all_bets = mcp.get_my_bets(settings.group_id, include_finished=True)
    already_processed = settled.load(settings.settled_path)
    all_finished = [b for b in all_bets if b.get("status") == "finished"]
    finished = [b for b in all_finished if b["match_id"] not in already_processed]
    pending = [b for b in all_bets if b.get("status") != "finished"]
    run_log["phases"].append(
        {
            "phase": "settle",
            "finished_total": len(all_finished),
            "finished_new": len(finished),
            "pending_count": len(pending),
            "finished": finished,
        }
    )
    print(
        f"    {len(all_finished)} finished total, {len(finished)} new to process "
        f"({len(all_finished) - len(finished)} already reflected on), "
        f"{len(pending)} still pending"
    )
    for bet in finished:
        print(
            f"    • {bet['home_team']} vs {bet['away_team']}: "
            f"pred {bet['predicted_home_score']}-{bet['predicted_away_score']} "
            f"({bet['predicted_winner']}), cards {bet['predicted_yellow_cards']}Y/"
            f"{bet['predicted_red_cards']}R → actual {bet.get('actual_score', '?')} "
            f"→ {bet.get('points_awarded', 0)} pts"
        )
    return finished


def _scheduled_knockout_violations(
    mcp: McpClient, settings: Settings
) -> list[dict[str, Any]]:
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=50)
    stage_by_id = {m["match_id"]: m.get("stage", "") for m in upcoming}
    scheduled = mcp.get_my_bets(settings.group_id, include_finished=False)
    return [
        b
        for b in scheduled
        if b.get("predicted_winner") == "draw"
        and stage_by_id.get(b["match_id"]) == "knockout"
    ]


def _research_phase(
    tavily: TavilySearch,
    finished: list[dict[str, Any]],
    run_log: dict[str, Any],
) -> dict[str, dict[str, str]]:
    """Gather recap + discipline + player-ratings intel per finished match (raw, no LLM).

    Mirrors the 3-category structure used for pre-match research (preview/lineups/odds)
    instead of one generic recap search — the dedicated player-ratings search in particular
    targets our recurring standout-player misses.
    """
    print("\n==> Phase 2: RESEARCH — Tavily recap + cards + player-ratings (raw, no LLM)")
    raw_intel: dict[str, dict[str, str]] = {}
    for bet in finished:
        raw_intel[bet["match_id"]] = tavily.gather_post_match_intel(
            bet["home_team"], bet["away_team"], match_id=bet["match_id"]
        )
        print(
            f"    searched: {bet['home_team']} vs {bet['away_team']} "
            f"(recap + cards + player-ratings)"
        )
    run_log["phases"].append({"phase": "research", "match_count": len(finished)})
    return raw_intel


def _summarize_finished_phase(
    router: ModelRouter,
    finished: list[dict[str, Any]],
    raw_intel: dict[str, dict[str, str]],
    run_log: dict[str, Any],
) -> dict[str, Any]:
    print("\n==> Phase 2b: SUMMARIZE — structured intel (summarize model)")
    intel = summarize_finished_matches(router, finished, raw_intel)
    run_log["phases"].append({"phase": "summarize_finished", "intel": intel})
    for row in intel.get("matches") or []:
        print(
            f"    • {row.get('match')}: {row.get('actual_score_90min')} "
            f"{row.get('actual_yellow')}Y/{row.get('actual_red')}R "
            f"winner={row.get('actual_winner')} standout={row.get('standout_player')} "
            f"({row.get('standout_player_source')})"
        )
    return intel


def _compute_brier_scores(
    settings: Settings,
    finished: list[dict[str, Any]],
    intel: dict[str, Any],
) -> list[dict[str, Any]]:
    """Look up locally-stored probability estimates and score them against actuals.

    Historical bets placed before probability tracking was added will have no
    stored estimate and are reported as such rather than silently skipped.
    """
    intel_by_id = {m.get("match_id"): m for m in (intel.get("matches") or []) if m.get("match_id")}
    intel_by_name = {m.get("match"): m for m in (intel.get("matches") or [])}
    results: list[dict[str, Any]] = []

    for bet in finished:
        match_id = bet["match_id"]
        match_name = f"{bet['home_team']} vs {bet['away_team']}"
        entry: dict[str, Any] = {"match_id": match_id, "match": match_name}

        stored = predictions_store.get_prediction(settings.predictions_path, match_id)
        if not stored or not stored.get("probs"):
            entry.update(
                brier_score=None,
                reason="no stored probability estimate (bet predates Brier tracking)",
            )
            results.append(entry)
            continue

        summarized = intel_by_id.get(match_id) or intel_by_name.get(match_name) or {}
        actual_outcome = summarized.get("actual_winner")
        if actual_outcome not in ("home", "draw", "away"):
            entry.update(
                probs=stored["probs"], brier_score=None, reason="actual outcome unknown"
            )
            results.append(entry)
            continue

        score = compute_brier(stored["probs"], actual_outcome)
        entry.update(
            probs=stored["probs"],
            actual_outcome=actual_outcome,
            brier_score=round(score, 4),
            points_awarded=bet.get("points_awarded"),
        )
        results.append(entry)
    return results


def _reflect_phase(
    router: ModelRouter,
    playbook: str,
    settings: Settings,
    finished: list[dict[str, Any]],
    intel: dict[str, Any],
    scheduled_violations: list[dict[str, Any]],
    run_log: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    print("\n==> Phase 3: REFLECT — critical analysis + Brier calibration (analyze model)")

    brier_rows = _compute_brier_scores(settings, finished, intel)
    scored_now = [r for r in brier_rows if r.get("brier_score") is not None]
    if scored_now:
        history = append_metrics(
            settings.metrics_path,
            [
                {
                    "match_id": r["match_id"],
                    "match": r["match"],
                    "brier_score": r["brier_score"],
                    "points_awarded": r.get("points_awarded"),
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
                for r in scored_now
            ],
        )
    else:
        history = append_metrics(settings.metrics_path, [])
    rolling = rolling_brier(history, n=5)

    print("    Brier scores (0=perfect, 2=worst):")
    for r in brier_rows:
        if r.get("brier_score") is not None:
            print(f"      {r['match']}: {r['brier_score']}")
        else:
            print(f"      {r['match']}: n/a ({r.get('reason')})")
    print(f"    rolling Brier (last 5): {rolling}")

    violation_note = ""
    if scheduled_violations:
        violation_note = f"""
Rule violations in scheduled knockout bets:
{json.dumps(scheduled_violations, indent=2)}
"""

    reflect_prompt = f"""
{KNOCKOUT_BETTING_RULES}
{REFLECT_CRITICAL_INSTRUCTIONS}

Current knockout playbook:
{playbook}

Our finished bets (JSON):
{json.dumps(finished, indent=2)}

Summarized match intel (includes extracted actual cards + winner):
{json.dumps(intel, indent=2)}

Brier calibration scores computed for this run (authoritative, do not recompute —
just comment on them). Lower is better calibrated (0=perfect, 2=worst). "n/a" means
we have no stored probability estimate for that bet (predates calibration tracking):
{json.dumps(brier_rows, indent=2)}
Rolling Brier (last 5 scored matches): {rolling}

{violation_note}

Analyze every dimension: winner, exact 90-min score, cards, favourite player, calibration
(Brier), points left on table.
Return JSON:
{{
  "summary": "critical 2-3 sentence assessment — highlight misses and calibration, not just wins",
  "per_match": [
    {{
      "match": "Home vs Away",
      "what_went_well": ["..."],
      "what_went_poorly": ["..."],
      "points_left_on_table": "what exact score/cards/fav player cost us",
      "cards": {{
        "predicted_yellow": 0,
        "predicted_red": 0,
        "actual_yellow": 0,
        "actual_red": 0,
        "card_assessment": "how close were we on bookings"
      }},
      "calibration_note": "comment on this match's Brier score if available, else say n/a",
      "lesson": "one actionable knockout-specific lesson"
    }}
  ],
  "card_trends": ["patterns e.g. over-counting yellows, missing reds"],
  "calibration_trend": "is rolling Brier improving, worsening, or too little data",
  "knockout_rule_violations": ["any draw picks or 90-min score mistakes"],
  "should_update_playbook": true,
  "update_rationale": "specific gaps to fix in the knockout playbook"
}}
"""
    reflection = router.analyze_json(reflect_prompt, system=SYSTEM_PROMPT, phase="reflect")
    reflection["brier_scores"] = brier_rows
    reflection["rolling_brier"] = rolling
    run_log["reflection"] = reflection
    print(f"    summary: {reflection.get('summary', '')[:140]}...")
    for row in reflection.get("per_match") or []:
        cards = row.get("cards") or {}
        if cards:
            print(
                f"    cards {row.get('match')}: "
                f"pred {cards.get('predicted_yellow')}Y/{cards.get('predicted_red')}R → "
                f"actual {cards.get('actual_yellow')}Y/{cards.get('actual_red')}R"
            )
    print(f"    update playbook? {reflection.get('should_update_playbook')}")
    return reflection, playbook


def _evolve_phase(
    router: ModelRouter,
    playbook: str,
    settings: Settings,
    reflection: dict[str, Any],
    intel: dict[str, Any],
    run_log: dict[str, Any],
    *,
    force: bool = False,
) -> str:
    should = reflection.get("should_update_playbook") or force
    if not should:
        print("\n==> Phase 4: EVOLVE — skipped")
        run_log["phases"].append({"phase": "evolve", "skipped": True})
        return playbook

    print("\n==> Phase 4: EVOLVE — rewriting playbook (analyze model)")
    version = playbook_store.current_version(playbook)
    evolve_prompt = f"""
{KNOCKOUT_BETTING_RULES}

Current knockout playbook (v{version}):
{playbook}

Reflection (includes Brier calibration scores and rolling_brier):
{json.dumps(reflection, indent=2)}

Summarized intel:
{json.dumps(intel, indent=2)}

Rewrite to v{version + 1} for knockout phase only. Fold in card trends, score misses,
no-draw rule, and calibration_trend if it points to over/under-confidence. Keep sections:
Principles, Knockout rules, Heuristics, Watch-outs, Open questions, Changelog.
Under ~450 words.

Return JSON:
{{
  "change_summary": "one line describing the most important change",
  "new_playbook_markdown": "full markdown starting with # Agent — Playbook v{{N}} (Knockout phase)"
}}
"""
    evolved = router.analyze_json(evolve_prompt, system=SYSTEM_PROMPT, phase="evolve")
    new_content = playbook_store.bump_version(evolved["new_playbook_markdown"], version + 1)
    playbook_store.write_playbook(settings.playbook_path, new_content)
    commit_msg = f"Playbook v{version + 1}: {evolved.get('change_summary', 'knockout update')}"
    commit_out = playbook_store.commit_playbook(ROOT, commit_msg)
    run_log["phases"].append(
        {
            "phase": "evolve",
            "from_version": version,
            "to_version": version + 1,
            "change_summary": evolved.get("change_summary"),
            "commit": commit_out,
        }
    )
    print(f"    {commit_out}")
    return new_content


def _scan_and_bet_phase(
    mcp: McpClient,
    router: ModelRouter,
    tavily: TavilySearch,
    settings: Settings,
    playbook: str,
    run_log: dict[str, Any],
) -> None:
    print(f"\n==> Phase 5: SCAN — fetch next {settings.bet_batch_size} upcoming matches")
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    _write_schedule(settings, upcoming)
    targets = [m for m in upcoming if not m.get("my_bet")][: settings.bet_batch_size]
    run_log["phases"].append({"phase": "scan", "targets": targets})
    for match in targets:
        print(f"    • {match['home_team']} vs {match['away_team']} @ {match['kickoff_at']}")

    if not targets:
        print("    No open matches to bet on.")
        return

    _research_predict_place(mcp, router, tavily, settings, playbook, targets, run_log)


def _write_schedule(settings: Settings, upcoming: list[dict[str, Any]]) -> None:
    """Persist upcoming kickoffs (+ my_bet status) so the scheduler and dashboard
    can compute the single refresh time (earliest kickoff − 50 min) without MCP."""
    entries = [
        {
            "match_id": m["match_id"],
            "match": f"{m['home_team']} vs {m['away_team']}",
            "kickoff_at": m.get("kickoff_at"),
            "stage": m.get("stage"),
            "has_bet": bool(m.get("my_bet")),
        }
        for m in upcoming
    ]
    settings.schedule_path.parent.mkdir(parents=True, exist_ok=True)
    settings.schedule_path.write_text(
        json.dumps(
            {"updated_at": datetime.now(timezone.utc).isoformat(), "matches": entries},
            indent=2,
        ),
        encoding="utf-8",
    )


def _research_predict_place(
    mcp: McpClient,
    router: ModelRouter,
    tavily: TavilySearch,
    settings: Settings,
    playbook: str,
    targets: list[dict[str, Any]],
    run_log: dict[str, Any],
    *,
    fresh_intel: bool = False,
) -> None:
    print("\n==> Phase 6: RESEARCH — Tavily preview + lineups + odds (raw, no LLM)")
    raw_intel: dict[str, dict[str, str]] = {}
    for match in targets:
        cache_key = f"{match['match_id']}:pre"
        was_cached = (
            not fresh_intel
            and tavily.cache is not None
            and tavily.cache.get(cache_key, PRE_MATCH_TTL_SEC) is not None
        )
        bundle = tavily.gather_pre_match_intel(
            match["home_team"],
            match["away_team"],
            match_id=match["match_id"],
            force_refresh=fresh_intel,
        )
        raw_intel[match["match_id"]] = bundle
        tag = " (cached)" if was_cached else ""
        print(
            f"    gathered: {match['home_team']} vs {match['away_team']} "
            f"(preview+lineups+odds){tag}"
        )

    print("\n==> Phase 6b: SUMMARIZE upcoming intel (summarize model)")
    intel = summarize_upcoming_matches(router, targets, raw_intel)
    run_log["phases"].append({"phase": "summarize_upcoming", "intel": intel})
    for row in intel.get("matches") or []:
        print(
            f"    • {row.get('match')}: {row.get('market_view', '')[:70]} "
            f"[P(H/D/A)={row.get('prob_home')}/{row.get('prob_draw')}/{row.get('prob_away')}]"
        )

    print("\n==> Phase 7: PREDICT + PLACE — batched (act model)")
    knockout = all(m.get("stage") == "knockout" for m in targets)
    winner_note = (
        "winner must be home or away for each knockout match (never draw)"
        if knockout
        else "winner may be home, draw, or away"
    )
    predict_prompt = f"""
{KNOCKOUT_BETTING_RULES if knockout else ""}
{PREDICT_KNOCKOUT_INSTRUCTIONS if knockout else ""}

Playbook:
{playbook}

Summarized intel for upcoming matches (includes market odds, lineups, and a starting
prob_home/prob_draw/prob_away estimate you may refine):
{json.dumps(intel, indent=2)}

Targets (JSON):
{json.dumps(targets, indent=2)}

Produce one prediction per match. {winner_note}. Aim close to real outcomes on every field.
Report your HONEST calibrated probabilities (prob_home/prob_draw/prob_away, sum to 1) for
the 90-minute 1X2 outcome separately from your discrete "winner" pick — the pick may differ
from argmax(prob) if your strategy favours it, but say so in reasoning if it does.

Return JSON:
{{
  "predictions": [
    {{
      "match_id": "uuid",
      "reasoning": "brief rationale, note if pick differs from raw probabilities",
      "prob_home": 0.0,
      "prob_draw": 0.0,
      "prob_away": 0.0,
      "winner": "home|away",
      "predicted_home_score": 0,
      "predicted_away_score": 0,
      "predicted_yellow_cards": 0,
      "predicted_red_cards": 0,
      "favourite_player": "name"
    }}
  ]
}}
"""
    batch = router.act_json(predict_prompt, system=SYSTEM_PROMPT, phase="predict_batch")
    by_id = {p["match_id"]: p for p in batch.get("predictions") or []}
    placed: list[dict[str, Any]] = []

    for match in targets:
        prediction = by_id.get(match["match_id"])
        if not prediction:
            print(f"    skip: no prediction for {match['home_team']} vs {match['away_team']}")
            continue
        if knockout and prediction.get("winner") == "draw":
            prediction["winner"] = "home"

        probs = _normalized_probs(prediction)
        predictions_store.save_prediction(
            settings.predictions_path,
            match["match_id"],
            {
                "match": f"{match['home_team']} vs {match['away_team']}",
                "probs": probs,
                "pick": prediction["winner"],
                "predicted_home_score": prediction["predicted_home_score"],
                "predicted_away_score": prediction["predicted_away_score"],
                "reasoning": prediction.get("reasoning", ""),
                "playbook_version": playbook_store.current_version(playbook),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        result = mcp.place_bet(
            group_id=settings.group_id,
            match_id=match["match_id"],
            winner=prediction["winner"],
            predicted_home_score=prediction["predicted_home_score"],
            predicted_away_score=prediction["predicted_away_score"],
            predicted_yellow_cards=prediction["predicted_yellow_cards"],
            predicted_red_cards=prediction["predicted_red_cards"],
            favourite_player=prediction.get("favourite_player", ""),
        )
        placed.append(
            {
                "match": f"{match['home_team']} vs {match['away_team']}",
                "prediction": prediction,
                "probs": probs,
                "mcp_result": result,
            }
        )
        print(
            f"    placed: {match['home_team']} vs {match['away_team']} → "
            f"{prediction['predicted_home_score']}-{prediction['predicted_away_score']} "
            f"({prediction['winner']}) Y{prediction['predicted_yellow_cards']}/"
            f"R{prediction['predicted_red_cards']} "
            f"P(H/D/A)={probs['home']}/{probs['draw']}/{probs['away']}"
        )
    run_log["phases"].append({"phase": "place", "bets": placed})


def _normalized_probs(prediction: dict[str, Any]) -> dict[str, float]:
    raw = {
        "home": float(prediction.get("prob_home", 0.0) or 0.0),
        "draw": float(prediction.get("prob_draw", 0.0) or 0.0),
        "away": float(prediction.get("prob_away", 0.0) or 0.0),
    }
    total = sum(raw.values())
    if total <= 0:
        return {"home": 1 / 3, "draw": 1 / 3, "away": 1 / 3}
    return {k: round(v / total, 4) for k, v in raw.items()}


def _finish_run(settings: Settings, run_log: dict[str, Any]) -> None:
    run_log["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write_run_log(settings, run_log)
    usage = run_log.get("model_usage")
    if usage:
        print(f"Model usage this run: {usage}")


def _write_run_log(settings: Settings, run_log: dict[str, Any]) -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = settings.logs_dir / f"run_{ts}.json"
    path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    print(f"\nRun log: {path}")
