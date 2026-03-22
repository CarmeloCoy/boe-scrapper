"""
This module contains the reusable runner class and convenience
functions to execute the scraper programmatically.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod

from boe_scraper.settings import settings
from boe_scraper.utils.writter import boe_jsonl_to_csv, boe_jsonl_to_delta


class ScraperRunner(ABC):
    """Main class for running scraper"""

    def __init__(
        self,
        scraper: str,
        output_path: str,
        format: str = "jsonl",
        log_file: str | None = None,
        log_level: str | None = None,
    ):
        """Initialize the runner with optional data folder override."""
        self.scraper = scraper
        self.format = format
        self.output_path = output_path
        self.log_file = log_file or settings.log_file
        self.log_level = log_level or settings.log_level
        self.setup_logging()
        env = os.environ.copy()
        self._env = env

    def setup_logging(self) -> None:
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

    @staticmethod
    def add_common_arguments(parser):
        """Add reusable arguments"""
        parser.add_argument(
            "--output-path",
            type=str,
            help="Path to write the output files",
            required=True,
        )
        parser.add_argument("--log-file", type=str, help="Override log file")
        parser.add_argument("--log-level", type=str, help="Log level")
        parser.add_argument(
            "--format", type=str, help="Format to write the output files", default="csv"
        )

    @staticmethod
    def configure_argparser(parser):
        ScraperRunner.add_common_arguments(parser)

    @staticmethod
    @abstractmethod
    def get_command_name():
        pass

    @staticmethod
    @abstractmethod
    def from_argparser(args):
        pass

    @staticmethod
    @abstractmethod
    def get_args_list(args):
        pass

    @abstractmethod
    def get_arguments_command(self, **kwargs):
        pass

    def run_scraper(self, **kwargs) -> str | None:
        """Run the scraper for a specific date and return the path to the temporary file."""
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.logger.debug(f"Temporary file created at: {tmp_file.name}")
            tmp_file.close()
            # Build the scrapy command
            cmd = [
                "scrapy",
                "crawl",
                self.scraper,
            ]
            cmd.extend(self.get_arguments_command(**kwargs))
            cmd.extend(
                [
                    "--logfile",
                    self.logfile,
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
                return tmp_file.name

            self.logger.error(f"Failed to parse: {result.stderr}")
            return None

        except Exception as e:  # noqa: BLE001
            self.logger.exception(f"Exception executing scraper: {str(e)}")
            return None

    def write_parser_output(self, parser_output_path: str, first: bool) -> None:
        """Writes the output file in the specified format to the output path."""
        if self.format == "delta":
            boe_jsonl_to_delta(parser_output_path, self.output_path)
        elif self.format == "csv":
            boe_jsonl_to_csv(
                parser_output_path,
                self.output_path,
                "overwrite" if first else "append",
            )
        elif self.format == "jsonl":
            shutil.copyfile(parser_output_path, self.output_path)
        else:
            raise ValueError(f"Unsupported format: {self.format}")

    def run_scraper_workflow(self, args_list: list[dict]) -> dict:
        """Run the complete scraper workflow for a list."""
        results = {
            "total_dates": len(args_list),
            "successful_parses": 0,
            "failed_parses": [],
            "skipped_parses": [],
        }

        self.logger.info(f"Starting scraper workflow for {len(args_list)} iterations")

        first = True
        for index, args in enumerate(args_list):
            self.logger.info(f"Processing element: {index}")

            parse_success = self.run_scraper(**args)
            if parse_success:
                self.write_parser_output(parse_success, first)
                first = False
                results["successful_parses"] += 1
            else:
                results["failed_parses"].append(index)

        return results

    def print_results(self, results: dict) -> None:
        """Print a summary of the scraping results."""
        self.logger.info("=" * 50)
        self.logger.info("SCRAPING RESULTS SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total dates processed: {results['total_dates']}")
        self.logger.info(f"Successful parses: {results['successful_parses']}")

        if results["failed_parses"]:
            self.logger.warning(f"Failed parses: {len(results['failed_parses'])}")
            self.logger.warning(f"Failed parses: {results['failed_parses']}")

        self.logger.info("=" * 50)
