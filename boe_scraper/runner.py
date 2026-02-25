#!/usr/bin/env python3
"""
BOE Scraper Date Runner

This script loops over a collection of dates and runs the BOE scraper for each date.
It supports various date generation methods and includes error handling and logging.
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

import boe_scraper.utils.date as date_utils
from boe_scraper.settings import settings
from boe_scraper.utils.writter import boe_jsonl_to_csv, boe_jsonl_to_delta


class DateScraperRunner:
    """Main class for running the BOE scraper across multiple dates."""

    def __init__(
        self,
        pattern: str,
        output_path: str,
        format: str = "delta",
        download_path: str = None,
        log_path: str = None,
        log_level: str = None,
    ):
        """Initialize the runner with optional data folder override."""
        self.format = format
        self.pattern = pattern
        self.download_path = download_path or settings.download_path
        self.output_path = output_path
        self.log_path = log_path or settings.log_path
        self.log_level = log_level or settings.log_level
        self.setup_logging()
        env = os.environ.copy()
        env["DOWNLOAD_PATH"] = self.download_path
        self._env = env

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=self.log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f"{self.log_path}/scraper_runner.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def run_parser_for_date(self, date: str, parse_only: bool = True) -> str:
        """Run the parser for a specific date and return the path to the temporary file."""
        try:
            self.logger.info(f"Running parser for date: {date}")
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.logger.debug(f"Temporary file created at: {tmp_file.name}")
            tmp_file.close()
            # Build the scrapy command
            cmd = [
                "scrapy",
                "crawl",
                "boe_parser",
                "-a",
                f"date={date}",
                "-a",
                f"parse_only={parse_only}",
            ]
            if self.pattern is not None:
                cmd.extend(["-a", f"pattern={self.pattern}"])
            cmd.extend(
                [
                    "-L",
                    self.log_level,
                    "-o",
                    f"{tmp_file.name}:jsonl",
                ]
            )
            # Run the command
            self.logger.debug(" ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, env=self._env)

            if result.returncode == 0:
                self.logger.info(f"Successfully parsed date: {date}")
                return tmp_file.name
            else:
                self.logger.error(f"Failed to parse date {date}: {result.stderr}")
                return None

        except Exception as e:
            self.logger.error(f"Exception while downloading date {date}: {str(e)}")
            return None

    def write_parser_output(self, parser_output_path: str, first: bool) -> dict:
        """Writes the output file in the specified format to the output path"""
        if self.format == "delta":
            boe_jsonl_to_delta(parser_output_path, self.output_path)
        elif self.format == "csv":
            boe_jsonl_to_csv(
                parser_output_path, self.output_path, "overwrite" if first else "append"
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

    def run_scraper_workflow(self, dates: list[str], parse_only: bool = True) -> dict:
        """Run the complete scraper workflow for a list of dates."""
        results = {
            "total_dates": len(dates),
            "successful_parses": 0,
            "failed_parses": [],
            "skipped_dates": [],
        }

        self.logger.info(f"Starting scraper workflow for {len(dates)} dates")

        first = True
        for date in dates:
            self.logger.info(f"Processing date: {date}")

            parse_success = self.run_parser_for_date(date, parse_only)
            if parse_success:
                self.write_parser_output(parse_success, first)
                first = False
                results["successful_parses"] += 1
            else:
                results["failed_parses"].append(date)

        return results

    def print_results(self, results: dict):
        """Print a summary of the scraping results."""
        self.logger.info("=" * 50)
        self.logger.info("SCRAPING RESULTS SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total dates processed: {results['total_dates']}")
        self.logger.info(f"Successful parses: {results['successful_parses']}")

        if results["failed_parses"]:
            self.logger.warning(f"Failed parses: {len(results['failed_parses'])}")
            self.logger.warning(f"Failed parse dates: {results['failed_parses']}")

        self.logger.info("=" * 50)


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
    runner = DateScraperRunner(pattern=pattern, output_path=output_path)
    results = runner.run_scraper_workflow(dates, parse_only=parse_only)
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


def scrape_business_days(
    start_date: str, end_date: str, parse_only: bool = False, pattern: str = None
) -> dict:
    """
    Scrape only business days (Monday-Friday) in a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)
    """
    dates = date_utils.get_business_days(start_date, end_date)
    print(f"Scraping business days from {start_date} to {end_date}: {len(dates)} days")
    return run_scraper_for_dates(dates, parse_only, pattern)


def scrape_specific_month(
    year: int, month: int, parse_only: bool = False, pattern: str = None
) -> dict:
    """
    Scrape a specific month.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)
    """
    dates = date_utils.generate_month_dates(year, month)
    print(f"Scraping {year}-{month:02d}: {len(dates)} days")
    return run_scraper_for_dates(dates, parse_only, pattern)


def scrape_previous_week(parse_only: bool = False, pattern: str = None) -> dict:
    """
    Scrape the previous calendar week (Monday to Sunday).

    Args:
        parse_only: If True, only parse HTML files, skip downloading
        pattern: Optional regex pattern to filter BOE edictos (passed to boe_parser spider)

    Returns:
        Dictionary with scraping results
    """
    dates = date_utils.get_previous_week_dates()
    print(f"Scraping previous week: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    return run_scraper_for_dates(dates, parse_only, pattern)


def main():
    """Main function to run the scraper with command line arguments."""
    parser = argparse.ArgumentParser(description="Run BOE scraper for multiple dates")

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
    parser.add_argument("--log-path", type=str, help="Override log path")
    parser.add_argument("--log-level", type=str, help="Log level")

    # Other options
    parser.add_argument(
        "--format", type=str, help="Format to write the output files", default="csv"
    )
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
        "--output-path", type=str, help="Path to write the output files", required=True
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Regex pattern to filter BOE edictos (passed to boe_parser spider)",
        required=True,
    )

    args = parser.parse_args()

    # Initialize runner
    runner = DateScraperRunner(
        format=args.format,
        download_path=args.download_path,
        output_path=args.output_path,
        log_path=args.log_path,
        log_level=args.log_level,
        pattern=args.pattern,
    )

    # Determine which dates to process
    dates = []

    if args.dates:
        # Use specific dates
        dates = args.dates
    elif args.previous_week:
        # Use previous calendar week
        dates = date_utils.get_previous_week_dates()
    elif args.start_date and args.end_date:
        # Use date range
        dates = date_utils.generate_date_range(args.start_date, args.end_date)
    elif args.month:
        # Use specific month
        year = args.year or datetime.now().year
        dates = date_utils.generate_month_dates(year, args.month)
    elif args.start_date and args.weeks:
        # Use weeks from start date
        dates = date_utils.generate_week_dates(args.start_date, args.weeks)
    else:
        # Default: current month
        now = datetime.now()
        dates = date_utils.generate_month_dates(now.year, now.month)

    if not dates:
        runner.logger.error("No dates specified. Use --help for usage information.")
        return 1

    runner.logger.info(f"Will process {len(dates)} dates: {dates}")

    # Run the scraper workflow
    parse_only = args.store_html is None
    results = runner.run_scraper_workflow(dates, parse_only=parse_only)

    # Print results
    runner.print_results(results)

    # Return appropriate exit code
    if results["failed_parses"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
