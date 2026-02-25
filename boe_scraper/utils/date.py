#!/usr/bin/env python3
"""
Date Utilities for BOE Scraper

Utility functions for generating date collections for the BOE scraper.
"""

import calendar
from datetime import datetime, timedelta
from typing import List


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate a list of dates between start_date and end_date (inclusive).

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def generate_month_dates(year: int, month: int) -> List[str]:
    """
    Generate all dates for a specific month.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d}"

    return generate_date_range(start_date, end_date)


def generate_week_dates(start_date: str, weeks: int = 1) -> List[str]:
    """
    Generate dates for a specific number of weeks starting from start_date.

    Args:
        start_date: Start date in YYYY-MM-DD format
        weeks: Number of weeks to generate

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(weeks=weeks) - timedelta(days=1)
    end_date = end.strftime("%Y-%m-%d")

    return generate_date_range(start_date, end_date)


def generate_weekday_dates(
    start_date: str, end_date: str, weekdays: List[int] = None
) -> List[str]:
    """
    Generate dates for specific weekdays between start and end date.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        weekdays: List of weekday numbers (0=Monday, 6=Sunday).
                  Default is weekdays only (0-4)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    if weekdays is None:
        weekdays = [0, 1, 2, 3, 4]  # Monday to Friday

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        if current.weekday() in weekdays:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def generate_quarter_dates(year: int, quarter: int) -> List[str]:
    """
    Generate all dates for a specific quarter.

    Args:
        year: Year (e.g., 2025)
        quarter: Quarter (1-4)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    if quarter == 1:
        months = [1, 2, 3]
    elif quarter == 2:
        months = [4, 5, 6]
    elif quarter == 3:
        months = [7, 8, 9]
    elif quarter == 4:
        months = [10, 11, 12]
    else:
        raise ValueError("Quarter must be between 1 and 4")

    dates = []
    for month in months:
        dates.extend(generate_month_dates(year, month))

    return dates


def get_previous_week_dates() -> list[str]:
    """
    Get dates for the previous calendar week (Monday to Sunday).

    Returns:
        List of date strings in YYYY-MM-DD format for the previous week
    """
    now = datetime.now()
    # Get the start of the current week (Monday)
    days_since_monday = now.weekday()
    current_week_monday = now - timedelta(days=days_since_monday)
    # Previous week's Monday is 7 days before current week's Monday
    previous_week_monday = current_week_monday - timedelta(days=7)
    # Previous week's Sunday is 6 days after previous week's Monday
    previous_week_sunday = previous_week_monday + timedelta(days=6)

    start_date = previous_week_monday.strftime("%Y-%m-%d")
    end_date = previous_week_sunday.strftime("%Y-%m-%d")

    return generate_date_range(start_date, end_date)


def generate_year_dates(year: int) -> List[str]:
    """
    Generate all dates for a specific year.

    Args:
        year: Year (e.g., 2025)

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    return generate_date_range(f"{year}-01-01", f"{year}-12-31")


def get_business_days(start_date: str, end_date: str) -> List[str]:
    """
    Generate business days (Monday-Friday) between start and end date.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    return generate_weekday_dates(start_date, end_date, [0, 1, 2, 3, 4])


def get_weekends(start_date: str, end_date: str) -> List[str]:
    """
    Generate weekend days (Saturday-Sunday) between start and end date.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    return generate_weekday_dates(start_date, end_date, [5, 6])
