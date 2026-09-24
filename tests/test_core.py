from datetime import datetime

import pytest

from planta_filler import core
from planta_filler.browser import PlantaPage
from planta_filler.core import (
    RunOptions,
    export_visible_week,
    fill_visible_week,
    iter_weeks,
    open_timesheet,
    reset_visible_week,
    run,
)
from planta_filler.exceptions import LoginRequiredError, ReferenceFileError
from planta_filler.reference_handler import load_reference_week
from tests.conftest import FakeDriver, hours_element, target_element

MON, TUE = "2024-01-01", "2024-01-02"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(core.time, "sleep", lambda s: None)


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(core, "week_offset_from_today", lambda spec: core_week_offset(spec))


def core_week_offset(spec):
    from planta_filler.week_handler import week_offset_from_today

    return week_offset_from_today(spec, datetime(2024, 1, 3))


def two_day_driver():
    return FakeDriver(
        hours_elements=[
            hours_element(MON, "a", "0.0"),
            hours_element(MON, "b", "0.0"),
            hours_element(TUE, "c", "1.0"),
            hours_element(TUE, "d", "0.0"),
            hours_element(TUE, "e", "0.5"),
        ],
        target_elements=[target_element(MON, "Anwesend: 4,0 h"), target_element(TUE, "Anwesend: 3,0 h")],
    )


def test_fill_visible_week_equal_strategy():
    driver = two_day_driver()
    changes = fill_visible_week(PlantaPage(driver), RunOptions(url="u", strategy="equal", delay=0))
    assert changes == 4  # c already holds 1.0
    assert [e.value for e in driver.hours_elements[:2]] == ["2.0", "2.0"]
    assert [e.value for e in driver.hours_elements[2:]] == ["1.0", "1.0", "1.0"]


def test_fill_visible_week_respects_weekdays_and_excludes():
    driver = two_day_driver()
    options = RunOptions(url="u", strategy="equal", weekdays=[1], exclude_indices=[0], delay=0)
    fill_visible_week(PlantaPage(driver), options)
    assert [e.value for e in driver.hours_elements[:2]] == ["0.0", "0.0"]  # Monday untouched
    assert driver.hours_elements[2].value == "1.0"  # excluded row keeps its value
    assert [e.value for e in driver.hours_elements[3:]] == ["1.0", "1.0"]


def test_fill_visible_week_skips_days_without_target():
    driver = FakeDriver(hours_elements=[hours_element(MON, "a", "0.0")], target_elements=[target_element(MON, "0")])
    assert fill_visible_week(PlantaPage(driver), RunOptions(url="u", delay=0)) == 0


def test_fill_visible_week_copy_reference(tmp_path):
    ref = tmp_path / "ref.csv"
    ref.write_text(",Mo,Di\n1,3,1\n2,1,1\n3,0,0\n")
    driver = FakeDriver(
        hours_elements=[hours_element(MON, "a", "0"), hours_element(MON, "b", "0"), hours_element(MON, "c", "0")],
        target_elements=[target_element(MON, "8")],
    )
    options = RunOptions(url="u", strategy="copy_reference", reference_file=str(ref), delay=0)
    fill_visible_week(PlantaPage(driver), options, load_reference_week(ref))
    assert [e.value for e in driver.hours_elements] == ["6.0", "2.0", "0"]  # unchanged cell keeps its text


def test_fill_visible_week_copy_reference_falls_back_on_mismatch(tmp_path, caplog):
    ref = tmp_path / "ref.csv"
    ref.write_text(",Mo\n1,3\n")  # 1 row, PLANTA has 2
    driver = FakeDriver(
        hours_elements=[hours_element(MON, "a", "0"), hours_element(MON, "b", "0")],
        target_elements=[target_element(MON, "8")],
    )
    options = RunOptions(url="u", strategy="copy_reference", reference_file=str(ref), delay=0)
    fill_visible_week(PlantaPage(driver), options, load_reference_week(ref))
    assert [e.value for e in driver.hours_elements] == ["4.0", "4.0"]
    assert "falling back to equal" in caplog.text


def test_load_reference_handles_unusable_file(tmp_path, caplog):
    options = RunOptions(url="u", strategy="copy_reference", reference_file=str(tmp_path / "missing.csv"))
    assert core.load_reference(options) is None
    assert "falls back to equal" in caplog.text
    assert core.load_reference(RunOptions(url="u", strategy="equal")) is None
    assert core.load_reference(RunOptions(url="u", strategy="copy_reference")) is not None


def test_reset_visible_week_zeroes_non_excluded_cells():
    driver = FakeDriver(
        hours_elements=[
            hours_element(MON, "a", "1.25"),
            hours_element(MON, "b", "0.75"),
            hours_element(TUE, "c", "3.00"),
        ]
    )
    changes = reset_visible_week(PlantaPage(driver), RunOptions(url="u", exclude_indices=[1], delay=0))
    assert changes == 2
    assert [e.value for e in driver.hours_elements] == ["0.0", "0.75", "0.0"]


def test_iter_weeks_navigates_relative_to_current_week():
    driver = FakeDriver()
    page = PlantaPage(driver)
    assert list(iter_weeks(page, ["0", "-2", "1"])) == ["0", "-2", "1"]
    assert driver.back_clicks == 2
    assert driver.forward_clicks == 3


def test_open_timesheet_prompts_for_login_when_interactive(monkeypatch):
    driver = FakeDriver()
    page = PlantaPage(driver)
    prompts = []

    def fake_input(*_):
        prompts.append(1)
        driver.hours_elements.append(hours_element(MON, "a", "0"))
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setitem(core.SELECTORS["timeouts"], "presence_seconds", 0.05)
    monkeypatch.setitem(core.SELECTORS["timeouts"], "after_login_seconds", 0.5)
    open_timesheet(page, "https://example.com", interactive=True)
    assert prompts == [1]


def test_open_timesheet_fails_fast_when_not_interactive(monkeypatch):
    monkeypatch.setitem(core.SELECTORS["timeouts"], "presence_seconds", 0.05)
    with pytest.raises(LoginRequiredError, match="not logged in"):
        open_timesheet(PlantaPage(FakeDriver()), "https://example.com", interactive=False)


def test_export_visible_week(tmp_path):
    driver = two_day_driver()
    driver.hours_elements.pop()  # make Tuesday have 2 rows like Monday
    written = export_visible_week(PlantaPage(driver), tmp_path / "out" / "ref.csv")
    assert written.read_text().splitlines() == [",Mo,Di", "1,0.00,1.00", "2,0.00,0.00"]


def test_export_visible_week_errors():
    with pytest.raises(ReferenceFileError, match="nothing to export"):
        export_visible_week(PlantaPage(FakeDriver()), "x.csv")
    with pytest.raises(ReferenceFileError, match="different numbers"):
        export_visible_week(PlantaPage(two_day_driver()), "x.csv")


def test_run_fills_multiple_weeks_and_waits(monkeypatch):
    driver = two_day_driver()
    options = RunOptions(url="https://example.com", week_specs=["0", "-1"], delay=0, close_delay=0)
    total = run(driver, options)
    assert driver.visited == ["https://example.com"]
    assert driver.back_clicks == 1
    assert total >= 4


def test_run_export_requires_single_week(tmp_path):
    options = RunOptions(url="u", week_specs=["0", "-1"], export_reference=str(tmp_path / "x.csv"))
    with pytest.raises(ReferenceFileError, match="exactly one week"):
        run(two_day_driver(), options)


def test_run_export_writes_file(tmp_path):
    driver = two_day_driver()
    driver.hours_elements.pop()
    out = tmp_path / "x.csv"
    assert run(driver, RunOptions(url="u", export_reference=str(out))) == 0
    assert out.exists()


def test_wait_before_close_counts_down(monkeypatch):
    sleeps = []
    monkeypatch.setattr(core.time, "sleep", lambda s: sleeps.append(s))
    core.wait_before_close(3)
    core.wait_before_close(0)
    assert sleeps == [1, 1, 1]


def test_run_login_only_changes_nothing():
    driver = two_day_driver()
    assert run(driver, RunOptions(url="u", login_only=True)) == 0
    assert all(e.send_keys_calls == 0 for e in driver.hours_elements)
