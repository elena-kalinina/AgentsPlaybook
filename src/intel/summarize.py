"""Batched Gemini summarization of raw Tavily/MCP intel."""

from __future__ import annotations

import json
from typing import Any

from src.agents.gemini import ModelRouter


def summarize_finished_matches(
    router: ModelRouter,
    finished_bets: list[dict[str, Any]],
    raw_intel_by_match: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Summarize recap/discipline/player-ratings intel gathered AFTER a match finishes.

    MCP currently returns actual_score + points_awarded only — not cards or scorers.
    Prefer MCP score when present; extract cards/scorers carefully from research.
    """
    bundle = [
        {
            "match_id": b["match_id"],
            "home_team": b["home_team"],
            "away_team": b["away_team"],
            "kickoff_at": b.get("kickoff_at"),
            "mcp_actual_score": b.get("actual_score"),
            "mcp_points_awarded": b.get("points_awarded"),
            "our_predicted_winner": b.get("predicted_winner"),
            "our_predicted_score": (
                f"{b.get('predicted_home_score')}-{b.get('predicted_away_score')}"
            ),
            "our_predicted_yellow": b.get("predicted_yellow_cards"),
            "our_predicted_red": b.get("predicted_red_cards"),
            "our_favourite_player": b.get("favourite_player"),
            "raw_recap": raw_intel_by_match.get(b["match_id"], {}).get("recap", ""),
            "raw_cards": raw_intel_by_match.get(b["match_id"], {}).get("cards", ""),
            "raw_player_ratings": raw_intel_by_match.get(b["match_id"], {}).get(
                "player_ratings", ""
            ),
        }
        for b in finished_bets
    ]
    prompt = f"""
Extract structured facts for each finished World Cup knockout match.

AUTHORITATIVE from Cup Clash MCP (trust these over web text when present):
- mcp_actual_score — use for actual_score_90min and actual_winner (home/draw/away from that score).
- mcp_points_awarded — Cup Clash scoring: winner 3, exact score 5, favourite player/goalscorer 2,
  exact yellows 2, yellows ±1 → 1, exact reds 1. Use this as a sanity check on cards/scorer.

NOT available from MCP today — extract from research only:
- yellow/red card TOTALS
- who scored (goalscorers) — this is what Cup Clash "favourite_player" is scored against

Matches (JSON):
{json.dumps(bundle, indent=2)}

Rules (critical — we have been burned by bad web summaries):
1. Prefer SOURCE SNIPPETS over any "Tavily summary" line. Tavily summaries often invent
   "0 yellow cards" or mix in a different Argentina/England match from earlier rounds.
2. Ignore research about the wrong fixture (wrong date, Round of 32 when this is a semi, etc.).
3. actual_yellow / actual_red: ONLY set an integer if a source gives a clear TOTAL or a
   named booking list you can count. If unknown, use null — NEVER invent 0.
4. If mcp_points_awarded is inconsistent with your card/scorer guesses (e.g. points look like
   exact-yellow+exact-red hits while you claim 0 yellows), prefer null cards and note the conflict.
5. key_scorers: list players who actually scored in THIS match (from recap/stats). Empty if unknown.
6. favourite_player_actual: best guess of who Cup Clash would credit for the 2-pt favourite-player
   field — prefer a goalscorer from key_scorers, not "man of the match" alone. null if unknown.
7. standout_player: MOTM / top-rated if clearly stated; may differ from favourite_player_actual.
8. Copy match_id exactly.

Return JSON:
{{
  "matches": [
    {{
      "match_id": "uuid copied exactly",
      "match": "Home vs Away",
      "actual_score_90min": "H-A from mcp_actual_score when present",
      "actual_yellow": null,
      "actual_red": null,
      "actual_winner": "home|draw|away",
      "key_scorers": ["..."],
      "favourite_player_actual": "goalscorer used for Cup Clash fav-player scoring, or null",
      "standout_player": "MOTM/top-rated if known, else null",
      "standout_player_source": "man_of_the_match|top_rated|scorer|unknown",
      "card_notes": "evidence for card totals, or why null",
      "confidence_notes": "any conflicts between MCP points and web intel",
      "recap": "2-3 sentence factual summary of THIS match only"
    }}
  ]
}}
"""
    return router.summarize_json(prompt, phase="summarize_finished")


def summarize_upcoming_matches(
    router: ModelRouter,
    matches: list[dict[str, Any]],
    raw_intel_by_match: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Summarize preview/lineup/odds intel gathered BEFORE placing a bet.

    raw_intel_by_match: match_id -> {"preview": ..., "lineups": ..., "odds": ...}
    """
    bundle = [
        {
            "match_id": m["match_id"],
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "kickoff_at": m.get("kickoff_at"),
            "stage": m.get("stage"),
            "raw_preview": raw_intel_by_match.get(m["match_id"], {}).get("preview", ""),
            "raw_lineups": raw_intel_by_match.get(m["match_id"], {}).get("lineups", ""),
            "raw_odds": raw_intel_by_match.get(m["match_id"], {}).get("odds", ""),
        }
        for m in matches
    ]
    prompt = f"""
Compress raw web intel (preview, lineups/team news, odds) into concise, prediction-ready
facts for each upcoming knockout match. This is gathered BEFORE the bet is placed.

Matches (JSON):
{json.dumps(bundle, indent=2)}

For each match extract:
- market odds / implied win probabilities if mentioned (de-vig mentally if you can)
- confirmed/likely lineups, key absences (injuries, suspensions)
- form and any tactical/style notes relevant to cards or scoring
- an honest 1X2 probability estimate (prob_home/prob_draw/prob_away, sum to 1) based on
  everything above — "draw" here means the 90-minute regulation outcome, even though the
  final bet cannot pick draw as a knockout winner.
- Prefer source snippets over any Tavily summary line; ignore wrong fixtures / wrong dates.

Return JSON:
{{
  "matches": [
    {{
      "match_id": "uuid",
      "match": "Home vs Away",
      "market_view": "who is favoured and by how much (odds if found)",
      "lineup_notes": "confirmed/likely XI, key absences",
      "form_notes": "recent results and injuries",
      "style_notes": "expected tempo, physicality, card risk",
      "prob_home": 0.0,
      "prob_draw": 0.0,
      "prob_away": 0.0,
      "intel_summary": "3-4 sentences max"
    }}
  ]
}}
"""
    return router.summarize_json(prompt, phase="summarize_upcoming")
