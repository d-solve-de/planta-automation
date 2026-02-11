from datetime import datetime, timedelta

import pytest

from planta_filler.week_handler import (
    parse_week_spec,
    get_week_dates,
    get_monday_of_week,
    format_week_display,
)


def test_parse_week_spec_current_week_when_zero():
    year, week = parse_week_spec("0")
    now = datetime.now()
    assert (year, week) == (now.isocalendar()[0], now.isocalendar()[1])


def test_parse_week_spec_go_one_week_back():
    # "go one week back" should map to the ISO week of today - 7 days
    year, week = parse_week_spec("-1")
    target = datetime.now() + timedelta(weeks=-1)
    assert (year, week) == (target.isocalendar()[0], target.isocalendar()[1])


def test_parse_week_spec_absolute_and_invalid():
    assert parse_week_spec("2024-W01") == (2024, 1)
    with pytest.raises(ValueError):
        parse_week_spec("2024-W54")
    with pytest.raises(ValueError):
        parse_week_spec("not-a-week")


def test_get_week_dates_and_monday_alignment():
    year, week = 2024, 10
    dates = get_week_dates(year, week)
    # Should return 7 entries starting on Monday
    assert len(dates) == 7
    monday = get_monday_of_week(year, week)
    assert dates[0] == monday.strftime("%Y-%m-%d")
    assert dates[-1] == (monday + timedelta(days=6)).strftime("%Y-%m-%d")


def test_format_week_display_contains_expected_range():
    year, week = 2024, 10
    display = format_week_display(year, week)
    monday = get_monday_of_week(year, week)
    sunday = monday + timedelta(days=6)
    assert str(week) in display and str(year) in display
    assert monday.strftime("%b %d") in display
    assert sunday.strftime("%b %d") in display
