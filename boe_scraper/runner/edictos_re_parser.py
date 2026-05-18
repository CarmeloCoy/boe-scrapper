"""
BOE Edictos Regex Parser runner helpers.
"""

from boe_scraper.settings import settings

from .base import ScraperRunner


class EdictosReParserScraperRunner(ScraperRunner):
    """Main class for running the Edictos BOE scraper across multiple dates."""

    def __init__(
        self,
        pattern: str,
        output_path: str,
        format: str = "csv",
        download_path: str | None = None,
        log_file: str | None = None,
        log_level: str | None = None,
    ):
        """Initialize the runner with optional data folder override."""
        super().__init__(
            scraper="re_boe_parser",
            output_path=output_path,
            format=format,
            log_file=log_file,
            log_level=log_level,
        )
        self.pattern = pattern
        self.download_path = download_path
        self._env["DOWNLOAD_PATH"] = self.download_path or settings.download_path

    def get_arguments_command(self):
        cmd = [
            "-a",
            f"pattern={self.pattern}",
        ]
        return cmd

    @staticmethod
    def configure_argparser(parser):
        ScraperRunner.configure_argparser(parser)

        # Date range options
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
        return "re-parse-edictos"

    @staticmethod
    def from_argparser(args):
        return EdictosReParserScraperRunner(
            format=args.format,
            download_path=args.download_path,
            output_path=args.output_path,
            log_file=args.log_file,
            log_level=args.log_level,
            pattern=args.pattern,
        )


def run_re_parser(download_path: str, output_path: str, pattern: str) -> bool:
    """
    Run the regex parser for a list of dates.
    """
    runner = EdictosReParserScraperRunner(
        pattern=pattern, download_path=download_path, output_path=output_path
    )
    return runner.run_scraper_workflow()
