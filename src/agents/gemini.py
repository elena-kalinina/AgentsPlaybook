"""Multi-model Gemini router with per-model rate limiting and fallbacks."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from google import genai
from google.genai import errors as genai_errors

from src.config import ModelRoutes, Settings


class ModelRole(str, Enum):
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"
    ACT = "act"


@dataclass
class _ModelSlot:
    primary: str
    fallback: str
    overflow: str = ""


class ModelRouter:
    """Routes LLM calls by role to spread quota across models."""

    def __init__(
        self,
        api_key: str,
        routes: ModelRoutes,
        *,
        min_interval_sec: float = 30.0,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self.min_interval_sec = min_interval_sec
        self._last_call_at: dict[str, float] = {}
        self._slots = {
            ModelRole.SUMMARIZE: _ModelSlot(
                routes.summarize, routes.summarize_fallback, routes.summarize_overflow
            ),
            ModelRole.ANALYZE: _ModelSlot(routes.analyze, routes.analyze_fallback),
            ModelRole.ACT: _ModelSlot(routes.act, routes.act_fallback),
        }
        self._usage: dict[str, int] = {}

    @classmethod
    def from_settings(cls, settings: Settings) -> ModelRouter:
        return cls(
            settings.gemini_api_key,
            settings.model_routes,
            min_interval_sec=settings.gemini_min_interval_sec,
        )

    def summarize_json(
        self, prompt: str, *, system: str | None = None, phase: str = "summarize"
    ) -> dict[str, Any]:
        return self._generate_json(ModelRole.SUMMARIZE, prompt, system=system, phase=phase)

    def analyze_json(
        self, prompt: str, *, system: str | None = None, phase: str = "analyze"
    ) -> dict[str, Any]:
        return self._generate_json(ModelRole.ANALYZE, prompt, system=system, phase=phase)

    def act_json(
        self, prompt: str, *, system: str | None = None, phase: str = "act"
    ) -> dict[str, Any]:
        return self._generate_json(ModelRole.ACT, prompt, system=system, phase=phase)

    def usage_summary(self) -> dict[str, int]:
        return dict(self._usage)

    def check_models(self) -> list[dict[str, str]]:
        """Probe each distinct configured model once and report ok / quota / error.

        Costs one request per distinct model — used before relying on a new split.
        """
        names: list[str] = []
        for role, slot in self._slots.items():
            for name in self._model_chain(role):
                if name not in names:
                    names.append(name)

        results: list[dict[str, str]] = []
        for name in names:
            self._wait_for_rate_limit(name, "check")
            try:
                response = self._client.models.generate_content(
                    model=name,
                    contents="Reply with exactly: OK",
                    config={"temperature": 0.0},
                )
                self._last_call_at[name] = time.time()
                text = (response.text or "").strip()
                results.append({"model": name, "status": "ok", "detail": text[:40]})
            except genai_errors.APIError as exc:
                status = "quota" if exc.code == 429 else "overloaded" if exc.code == 503 else "error"
                results.append({"model": name, "status": status, "detail": str(exc)[:200]})
            except Exception as exc:
                results.append({"model": name, "status": "error", "detail": str(exc)[:200]})
        return results

    def _generate_json(
        self,
        role: ModelRole,
        prompt: str,
        *,
        system: str | None,
        phase: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        text = self._generate_text(role, prompt, system=system, phase=phase, max_retries=max_retries)
        return parse_json_response(text)

    def _generate_text(
        self,
        role: ModelRole,
        prompt: str,
        *,
        system: str | None,
        phase: str,
        max_retries: int = 3,
    ) -> str:
        slot = self._slots[role]
        models = self._model_chain(role)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        last_exc: Exception | None = None

        for model_name in models:
            for attempt in range(max_retries):
                self._wait_for_rate_limit(model_name, phase)
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config={"temperature": 0.4},
                    )
                    self._last_call_at[model_name] = time.time()
                    self._usage[model_name] = self._usage.get(model_name, 0) + 1
                    return (response.text or "").strip()
                except genai_errors.APIError as exc:
                    last_exc = exc
                    # 429 = quota, 503 = transient overload; both worth retrying
                    if exc.code not in (429, 503):
                        print(f"[gemini:{phase}@{model_name}] error: {exc}")
                        break
                    if exc.code == 503:
                        wait = 15.0 * (attempt + 1)
                        reason = "overloaded"
                    else:
                        wait = _retry_delay_sec(exc, fallback=60 * (attempt + 1))
                        reason = "quota"
                    print(
                        f"[gemini:{phase}@{model_name}] {reason} — retry in {wait:.0f}s "
                        f"({attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait)
                except Exception as exc:
                    last_exc = exc
                    print(f"[gemini:{phase}@{model_name}] error: {exc}")
                    break

            if model_name == slot.primary:
                print(f"[gemini:{phase}] falling back {slot.primary} → {slot.fallback}")
            elif (
                role == ModelRole.SUMMARIZE
                and model_name == slot.fallback
                and len(models) > 2
            ):
                print(
                    f"[gemini:{phase}] overflow fallback "
                    f"{slot.fallback} → {models[2]}"
                )

        raise RuntimeError(
            f"Gemini failed for role={role.value} phase={phase}: {last_exc}"
        )

    def _model_chain(self, role: ModelRole) -> list[str]:
        """Primary → fallback → optional overflow (deduped, separate quota buckets)."""
        slot = self._slots[role]
        chain = [slot.primary, slot.fallback]
        if role == ModelRole.SUMMARIZE and slot.overflow:
            chain.append(slot.overflow)
        seen: set[str] = set()
        out: list[str] = []
        for name in chain:
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out

    def _wait_for_rate_limit(self, model_name: str, phase: str) -> None:
        last = self._last_call_at.get(model_name, 0.0)
        elapsed = time.time() - last
        if last and elapsed < self.min_interval_sec:
            wait = self.min_interval_sec - elapsed
            print(f"[gemini:{phase}@{model_name}] spacing {wait:.0f}s")
            time.sleep(wait)


# Backward-compatible alias for any direct single-model use
GeminiClient = ModelRouter


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    return json.loads(cleaned)


def _retry_delay_sec(exc: Exception, *, fallback: float) -> float:
    text = str(exc)
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", text, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 2.0
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", text)
    if match:
        return float(match.group(1)) + 2.0
    return fallback
