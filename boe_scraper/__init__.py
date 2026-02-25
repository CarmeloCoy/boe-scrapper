from boe_scraper.runner.edictos import (
    scrape_current_month,
    scrape_date_range,
    scrape_last_week,
    scrape_previous_week,
    scrape_specific_month,
)
from boe_scraper.runner.subastas import run_subastas_scraper_for_dates

__all__ = [
    "scrape_current_month",
    "scrape_date_range",
    "scrape_last_week",
    "scrape_previous_week",
    "scrape_specific_month",
    "run_subastas_scraper_for_dates",
]

import os

from single_source import get_version

__version__ = get_version(__name__, os.path.dirname(os.path.dirname(__file__)))
