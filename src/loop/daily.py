"""Daily agent loop: settle → reflect → evolve → bet."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agents.gemini import GeminiClient
from src.config import ROOT, Settings
from src.intel.tavily import TavilySearch
from src.mcp.client import McpClient
from src.playbook import store as playbook_store

SYSTEM_PROMPT = """You are a Cup Clash prediction agent. You analyze football matches,
learn from results, maintain a strategy playbook, and place in-app play-money predictions.
Return ONLY valid JSON when asked — no markdown fences, no extra prose."""


def run_daily_loop(settings: Settings) -> dict[str, Any]:
    mcp = McpClient(settings.mcp_url, settings.mcp_token)
    gemini = GeminiClient(
        settings.gemini_api_key,
        settings.gemini_model,
        min_interval_sec=settings.gemini_min_interval_sec,
    )
    tavily = TavilySearch(settings.tavily_api_key)
    playbook = playbook_store.read_playbook(settings.playbook_path)

    run_log: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": [],
    }

    # --- 1. SETTLE: check finished bets and results ---
    print("\n==> Phase 1: SETTLE — checking bet results")
    all_bets = mcp.get_my_bets(settings.group_id, include_finished=True)
    finished = [b for b in all_bets if b.get("status") == "finished"]
    pending = [b for b in all_bets if b.get("status") != "finished"]
    run_log["phases"].append(
        {
            "phase": "settle",
            "finished_count": len(finished),
            "pending_count": len(pending),
            "finished": finished,
        }
    )
    print(f"    {len(finished)} finished, {len(pending)} still pending")
    for bet in finished:
        print(
            f"    • {bet['home_team']} vs {bet['away_team']}: "
            f"pred {bet['predicted_home_score']}-{bet['predicted_away_score']} "
            f"({bet['predicted_winner']}) → actual {bet.get('actual_score', '?')} "
            f"→ {bet.get('points_awarded', 0)} pts"
        )

    if not finished:
        print("    No finished bets to reflect on yet.")
        run_log["reflection"] = None
    else:
        # --- 2. RESEARCH finished matches via Tavily ---
        print("\n==> Phase 2: RESEARCH — Tavily search on finished matches")
        research_blocks: list[str] = []
        for bet in finished:
            hits = tavily.search_match(
                bet["home_team"],
                bet["away_team"],
                context="match result recap analysis",
            )
            block = tavily.format_hits(hits)
            research_blocks.append(
                f"### {bet['home_team']} vs {bet['away_team']}\n{block}"
            )
            print(f"    searched: {bet['home_team']} vs {bet['away_team']} ({len(hits)} hits)")
        research_text = "\n\n".join(research_blocks)

        # --- 3. REFLECT ---
        print("\n==> Phase 3: REFLECT — analyze bets vs results")
        reflect_prompt = f"""
Current playbook:
{playbook}

Finished bets (JSON):
{json.dumps(finished, indent=2)}

Web research on these matches:
{research_text}

Analyze what went well and what did not. Reference specific predictions vs actual scores and points.
Return JSON:
{{
  "summary": "2-3 sentence overall assessment",
  "per_match": [
    {{
      "match": "Home vs Away",
      "what_went_well": ["..."],
      "what_went_poorly": ["..."],
      "lesson": "one actionable lesson"
    }}
  ],
  "should_update_playbook": true,
  "update_rationale": "why or why not to rewrite the playbook now"
}}
"""
        reflection = gemini.generate_json(reflect_prompt, system=SYSTEM_PROMPT, phase="reflect")
        run_log["reflection"] = reflection
        print(f"    summary: {reflection.get('summary', '')[:120]}...")
        print(f"    update playbook? {reflection.get('should_update_playbook')}")

        # --- 4. EVOLVE playbook if warranted ---
        if reflection.get("should_update_playbook"):
            print("\n==> Phase 4: EVOLVE — rewriting playbook")
            version = playbook_store.current_version(playbook)
            evolve_prompt = f"""
Current playbook (v{version}):
{playbook}

Reflection analysis:
{json.dumps(reflection, indent=2)}

Web research:
{research_text}

Rewrite the playbook to v{version + 1}. Fold durable lessons into Heuristics and Watch-outs,
prune anything contradicted by results, keep under ~400 words. Preserve markdown section headings.
Add a Changelog bullet for v{version + 1}.

Return JSON:
{{
  "change_summary": "one line describing the most important change",
  "new_playbook_markdown": "full markdown content starting with # Agent — Playbook v{N}"
}}
"""
            evolved = gemini.generate_json(evolve_prompt, system=SYSTEM_PROMPT, phase="evolve")
            new_content = evolved["new_playbook_markdown"]
            new_content = playbook_store.bump_version(new_content, version + 1)
            playbook_store.write_playbook(settings.playbook_path, new_content)
            playbook = new_content
            commit_msg = f"Playbook v{version + 1}: {evolved.get('change_summary', 'agent update')}"
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
        else:
            print("\n==> Phase 4: EVOLVE — skipped (agent decided no update needed)")
            run_log["phases"].append({"phase": "evolve", "skipped": True})

    # --- 5. SCAN next 3 upcoming matches ---
    print("\n==> Phase 5: SCAN — fetch next 3 upcoming matches")
    upcoming = mcp.list_upcoming_matches(settings.group_id, limit=10)
    targets = [m for m in upcoming if not m.get("my_bet")][:3]
    run_log["phases"].append({"phase": "scan", "targets": targets})
    for match in targets:
        print(f"    • {match['home_team']} vs {match['away_team']} @ {match['kickoff_at']}")

    if not targets:
        print("    No open matches to bet on.")
        _write_run_log(settings, run_log)
        return run_log

    # --- 6. REASON + ACT: place bets using updated playbook ---
    print("\n==> Phase 6: REASON + ACT — place bets")
    placed: list[dict[str, Any]] = []
    for match in targets:
        hits = tavily.search_match(
            match["home_team"],
            match["away_team"],
            context="preview odds form injuries",
        )
        intel = tavily.format_hits(hits)
        predict_prompt = f"""
Playbook:
{playbook}

Upcoming match:
{json.dumps(match, indent=2)}

Web intel:
{intel}

Using the playbook, produce one prediction for this match.
Return JSON:
{{
  "reasoning": "brief rationale referencing playbook heuristics",
  "winner": "home|draw|away",
  "predicted_home_score": 0,
  "predicted_away_score": 0,
  "predicted_yellow_cards": 0,
  "predicted_red_cards": 0,
  "favourite_player": "player name"
}}
"""
        prediction = gemini.generate_json(predict_prompt, system=SYSTEM_PROMPT, phase="predict")
        bet_args = {
            "group_id": settings.group_id,
            "match_id": match["match_id"],
            "winner": prediction["winner"],
            "predicted_home_score": prediction["predicted_home_score"],
            "predicted_away_score": prediction["predicted_away_score"],
            "predicted_yellow_cards": prediction["predicted_yellow_cards"],
            "predicted_red_cards": prediction["predicted_red_cards"],
            "favourite_player": prediction.get("favourite_player", ""),
        }
        result = mcp.place_bet(**bet_args)
        entry = {
            "match": f"{match['home_team']} vs {match['away_team']}",
            "prediction": prediction,
            "mcp_result": result,
        }
        placed.append(entry)
        print(
            f"    placed: {match['home_team']} vs {match['away_team']} → "
            f"{prediction['predicted_home_score']}-{prediction['predicted_away_score']} "
            f"({prediction['winner']})"
        )

    run_log["phases"].append({"phase": "place", "bets": placed})
    run_log["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write_run_log(settings, run_log)
    print("\n==> Daily loop complete.")
    return run_log


def _write_run_log(settings: Settings, run_log: dict[str, Any]) -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = settings.logs_dir / f"run_{ts}.json"
    path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    print(f"\nRun log: {path}")
