"""Cup Clash MCP HTTP client."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class McpClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token
        self._session: str | None = None

    def _post(self, body: dict[str, Any], *, include_session: bool = True) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": UA,
        }
        if include_session and self._session:
            headers["Mcp-Session-Id"] = self._session

        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw_headers = resp.headers
                text = resp.read().decode()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode() if exc.fp else str(exc)
            raise RuntimeError(f"MCP HTTP {exc.code}: {detail}") from exc

        if not self._session:
            session = raw_headers.get("mcp-session-id") or raw_headers.get("Mcp-Session-Id")
            if session:
                self._session = session.strip()

        payload = _unwrap_sse(text)
        if "error" in payload:
            raise RuntimeError(f"MCP error: {payload['error']}")
        return payload

    def _ensure_session(self) -> None:
        if self._session:
            return
        self._post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "agents-playbook", "version": "0.1.0"},
                },
            },
            include_session=False,
        )
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except RuntimeError:
            pass

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        self._ensure_session()
        payload = self._post(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        )
        result = payload.get("result") or {}
        content = result.get("content") or []
        if not content:
            return result
        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def get_my_bets(self, group_id: str, *, include_finished: bool = False) -> list[dict[str, Any]]:
        return self.call_tool(
            "get_my_bets",
            {"group_id": group_id, "include_finished": include_finished},
        )

    def list_upcoming_matches(self, group_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
        return self.call_tool(
            "list_upcoming_matches",
            {"group_id": group_id, "limit": limit},
        )

    def place_bet(self, **kwargs: Any) -> Any:
        return self.call_tool("place_bet", kwargs)


def _unwrap_sse(text: str) -> dict[str, Any]:
    for line in text.splitlines():
        if line.startswith("data: "):
            candidate = line[6:]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise RuntimeError(f"Could not parse MCP response: {text[:300]}")
