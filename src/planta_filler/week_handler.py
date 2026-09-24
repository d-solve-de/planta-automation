"""Week specification parsing and ISO week helpers.

A *week spec* is either a relative offset (``"0"`` current week, ``"-1"`` last
week, ``"2"`` two weeks ahead) or an absolute ISO week (``"2024-W05"``).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

_OFFSET_RE = re.compile(r"^[+-]?\d+$")
_ISO_WEEK_RE = re.compile(r"^(\d{4})-W(\d{1,2})$", re.IGNORECASE)


def parse_week_spec(week_spec: str, today: datetime | None = None) -> tuple[int, int]:
    """Return ``(iso_year, iso_week)`` for a week spec.

    ``today`` can be injected for deterministic tests.
    """
    today = today or datetime.now()
    spec = (week_spec or "").strip()

    if spec == "" or _OFFSET_RE.match(spec):
        offset = int(spec) if spec else 0
        target = today + timedelta(weeks=offset)
        iso = target.isocalendar()
        return iso[0], iso[1]

    match = _ISO_WEEK_RE.match(spec)
    if match:
        year, week = int(match.group(1)), int(match.group(2))
        if not 1 <= week <= 53:
            raise ValueError(f"Week number must be 1-53, got {week}")
        return year, week

    raise ValueError(f"Invalid week format: {week_spec!r}. Use YYYY-WNN or an offset like -1, 0, 1")


def parse_week_specs(spec_string: str) -> list[str]:
    """Split a comma-separated week list, validating each entry, preserving order."""
    specs = [part.strip() for part in spec_string.split(",") if part.strip()]
    if not specs:
        specs = ["0"]
    for spec in specs:
        parse_week_spec(spec)  # raises ValueError on bad input
    return specs


def get_monday_of_week(year: int, week: int) -> datetime:
    return datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u")


def get_week_dates(year: int, week: int) -> list[str]:
    """All seven dates (``YYYY-MM-DD``) of an ISO week, Monday first."""
    monday = get_monday_of_week(year, week)
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def week_offset_from_today(week_spec: str, today: datetime | None = None) -> int:
    """Number of weeks between the current week and the spec's week.

    Negative means the target week lies in the past.
    """
    today = today or datetime.now()
    iso = today.isocalendar()
    current_monday = get_monday_of_week(iso[0], iso[1])
    target_monday = get_monday_of_week(*parse_week_spec(week_spec, today))
    return (target_monday - current_monday).days // 7


def format_week_display(year: int, week: int) -> str:
    monday = get_monday_of_week(year, week)
    sunday = monday + timedelta(days=6)
    return f"Week {week}/{year} ({monday.strftime('%b %d')} - {sunday.strftime('%b %d')})"


def weekday_of(date_str: str) -> int:
    """0 = Monday ... 6 = Sunday for a ``YYYY-MM-DD`` string."""
    return datetime.strptime(date_str, "%Y-%m-%d").weekday()


def filter_dates_by_weekdays(dates: list[str], weekdays: list[int] | None) -> list[str]:
    """Keep only dates whose weekday is in ``weekdays`` (``None`` keeps all)."""
    if not weekdays:
        return list(dates)
    return [d for d in dates if weekday_of(d) in weekdays]
