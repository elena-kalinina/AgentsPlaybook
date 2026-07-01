"""Load configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    mcp_url: str
    mcp_token: str
    group_id: str
    gemini_api_key: str
    gemini_model: str
    tavily_api_key: str
    gemini_min_interval_sec: float
    playbook_path: Path
    logs_dir: Path


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        mcp_url=os.environ["APP_MCP_SERVER_URL"],
        mcp_token=os.environ["APP_MCP_SERVER_TOKEN"],
        group_id=os.environ["CUP_CLASH_GROUP_ID"],
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        tavily_api_key=os.environ["TAVILY_API_KEY"],
        gemini_min_interval_sec=float(os.environ.get("GEMINI_MIN_INTERVAL_SEC", "30")),
        playbook_path=ROOT / "playbooks" / "playbook.md",
        logs_dir=ROOT / "logs",
    )
