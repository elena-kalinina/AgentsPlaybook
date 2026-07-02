"""Tavily web search for match context."""

from __future__ import annotations

from typing import Any

import requests


class TavilySearch:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search_match_recap(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        """Official-style match report: final score, scorers, minute-by-minute, referee decisions."""
        return self.search_match(
            home_team,
            away_team,
            context="full time result match report goal scorers minute by minute referee",
        )

    def search_match_cards(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        return self.search_match(
            home_team,
            away_team,
            context="final yellow cards red cards bookings disciplinary report referee name",
        )

    def search_player_ratings(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        """Targets man-of-the-match / player-ratings pages so 'standout player' is
        grounded in post-match performance data, not just who scored or reputation."""
        return self.search_match(
            home_team,
            away_team,
            context="man of the match player ratings best performer top rated",
        )

    def gather_post_match_intel(self, home_team: str, away_team: str) -> dict[str, str]:
        """Combined bundle of recap, cards/discipline, and player-ratings intel."""
        return {
            "recap": self.format_hits(self.search_match_recap(home_team, away_team)),
            "cards": self.format_hits(self.search_match_cards(home_team, away_team)),
            "player_ratings": self.format_hits(self.search_player_ratings(home_team, away_team)),
        }

    def search_lineups(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        return self.search_match(
            home_team,
            away_team,
            context="predicted starting lineup XI team news injuries suspensions",
        )

    def search_odds(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        return self.search_match(
            home_team,
            away_team,
            context="betting odds moneyline win probability favourite",
        )

    def search_preview(self, home_team: str, away_team: str) -> list[dict[str, Any]]:
        return self.search_match(
            home_team,
            away_team,
            context="knockout preview form who wins extra time penalties",
        )

    def gather_pre_match_intel(self, home_team: str, away_team: str) -> dict[str, str]:
        """One combined bundle of preview, lineup, and odds intel for a match."""
        return {
            "preview": self.format_hits(self.search_preview(home_team, away_team)),
            "lineups": self.format_hits(self.search_lineups(home_team, away_team)),
            "odds": self.format_hits(self.search_odds(home_team, away_team)),
        }

    def search_match(self, home_team: str, away_team: str, *, context: str = "") -> list[dict[str, Any]]:
        query = f"{home_team} vs {away_team} World Cup 2026 {context}".strip()
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        hits: list[dict[str, Any]] = []
        if data.get("answer"):
            hits.append({"title": "Tavily summary", "snippet": data["answer"], "url": ""})
        for item in data.get("results") or []:
            hits.append(
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                }
            )
        return hits

    def format_hits(self, hits: list[dict[str, Any]]) -> str:
        if not hits:
            return "No web results found."
        lines = []
        for hit in hits:
            lines.append(f"- {hit['title']}: {hit['snippet'][:400]}")
            if hit.get("url"):
                lines.append(f"  ({hit['url']})")
        return "\n".join(lines)
