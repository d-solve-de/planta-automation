# =============================================================================
# week_handler.py - Week Parsing and Navigation
# =============================================================================
# This module handles parsing of week specifications and provides utilities
# for working with ISO week numbers. It supports absolute week formats
# (YYYY-WNN) and relative offsets (-1 for last week, 0 for current, etc.)
#
# Main functions:
# - parse_week_spec(): Parses week specification string to (year, week) tuple
# - format_week_display(): Creates human-readable week display string
# - get_week_dates(): Returns list of date strings for all days in a week
# - get_monday_of_week(): Returns Monday datetime for given year/week
# =============================================================================

from datetime import datetime, timedelta
import re


def parse_week_spec(week_spec: str) -> tuple:
    if not week_spec or week_spec == "0":
        today = datetime.now()
        return today.isocalendar()[0], today.isocalendar()[1]
    
    if re.match(r'^-?\d+$', week_spec):
        offset = int(week_spec)
        target_date = datetime.now() + timedelta(weeks=offset)
        return target_date.isocalendar()[0], target_date.isocalendar()[1]
    
    match = re.match(r'^(\d{4})-W(\d{1,2})$', week_spec, re.IGNORECASE)
    if match:
        year = int(match.group(1))
        week = int(match.group(2))
        if not (1 <= week <= 53):
            raise ValueError(f"Week number must be 1-53, got {week}")
        return year, week
    
    raise ValueError(f"Invalid week format: {week_spec}. Use YYYY-WNN or offset (-1, 0, 1)")


def get_week_dates(year: int, week: int) -> list:
    first_day = datetime.strptime(f'{year}-W{week:02d}-1', '%G-W%V-%u')
    return [(first_day + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]


def get_monday_of_week(year: int, week: int) -> datetime:
    return datetime.strptime(f'{year}-W{week:02d}-1', '%G-W%V-%u')


def format_week_display(year: int, week: int) -> str:
    monday = get_monday_of_week(year, week)
    sunday = monday + timedelta(days=6)
    return f"Week {week}/{year} ({monday.strftime('%b %d')} - {sunday.strftime('%b %d')})"
