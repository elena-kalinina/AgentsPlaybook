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

    raw_intel_by_match: match_id -> {"recap": ..., "cards": ..., "player_ratings": ...}
    Mirrors the structure of summarize_upcoming_matches so both phases get equally
    targeted research instead of one generic search per category.
    """
    bundle = [
        {
            "match_id": b["match_id"],
            "home_team": b["home_team"],
            "away_team": b["away_team"],
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
Extract structured facts for each finished match from the raw research below.
MCP does NOT return actual card counts or man-of-the-match data — infer them from research.
Each match already has a "match_id" — copy it through exactly so results can be joined reliably
(do not invent or alter it).

Matches with our bets and raw research (JSON):
{json.dumps(bundle, indent=2)}

For "standout_player", prefer the raw_player_ratings research (man of the match / top-rated
performer) over assuming the scorer or a big-name reputation is automatically the standout —
this is where we have repeatedly been wrong (e.g. picking a veteran when a substitute won it).

Return JSON:
{{
  "matches": [
    {{
      "match_id": "uuid copied exactly",
      "match": "Home vs Away",
      "actual_score_90min": "H-A",
      "actual_yellow": 0,
      "actual_red": 0,
      "actual_winner": "home|draw|away",
      "key_scorers": ["..."],
      "standout_player": "grounded in player-ratings research, not assumption",
      "standout_player_source": "man_of_the_match|top_rated|scorer_inference",
      "card_notes": "brief note on bookings, referee if known",
      "recap": "2-3 sentence factual summary"
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
