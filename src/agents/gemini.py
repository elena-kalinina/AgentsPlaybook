"""Rate-limited Gemini client."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import google.generativeai as genai


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        min_interval_sec: float = 30.0,
    ) -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.min_interval_sec = min_interval_sec
        self._last_call_at = 0.0

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        phase: str = "unknown",
    ) -> dict[str, Any]:
        text = self.generate_text(prompt, system=system, phase=phase)
        return parse_json_response(text)

    def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        phase: str = "unknown",
    ) -> str:
        self._wait_for_rate_limit(phase)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self.model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.4},
        )
        self._last_call_at = time.time()
        return (response.text or "").strip()

    def _wait_for_rate_limit(self, phase: str) -> None:
        elapsed = time.time() - self._last_call_at
        if self._last_call_at and elapsed < self.min_interval_sec:
            wait = self.min_interval_sec - elapsed
            print(f"[gemini:{phase}] spacing {wait:.0f}s (free tier)")
            time.sleep(wait)


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    return json.loads(cleaned)
