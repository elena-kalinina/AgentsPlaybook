"""CLI entry points."""

from __future__ import annotations

import argparse
import sys

from src.config import load_settings
from src.loop.daily import run_daily_loop, run_maybe_prebet, run_place_bets_only, run_prebet_refresh, run_reflect_only
from src.loop.livelog import live_log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cup Clash agent runner")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-daily-loop", help="Settle → reflect → evolve → place next N bets (BET_BATCH_SIZE)")

    sub.add_parser(
        "prebet",
        help="Refresh intel and re-place bets for ALL upcoming matches (run near kickoff)",
    )

    place = sub.add_parser(
        "place-bets",
        help="Resume from phase 5: place bets only (no reflection, uses cached Tavily intel)",
    )
    place.add_argument(
        "--daily-cycle",
        action="store_true",
        help="Mark morning daily cycle complete (enables prebet for today)",
    )

    sub.add_parser(
        "maybe-prebet",
        help="Run prebet only if inside T-50 window (for GitHub Actions polling)",
    )

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

    sub.add_parser(
        "check-models",
        help="Probe each configured Gemini model once and report ok/quota/error",
    )

    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command == "run-daily-loop":
        with live_log(settings.live_log_path):
            run_daily_loop(settings)
        return 0

    if args.command == "prebet":
        with live_log(settings.live_log_path):
            run_prebet_refresh(settings)
        return 0

    if args.command == "place-bets":
        with live_log(settings.live_log_path):
            run_place_bets_only(settings, mark_daily_cycle=args.daily_cycle)
        return 0

    if args.command == "maybe-prebet":
        with live_log(settings.live_log_path):
            run_maybe_prebet(settings)
        return 0

    if args.command == "reflect-only":
        with live_log(settings.live_log_path):
            run_reflect_only(settings, force_evolve=args.force_evolve)
        return 0

    if args.command == "check-models":
        from src.agents.gemini import ModelRouter

        router = ModelRouter.from_settings(settings)
        routes = settings.model_routes
        print(
            f"Routes: summarize={routes.summarize} (fb {routes.summarize_fallback}, "
            f"overflow {routes.summarize_overflow}), "
            f"analyze={routes.analyze} (fb {routes.analyze_fallback}), "
            f"act={routes.act} (fb {routes.act_fallback})"
        )
        results = router.check_models()
        failed = False
        for row in results:
            marker = "OK  " if row["status"] == "ok" else "FAIL"
            print(f"  [{marker}] {row['model']}: {row['status']} — {row['detail']}")
            if row["status"] != "ok":
                failed = True
        return 1 if failed else 0

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
