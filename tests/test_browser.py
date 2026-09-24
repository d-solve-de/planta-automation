import pytest

from planta_filler.browser import PlantaPage, end_driver
from planta_filler.config import SELECTORS
from planta_filler.exceptions import BrowserError
from tests.conftest import FakeDriver, hours_element, target_element


def test_check_title_accepts_and_rejects():
    PlantaPage(FakeDriver(title="PLANTA Pulse - Home")).check_title()
    with pytest.raises(BrowserError, match="VPN"):
        PlantaPage(FakeDriver(title="Some Other App")).check_title()
    with pytest.raises(BrowserError):
        PlantaPage(FakeDriver(title="")).check_title()


def test_open_visits_url_and_checks_title():
    driver = FakeDriver()
    PlantaPage(driver).open("https://example.com")
    assert driver.visited == ["https://example.com"]


def test_read_target_hours_parses_german_numbers():
    driver = FakeDriver(
        target_elements=[target_element("2024-01-01", "Anwesend: 8,5 h"), target_element("2024-01-02", "")]
    )
    driver.target_elements.append(hours_element("2024-01-01", "x", 1))  # no att- class, ignored
    assert PlantaPage(driver).read_target_hours() == {"2024-01-01": 8.5}


def test_read_hours_groups_by_date_and_handles_blank_and_comma():
    driver = FakeDriver(
        hours_elements=[
            hours_element("2024-01-01", "a", "1.0"),
            hours_element("2024-01-01", "b", ""),
            hours_element("2024-01-02", "c", "2,5"),
            hours_element("2024-01-02", "d", "abc"),
        ]
    )
    driver.hours_elements.append(target_element("2024-01-03", "x"))  # no id, ignored
    hours = PlantaPage(driver).read_hours()
    assert list(hours) == ["2024-01-01", "2024-01-02"]
    assert [f.value for f in hours["2024-01-01"]] == [1.0, 0.0]
    assert [f.value for f in hours["2024-01-02"]] == [2.5, 0.0]
    assert hours["2024-01-01"][0].field_id == "load-field-a-2024-01-01"


def test_write_hours_types_and_blurs():
    element = hours_element("2024-01-01", "a", "1.0")
    driver = FakeDriver(hours_elements=[element])
    assert PlantaPage(driver).write_hours(element.element_id, 2.5) is True
    assert element.value == "2.5"
    assert element.send_keys_calls == 1


def test_wait_for_timesheet_true_and_false():
    assert PlantaPage(FakeDriver(hours_elements=[hours_element("2024-01-01", "a", 0)])).wait_for_timesheet(0.1)
    assert PlantaPage(FakeDriver()).wait_for_timesheet(0.1) is False


def test_go_weeks_clicks_the_right_arrow():
    driver = FakeDriver()
    page = PlantaPage(driver)
    page.go_weeks(-2)
    page.go_weeks(1)
    page.go_weeks(0)
    assert driver.back_clicks == 2
    assert driver.forward_clicks == 1


def test_end_driver_swallows_errors():
    class Broken:
        def quit(self):
            raise RuntimeError("boom")

    end_driver(Broken())


def test_go_weeks_falls_back_to_javascript_click():
    from selenium.common.exceptions import ElementClickInterceptedException

    driver = FakeDriver()
    scripts = []

    class Covered:
        def click(self):
            raise ElementClickInterceptedException("overlay")

    driver.nav[SELECTORS["navigation"]["week_back"]] = Covered()
    driver.execute_script = lambda script, element: scripts.append((script, element))
    PlantaPage(driver).go_weeks(-1)
    assert len(scripts) == 1 and "click()" in scripts[0][0]


def test_wait_for_any_date():
    page = PlantaPage(FakeDriver(hours_elements=[hours_element("2024-01-02", "a", 0)]))
    assert page.wait_for_any_date(["2024-01-01", "2024-01-02"], 0.1) is True
    assert page.wait_for_any_date(["2024-01-08"], 0.1) is False
