"""
BOE Edictos Scraper runner helpers.

This module contains the reusable runner class and convenience
functions to execute the scraper programmatically.
"""

from .base import ScraperRunner


class SubastasScraperRunner(ScraperRunner):
    """Run BOE subastas scraper for a range of dates for a province"""

    def __init__(
        self,
        output_path: str,
        code_province: str = "30",
        from_start_date: str | None = None,
        to_start_date: str | None = None,
        format: str = "jsonl",
        log_file: str | None = None,
        log_level: str | None = None,
    ):
        """Initialize the runner with optional data folder override."""
        super().__init__(
            scraper="subastas_boe_parser",
            output_path=output_path,
            format=format,
            log_file=log_file,
            log_level=log_level,
        )
        self.from_start_date = from_start_date
        self.to_start_date = to_start_date
        self.code_province = code_province

    def get_arguments_command(self):
        cmd = ["-a", f"cod_provincia={self.code_province}"]
        if self.from_start_date:
            cmd.extend(
                [
                    "-a",
                    f"from_start_date={self.from_start_date}",
                ]
            )
        if self.to_start_date:
            cmd.extend(
                [
                    "-a",
                    f"to_start_date={self.to_start_date}",
                ]
            )
        return cmd

    @staticmethod
    def configure_argparser(parser):
        ScraperRunner.configure_argparser(parser)
        parser.add_argument(
            "--from-start-date", type=str, help="From start date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--to-start-date", type=str, help="To start date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--code-province", type=int, help="INE cod province", required=True
        )

    @staticmethod
    def get_command_name():
        return "subastas"

    @staticmethod
    def from_argparser(parser):
        return SubastasScraperRunner(
            code_province=parser.code_province,
            from_start_date=parser.from_start_date,
            to_start_date=parser.to_start_date,
            format=parser.format,
            output_path=parser.output_path,
            log_file=parser.log_file,
            log_level=parser.log_level,
        )


def run_subastas_scraper_for_dates(
    cod_provincia: str,
    output_path: str,
    from_start_date: str | None = None,
    to_start_date: str | None = None,
    format: str = "jsonl",
) -> dict:
    """
    Run the scraper for a province in a range of dates (optional).

    Args:
        cod_provincia: INE cod provincia
        from_start_date:
        to_start_date:

    Returns:
        Dictionary with scraping results
    """
    if format is None:
        try:
            format = output_path.split["."][-1]
        except ValueError:
            raise ValueError("Format not provided anc could not be inphered from path")
    runner = SubastasScraperRunner(
        code_province=cod_provincia,
        from_start_date=from_start_date,
        to_start_date=to_start_date,
        format=format,
        output_path=output_path,
    )
    return runner.run_scraper_workflow()
