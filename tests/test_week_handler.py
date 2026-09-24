from datetime import datetime, timedelta

import pytest

from planta_filler.week_handler import (
    filter_dates_by_weekdays,
    format_week_display,
    get_monday_of_week,
    get_week_dates,
    parse_week_spec,
    parse_week_specs,
    week_offset_from_today,
    weekday_of,
)

TODAY = datetime(2024, 3, 6)  # a Wednesday in ISO week 10


def test_parse_week_spec_offsets():
    assert parse_week_spec("0", TODAY) == (2024, 10)
    assert parse_week_spec("", TODAY) == (2024, 10)
    assert parse_week_spec("-1", TODAY) == (2024, 9)
    assert parse_week_spec("+2", TODAY) == (2024, 12)
    assert parse_week_spec("-10", TODAY) == (2023, 52)


def test_parse_week_spec_uses_today_by_default():
    now = datetime.now()
    assert parse_week_spec("0") == (now.isocalendar()[0], now.isocalendar()[1])


def test_parse_week_spec_absolute_and_invalid():
    assert parse_week_spec("2024-W01") == (2024, 1)
    assert parse_week_spec("2024-w5") == (2024, 5)
    with pytest.raises(ValueError):
        parse_week_spec("2024-W54")
    with pytest.raises(ValueError):
        parse_week_spec("not-a-week")


def test_parse_week_specs_preserves_order():
    assert parse_week_specs("0,-1,2024-W05") == ["0", "-1", "2024-W05"]
    assert parse_week_specs(" ") == ["0"]
    with pytest.raises(ValueError):
        parse_week_specs("0,x")


def test_week_offset_from_today():
    assert week_offset_from_today("0", TODAY) == 0
    assert week_offset_from_today("-3", TODAY) == -3
    assert week_offset_from_today("2024-W12", TODAY) == 2
    assert week_offset_from_today("2023-W52", TODAY) == -10


def test_get_week_dates_and_monday_alignment():
    dates = get_week_dates(2024, 10)
    monday = get_monday_of_week(2024, 10)
    assert monday == datetime(2024, 3, 4)
    assert len(dates) == 7
    assert dates[0] == "2024-03-04"
    assert dates[-1] == (monday + timedelta(days=6)).strftime("%Y-%m-%d")


def test_format_week_display():
    assert format_week_display(2024, 10) == "Week 10/2024 (Mar 04 - Mar 10)"


def test_weekday_filters():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]  # Mon, Tue, Wed
    assert weekday_of("2024-01-03") == 2
    assert filter_dates_by_weekdays(dates, [2]) == ["2024-01-03"]
    assert filter_dates_by_weekdays(dates, None) == dates
    assert filter_dates_by_weekdays(dates, []) == dates
