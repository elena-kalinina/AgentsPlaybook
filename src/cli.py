"""CLI entry points."""

from __future__ import annotations

import argparse
import sys

from src.config import load_settings
from src.loop.daily import run_daily_loop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cup Clash agent runner")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-daily-loop", help="Settle → reflect → evolve → place next 3 bets")

    args = parser.parse_args(argv)
    settings = load_settings()

    if args.command == "run-daily-loop":
        run_daily_loop(settings)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
