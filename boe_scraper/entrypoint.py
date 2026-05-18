#!/usr/bin/env python3
import argparse
import inspect
import sys

from boe_scraper.runner.edictos import EdictosScraperRunner
from boe_scraper.runner.edictos_re_parser import EdictosReParserScraperRunner
from boe_scraper.runner.subastas import SubastasScraperRunner


def main() -> int:
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(description="Run BOE scrapers")
    subparsers = parser.add_subparsers(dest="command", required=True)
    runners = [
        EdictosScraperRunner,
        EdictosReParserScraperRunner,
        SubastasScraperRunner,
    ]
    for runner in runners:
        subparser = subparsers.add_parser(
            runner.get_command_name(), help=inspect.getdoc(runner)
        )
        runner.configure_argparser(subparser)
    args = parser.parse_args()

    runner_cls = None
    for runner in runners:
        if args.command == runner.get_command_name():
            runner_cls = runner
            break
    if not runner_cls:
        parser.print_help()
        return 1

    runner = runner_cls.from_argparser(args)
    results = runner.run_scraper_workflow()

    if not results:
        print("Failed to run scraper")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
