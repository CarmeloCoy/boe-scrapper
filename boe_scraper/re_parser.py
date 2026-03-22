#!/usr/bin/env python3
"""
BOE Scraper Date RE Runner

"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile

from boe_scraper.settings import settings
from boe_scraper.utils.writter import boe_jsonl_to_csv, boe_jsonl_to_delta


class DateScraperReRunner:
    """Main class for running the BOE scraper across multiple dates."""

    def __init__(
        self,
        format: str = "delta",
        download_path: str = None,
        output_path: str = None,
        log_file: str = None,
        log_level: str = None,
        pattern: str = None,
    ):
        """Initialize the runner with optional data folder override."""
        self.format = format
        self.pattern = pattern
        self.download_path = download_path or settings.download_path
        self.output_path = output_path
        self.log_file = log_file or settings.log_file
        self.log_level = log_level or settings.log_level
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=self.log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def run_re_parser_for_date(self, date: str, output_file_name: str) -> str:
        """Run the parser for a specific date and return true if success."""
        self.logger.info(f"Running parser for date: {date}")
        try:
            # Build the scrapy command
            cmd = [
                "scrapy",
                "crawl",
                "re_boe_parser",
                "-a",
                f"date={date}",
                "-a",
                f"download_path={self.download_path}",
                "-a",
                f"pattern={self.pattern}",
                "-L",
                self.log_level,
                "-o",
                f"{output_file_name}:jsonl",
            ]
            # Run the command
            self.logger.info(cmd)
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"Successfully parsed date: {date}")
                return True
            else:
                self.logger.error(f"Failed to parse date {date}: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Exception while downloading date {date}: {str(e)}")
            return False

    def write_parser_output(self, parser_output_path: str) -> dict:
        """Writes the output file in the specified format to the output path"""
        if self.format == "delta":
            boe_jsonl_to_delta(parser_output_path, self.output_path)
        elif self.format == "csv":
            boe_jsonl_to_csv(parser_output_path, self.output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def run_re_scraper_workflow(self) -> dict:
        """Run the complete scraper workflow for a list of dates."""

        # INSERT_YOUR_CODE
        dates = []
        for name in os.listdir(self.download_path):
            full_path = os.path.join(self.download_path, name)
            if os.path.isdir(full_path) and name.startswith("date="):
                dates.append(name.replace("date=", ""))
        dates.sort()
        results = {
            "total_dates": len(dates),
            "successful_parses": 0,
            "failed_parses": [],
            "skipped_dates": [],
        }

        self.logger.info(f"Starting scraper workflow for {len(dates)} dates")

        n = 20
        chunks = [dates[i : i + n] for i in range(0, len(dates), n)]
        for chunk in chunks:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.logger.info(f"Temporary file created at: {tmp_file.name}")
            tmp_file.close()
            for date in chunk:
                self.logger.info(f"Processing date: {date}")

                parse_success = self.run_re_parser_for_date(date, tmp_file.name)
                if parse_success:
                    results["successful_parses"] += 1
                else:
                    results["failed_parses"].append(date)
            self.logger.info(f"Writing output tmp {tmp_file.name} to expected output")
            self.write_parser_output(tmp_file.name)
            os.remove(tmp_file.name)

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


def main():
    """Main function to run the scraper with command line arguments."""
    parser = argparse.ArgumentParser(description="Run BOE scraper for multiple dates")
    parser.add_argument("--log-path", type=str, help="Override log path")
    parser.add_argument("--log-level", type=str, help="Log level")

    # Other options
    parser.add_argument(
        "--format", type=str, help="Format to write the output files", default="delta"
    )
    parser.add_argument(
        "--download-path", type=str, help="Override download folder path"
    )
    parser.add_argument(
        "--output-path", type=str, help="Path to write the output files"
    )
    parser.add_argument(
        "--pattern",
        required=True,
        type=str,
        help="Regex pattern to filter BOE edictos (passed to boe_parser spider)",
    )

    args = parser.parse_args()

    # Initialize runner
    runner = DateScraperReRunner(
        format=args.format,
        download_path=args.download_path,
        output_path=args.output_path,
        log_file=args.log_file,
        log_level=args.log_level,
        pattern=args.pattern,
    )
    results = runner.run_re_scraper_workflow()

    # Print results
    runner.print_results(results)

    # Return appropriate exit code
    if results["failed_parses"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
