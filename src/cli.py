"""CLI entry points."""

from __future__ import annotations

import argparse
import sys

from src.config import load_settings
from src.loop.daily import run_daily_loop, run_reflect_only


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cup Clash agent runner")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-daily-loop", help="Settle → reflect → evolve → place next 3 bets")

    reflect = sub.add_parser(
        "reflect-only",
        help="Fix invalid knockout bets, then settle → reflect → evolve (no new bets)",
    )
    reflect.add_argument(
        "--force-evolve",
        action="store_true",
        help="Always rewrite the playbook even if the model says no",
    )

    fix = sub.add_parser(
        "fix-knockout-bets",
        help="Fix scheduled knockout bets that incorrectly picked draw",
    )

    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command == "run-daily-loop":
        run_daily_loop(settings)
        return 0

    if args.command == "reflect-only":
        run_reflect_only(settings, force_evolve=args.force_evolve)
        return 0

    if args.command == "fix-knockout-bets":
        from src.agents.gemini import ModelRouter
        from src.intel.tavily import TavilySearch
        from src.loop.daily import fix_knockout_bets
        from src.mcp.client import McpClient

        mcp = McpClient(settings.mcp_url, settings.mcp_token)
        router = ModelRouter.from_settings(settings)
        tavily = TavilySearch(settings.tavily_api_key)
        fixes = fix_knockout_bets(settings, mcp, router, tavily)
        print(f"Fixed {len(fixes)} bet(s). Model usage: {router.usage_summary()}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
