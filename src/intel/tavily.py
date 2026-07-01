"""Tavily web search for match context."""

from __future__ import annotations

from typing import Any

import requests


class TavilySearch:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

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
