"""Load configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ModelRoutes:
    summarize: str
    summarize_fallback: str
    analyze: str
    analyze_fallback: str
    act: str
    act_fallback: str


@dataclass(frozen=True)
class Settings:
    mcp_url: str
    mcp_token: str
    group_id: str
    gemini_api_key: str
    model_routes: ModelRoutes
    tavily_api_key: str
    gemini_min_interval_sec: float
    playbook_path: Path
    logs_dir: Path
    data_dir: Path
    predictions_path: Path
    metrics_path: Path


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")

    default = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    summarize = os.environ.get("GEMINI_MODEL_SUMMARIZE", default)
    analyze = os.environ.get("GEMINI_MODEL_ANALYZE", "gemini-3-flash-preview")
    act = os.environ.get("GEMINI_MODEL_ACT", default)

    return Settings(
        mcp_url=os.environ["APP_MCP_SERVER_URL"],
        mcp_token=os.environ["APP_MCP_SERVER_TOKEN"],
        group_id=os.environ["CUP_CLASH_GROUP_ID"],
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        model_routes=ModelRoutes(
            summarize=summarize,
            summarize_fallback=os.environ.get("GEMINI_MODEL_SUMMARIZE_FALLBACK", analyze),
            analyze=analyze,
            analyze_fallback=os.environ.get("GEMINI_MODEL_ANALYZE_FALLBACK", summarize),
            act=act,
            act_fallback=os.environ.get("GEMINI_MODEL_ACT_FALLBACK", analyze),
        ),
        tavily_api_key=os.environ["TAVILY_API_KEY"],
        gemini_min_interval_sec=float(os.environ.get("GEMINI_MIN_INTERVAL_SEC", "30")),
        playbook_path=ROOT / "playbooks" / "playbook.md",
        logs_dir=ROOT / "logs",
        data_dir=ROOT / "data",
        predictions_path=ROOT / "data" / "predictions.json",
        metrics_path=ROOT / "data" / "metrics.json",
    )
