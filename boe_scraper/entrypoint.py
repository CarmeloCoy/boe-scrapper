#!/usr/bin/env python3
import argparse
import inspect
import sys

from boe_scraper.runner.edictos import EdictosScraperRunner
from boe_scraper.runner.subastas import SubastasScraperRunner


def main() -> int:
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(description="Run BOE scrapers")
    subparsers = parser.add_subparsers(dest="command", required=True)
    runners = [EdictosScraperRunner, SubastasScraperRunner]
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
    args_list = runner.get_args_list(args)
    if not args_list:
        runner.logger.error("Invalid parameters. Use --help for usage information.")
        return 1

    results = runner.run_scraper_workflow(args_list)

    runner.print_results(results)

    if results["failed_parses"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
