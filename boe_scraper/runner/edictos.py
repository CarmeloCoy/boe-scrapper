"""
BOE Edictos Scraper runner helpers.

This module contains the reusable runner class and convenience
functions to execute the scraper programmatically.
"""

from datetime import datetime, timedelta

import boe_scraper.utils.date as date_utils
from boe_scraper.settings import settings

from .base import ScraperRunner


class EdictosScraperRunner(ScraperRunner):
    """Main class for running the Edictos BOE scraper across multiple dates."""

    def __init__(
        self,
        pattern: str,
        output_path: str,
        parse_only: bool = True,
        format: str = "delta",
        download_path: str | None = None,
        log_file: str | None = None,
        log_level: str | None = None,
    ):
        """Initialize the runner with optional data folder override."""
        super().__init__(
            scraper="edictos_boe_parser",
            output_path=output_path,
            format=format,
            log_file=log_file,
            log_level=log_level,
        )
        self.pattern = pattern
        self.parse_only = parse_only
        self.download_path = download_path
        self._env["DOWNLOAD_PATH"] = self.download_path or settings.download_path

    def get_arguments_command(self, dates: list[str] = None):
        cmd = [
            "-a",
            f"dates={','.join(dates)}",
            "-a",
            f"parse_only={self.parse_only}",
            "-a",
            f"pattern={self.pattern}",
        ]
        return cmd

    @staticmethod
    def configure_argparser(parser):
        ScraperRunner.configure_argparser(parser)

        # Date range options
        parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
        parser.add_argument("--month", type=int, help="Month (1-12)")
        parser.add_argument("--year", type=int, help="Year (default: current year)")
        parser.add_argument("--weeks", type=int, help="Number of weeks from start date")
        parser.add_argument(
            "--dates", type=str, nargs="+", help="Specific dates (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--previous-week",
            action="store_true",
            help="Run scraper for the previous calendar week (Monday to Sunday)",
        )
        # Other options
        parser.add_argument(
            "--store-html",
            action="store_true",
            help="Store HTML files in the download folder if not set uses the data folder",
        )
        parser.add_argument(
            "--download-path",
            type=str,
            help="Override download folder path. Required if the store-html flag is enabled.",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            help="Regex pattern to filter BOE edictos (passed to boe_parser spider)",
            required=True,
        )

    @staticmethod
    def get_command_name():
        return "edictos"

    @staticmethod
    def get_args_list(args):
        dates = get_dates_from_args(args)
        if not dates:
            return None
        return [{"dates": dates}]

    @staticmethod
    def from_argparser(args):
        return EdictosScraperRunner(
            format=args.format,
            download_path=args.download_path,
            output_path=args.output_path,
            log_file=args.log_file,
            log_level=args.log_level,
            pattern=args.pattern,
            parse_only=args.store_html is None,
        )


def run_scraper_for_dates(
    dates: list[str], output_path: str, pattern: str, parse_only: bool = False
) -> dict:
    """
    Run the scraper for a list of dates.

    Args:
        dates: List of date strings in YYYY-MM-DD format
        output_path: Path to write the output files
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)
        parse_only: If True, only parse HTML files, skip downloading

    Returns:
        Dictionary with scraping results
    """
    runner = EdictosScraperRunner(
        pattern=pattern, parse_only=parse_only, output_path=output_path
    )
    results = runner.run_scraper_workflow([{"dates": dates}])
    runner.print_results(results)
    return results


def scrape_current_month(
    output_path: str, pattern: str, parse_only: bool = False
) -> dict:
    """Scrape the current month."""
    now = datetime.now()
    dates = date_utils.generate_month_dates(now.year, now.month)
    print(f"Scraping current month ({now.year}-{now.month:02d}): {len(dates)} days")
    return run_scraper_for_dates(dates, output_path, pattern, parse_only)


def scrape_last_week(output_path: str, pattern: str, parse_only: bool = False) -> dict:
    """Scrape the last week."""
    last_week_start = (datetime.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")
    dates = date_utils.generate_week_dates(last_week_start, 1)
    print(f"Scraping last week: {dates}")
    return run_scraper_for_dates(dates, output_path, pattern, parse_only)


def scrape_date_range(
    start_date: str,
    end_date: str,
    output_path: str,
    pattern: str,
    parse_only: bool = False,
) -> dict:
    """
    Scrape a specific date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_path: Path to write the output files
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)
    """
    dates = date_utils.generate_date_range(start_date, end_date)
    print(f"Scraping date range {start_date} to {end_date}: {len(dates)} days")
    return run_scraper_for_dates(dates, output_path, pattern, parse_only)


def scrape_specific_month(
    year: int, month: int, output_path: str, pattern: str, parse_only: bool = False
) -> dict:
    """
    Scrape a specific month.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        output_path: Path to write the output files
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)
    """
    dates = date_utils.generate_month_dates(year, month)
    print(f"Scraping {year}-{month:02d}: {len(dates)} days")
    return run_scraper_for_dates(dates, output_path, pattern, parse_only)


def scrape_previous_week(
    output_path: str, pattern: str, parse_only: bool = False
) -> dict:
    """
    Scrape the previous calendar week (Monday to Sunday).

    Args:
        output_path: Path to write the output files
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)

    Returns:
        Dictionary with scraping results
    """
    dates = date_utils.get_previous_week_dates()
    print(f"Scraping previous week: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    return run_scraper_for_dates(dates, output_path, pattern, parse_only)


def get_dates_from_args(args) -> list[str]:
    """Build list of dates from CLI arguments for the edictos command."""
    if args.dates:
        return args.dates
    if args.previous_week:
        return date_utils.get_previous_week_dates()
    if args.start_date and args.end_date:
        return date_utils.generate_date_range(args.start_date, args.end_date)
    if args.month:
        year = args.year or datetime.now().year
        return date_utils.generate_month_dates(year, args.month)
    if args.start_date and args.weeks:
        return date_utils.generate_week_dates(args.start_date, args.weeks)

    now = datetime.now()
    return date_utils.generate_month_dates(now.year, now.month)
