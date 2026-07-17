"""Tavily web search for match context, with parallel fetches and an on-disk cache."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

import requests

PRE_MATCH_TTL_SEC = 45 * 60  # lineups/odds go stale quickly
POST_MATCH_TTL_SEC = None  # finished-match facts never change (until force_refresh)


class IntelCache:
    """JSON file cache keyed by (match_id, bundle-kind) with per-entry timestamps."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def get(self, key: str, ttl_sec: float | None) -> dict[str, str] | None:
        store = self._load()
        entry = store.get(key)
        if not entry:
            return None
        if ttl_sec is not None and time.time() - entry.get("saved_at", 0) > ttl_sec:
            return None
        return entry.get("data")

    def put(self, key: str, data: dict[str, str]) -> None:
        store = self._load()
        store[key] = {"saved_at": time.time(), "data": data}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(store, indent=2), encoding="utf-8")

    def delete(self, key: str) -> bool:
        store = self._load()
        if key not in store:
            return False
        del store[key]
        self.path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        return True

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}


class TavilySearch:
    def __init__(self, api_key: str, *, cache_path: Path | None = None) -> None:
        self.api_key = api_key
        self.cache = IntelCache(cache_path) if cache_path else None

    def search_match_recap(
        self,
        home_team: str,
        away_team: str,
        *,
        date_hint: str = "",
        stage_hint: str = "",
    ) -> list[dict[str, Any]]:
        """Official-style match report: final score, scorers, minute-by-minute."""
        return self.search_match(
            home_team,
            away_team,
            context=(
                f"{stage_hint} {date_hint} full time result match report "
                f"goal scorers 90 minutes highlights"
            ).strip(),
            include_answer=True,
            search_depth="advanced",
        )

    def search_match_cards(
        self,
        home_team: str,
        away_team: str,
        *,
        date_hint: str = "",
        stage_hint: str = "",
    ) -> list[dict[str, Any]]:
        """Bookings only — do NOT trust Tavily's AI answer (it often invents '0 cards')."""
        return self.search_match(
            home_team,
            away_team,
            context=(
                f"{stage_hint} {date_hint} how many yellow cards red cards "
                f"bookings list disciplinary report statistics"
            ).strip(),
            include_answer=False,
            search_depth="advanced",
            max_results=8,
        )

    def search_player_ratings(
        self,
        home_team: str,
        away_team: str,
        *,
        date_hint: str = "",
        stage_hint: str = "",
    ) -> list[dict[str, Any]]:
        """Man-of-the-match / ratings AND who scored (Cup Clash fav player = goalscorer)."""
        return self.search_match(
            home_team,
            away_team,
            context=(
                f"{stage_hint} {date_hint} goal scorers who scored "
                f"man of the match player ratings"
            ).strip(),
            include_answer=True,
            search_depth="advanced",
        )

    def gather_post_match_intel(
        self,
        home_team: str,
        away_team: str,
        *,
        match_id: str | None = None,
        kickoff_at: str | None = None,
        stage: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, str]:
        """Combined bundle of recap, cards/discipline, and player-ratings intel."""
        date_hint = _date_hint(kickoff_at)
        stage_hint = (stage or "").replace("_", " ").strip()

        def recap(h: str, a: str) -> list[dict[str, Any]]:
            return self.search_match_recap(h, a, date_hint=date_hint, stage_hint=stage_hint)

        def cards(h: str, a: str) -> list[dict[str, Any]]:
            return self.search_match_cards(h, a, date_hint=date_hint, stage_hint=stage_hint)

        def ratings(h: str, a: str) -> list[dict[str, Any]]:
            return self.search_player_ratings(
                h, a, date_hint=date_hint, stage_hint=stage_hint
            )

        return self._gather_bundle(
            {"recap": recap, "cards": cards, "player_ratings": ratings},
            home_team,
            away_team,
            cache_key=f"{match_id}:post" if match_id else None,
            ttl_sec=POST_MATCH_TTL_SEC,
            force_refresh=force_refresh,
        )

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

    def gather_pre_match_intel(
        self,
        home_team: str,
        away_team: str,
        *,
        match_id: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, str]:
        """One combined bundle of preview, lineup, and odds intel for a match."""
        return self._gather_bundle(
            {
                "preview": self.search_preview,
                "lineups": self.search_lineups,
                "odds": self.search_odds,
            },
            home_team,
            away_team,
            cache_key=f"{match_id}:pre" if match_id else None,
            ttl_sec=PRE_MATCH_TTL_SEC,
            force_refresh=force_refresh,
        )

    def _gather_bundle(
        self,
        searches: dict[str, Callable[[str, str], list[dict[str, Any]]]],
        home_team: str,
        away_team: str,
        *,
        cache_key: str | None,
        ttl_sec: float | None,
        force_refresh: bool,
    ) -> dict[str, str]:
        if self.cache and cache_key and not force_refresh:
            cached = self.cache.get(cache_key, ttl_sec)
            if cached:
                return cached

        with ThreadPoolExecutor(max_workers=len(searches)) as pool:
            futures = {
                name: pool.submit(fn, home_team, away_team) for name, fn in searches.items()
            }
            bundle = {name: self.format_hits(f.result()) for name, f in futures.items()}

        if self.cache and cache_key:
            self.cache.put(cache_key, bundle)
        return bundle

    def search_match(
        self,
        home_team: str,
        away_team: str,
        *,
        context: str = "",
        include_answer: bool = True,
        search_depth: str = "basic",
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        query = f"{home_team} vs {away_team} World Cup 2026 {context}".strip()
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": include_answer,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        hits: list[dict[str, Any]] = []
        if include_answer and data.get("answer"):
            hits.append(
                {
                    "title": "Tavily summary (may be wrong — verify against sources)",
                    "snippet": data["answer"],
                    "url": "",
                }
            )
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
            lines.append(f"- {hit['title']}: {hit['snippet'][:500]}")
            if hit.get("url"):
                lines.append(f"  ({hit['url']})")
        return "\n".join(lines)


def _date_hint(kickoff_at: str | None) -> str:
    """Pull YYYY-MM-DD from an ISO kickoff so searches hit the right matchday."""
    if not kickoff_at:
        return ""
    return kickoff_at[:10]
