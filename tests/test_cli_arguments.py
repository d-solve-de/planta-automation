import sys
import types
import pytest

from planta_filler import cli as cli_mod


def run_cli(argv):
    # Simulate calling CLI main() with given args
    sys.argv = ["planta_filler"] + argv
    # Monkeypatch start/end driver and core.set_week/reset_week to avoid real browser
    called = {
        "set_week": None,
        "reset_week": None,
    }

    class DummyDriver:
        pass

    def fake_start_driver(**kwargs):
        return DummyDriver()

    def fake_end_driver(driver):
        return None

    def fake_set_week(driver, url, strategy, weekdays, skip_login_prompt, delay, close_delay, post_randomization, week_specs, reference_day=None, reference_file=None, exclude_indices=None):
        called["set_week"] = dict(
            url=url,
            strategy=strategy,
            weekdays=weekdays,
            skip_login_prompt=skip_login_prompt,
            delay=delay,
            close_delay=close_delay,
            post_randomization=post_randomization,
            week_specs=week_specs,
            reference_day=reference_day,
            reference_file=reference_file,
            exclude_indices=exclude_indices,
        )

    def fake_reset_week(driver, url, weekdays, delay, close_delay, skip_login_prompt=False, week_specs=None, exclude_indices=None):
        called["reset_week"] = dict(url=url, weekdays=weekdays, delay=delay, close_delay=close_delay, skip_login_prompt=skip_login_prompt, week_specs=week_specs, exclude_indices=exclude_indices)

    # Apply monkeypatches
    cli_mod.start_driver = fake_start_driver
    cli_mod.end_driver = fake_end_driver
    cli_mod.set_week = fake_set_week
    cli_mod.reset_week = fake_reset_week

    # Run
    cli_mod.main()
    return called


def test_cli_parses_multiple_weeks_and_post_randomization(monkeypatch):
    called = run_cli([
        "--url", "https://example.com",
        "--strategy", "equal",
        "--week=0,-1",
        "--post-randomization", "0.2",
        "--weekdays", "0,2,4",
        "--close-delay", "0",
        "--delay", "0",
        "--headless",
        "--persistent",
    ])

    assert called["set_week"] is not None
    args = called["set_week"]
    assert args["week_specs"] == ["0", "-1"]
    assert pytest.approx(args["post_randomization"], rel=1e-9) == 0.2
    assert args["weekdays"] == [0, 2, 4]


def test_cli_reset_mode(monkeypatch):
    called = run_cli([
        "--url", "https://example.com",
        "--reset",
        "--weekdays", "1,3",
        "--close-delay", "0",
        "--delay", "0",
    ])

    assert called["reset_week"] is not None
    args = called["reset_week"]
    assert args["url"] == "https://example.com"
    assert args["weekdays"] == [1, 3]
