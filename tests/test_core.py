from datetime import datetime

import types

from planta_filler.core import (
    get_target_hours_per_day,
    get_hours_per_day,
    filter_dates_by_weekdays,
    set_week,
    reset_week,
)
from planta_filler.config import SELECTORS
from planta_filler.week_handler import parse_week_spec


class FakeElement:
    def __init__(self, id=None, value="", class_attr="", text=""):
        self._id = id
        self.value = value
        self._class = class_attr
        self.text = text
        self.update_calls = 0
        self.clears = 0

    def get_attribute(self, name):
        if name == "id":
            return self._id
        if name == "class":
            return self._class
        return None

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def clear(self):
        self.clears += 1
        self.value = ""

    def send_keys(self, s):
        self.update_calls += 1
        self.value = str(s)


class FakeDriver:
    def __init__(self, hours_elements, target_elements):
        self.hours_elements = hours_elements
        self.target_elements = target_elements
        # index by id for quick lookup in set_week()
        self._by_id = {e._id: e for e in hours_elements if e._id}
        self.last_url = None
        # navigation support
        self.clicks = {SELECTORS['navigation']['week_back']: 0, SELECTORS['navigation']['week_forward']: 0}

    def get(self, url):
        self.last_url = url

    def quit(self):
        pass

    def find_elements(self, by, selector):
        if selector == SELECTORS['selectors']['hours_input']:
            return self.hours_elements
        if selector == SELECTORS['selectors']['target_hours_div']:
            return self.target_elements
        return []

    def find_element(self, by, sel_or_id):
        # Ignore 'by' in the fake driver; decide based on the selector/id value.
        # If sel_or_id matches a known navigation CSS selector, return a clickable stub.
        if isinstance(sel_or_id, str) and sel_or_id in self.clicks:
            return Clickable(self.clicks, sel_or_id)
        # Otherwise, treat sel_or_id as an element ID.
        return self._by_id[sel_or_id]

    def execute_script(self, script, element):
        # Only used as: "return arguments[0].value;"
        return element.value


class DummyWait:
    def __init__(self, driver, timeout):
        self.driver = driver
        self.timeout = timeout

    def until(self, condition):
        return True


def make_target_element(date_str, hours_text):
    # date_str in YYYY-MM-DD; core expects class with att-YYYYMMDD
    ymd = date_str.replace("-", "")
    return FakeElement(class_attr=f"something att-{ymd} other", text=hours_text)


def make_hours_element(field_id, val):
    return FakeElement(id=field_id, value=str(val))


def test_get_target_hours_per_day_parses_values(monkeypatch):
    date = "2024-01-01"
    # text may contain commas; function replaces with dot and extracts first number
    target_elems = [
        make_target_element(date, "Anwesend: 8,0 h"),
        # unrelated element without matching class won't be used
        FakeElement(class_attr="no-att", text="5,0 h"),
    ]
    driver = FakeDriver(hours_elements=[], target_elements=target_elems)
    res = get_target_hours_per_day(driver)
    assert res == {date: 8.0}


def test_get_hours_per_day_groups_by_date():
    date1 = "2024-01-01"
    date2 = "2024-01-02"
    hours_elems = [
        make_hours_element(f"load-field-xxx-{date1}", "1.0"),
        make_hours_element(f"load-field-yyy-{date1}", ""),  # blank -> 0.0
        make_hours_element(f"load-field-zzz-{date2}", "2.5"),
    ]
    driver = FakeDriver(hours_elements=hours_elems, target_elements=[])
    res = get_hours_per_day(driver)
    assert set(res.keys()) == {date1, date2}
    assert res[date1][0][0].endswith(date1)
    assert [v for _, v in res[date1]] == [1.0, 0.0]
    assert [v for _, v in res[date2]] == [2.5]


def test_filter_dates_by_weekdays():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]  # Tue, Wed, Thu
    # Select Wednesday only (2)
    filtered = filter_dates_by_weekdays(dates, [2])
    # Map to ISO weekday numbers to confirm
    assert [datetime.strptime(d, "%Y-%m-%d").weekday() for d in filtered] == [2]


class Clickable:
    def __init__(self, clicks_store, key):
        self._store = clicks_store
        self._key = key

    def click(self):
        self._store[self._key] += 1


def test_set_week_applies_changes_equal_strategy(monkeypatch):
    # Monkeypatch WebDriverWait to avoid waiting
    from planta_filler import core as core_mod
    monkeypatch.setattr(core_mod, "WebDriverWait", DummyWait)
    monkeypatch.setattr(core_mod, "_assert_planta_pulse_title", lambda d: None)

    date1 = "2024-01-01"
    date2 = "2024-01-02"

    hours_elems = [
        # date1: two slots, both 0 -> expect both set to 2.0 when target is 4.0
        make_hours_element(f"load-field-a-{date1}", "0.0"),
        make_hours_element(f"load-field-b-{date1}", "0.0"),
        # date2: three slots, current values 1.0, 0.0, 0.5 -> expect to set to 1.0 each (target 3.0)
        make_hours_element(f"load-field-c-{date2}", "1.0"),
        make_hours_element(f"load-field-d-{date2}", "0.0"),
        make_hours_element(f"load-field-e-{date2}", "0.5"),
    ]

    target_elems = [
        make_target_element(date1, "Anwesend: 4,0 h"),
        make_target_element(date2, "Anwesend: 3,0 h"),
    ]

    driver = FakeDriver(hours_elements=hours_elems, target_elements=target_elems)

    # Run set_week in override mode (skip_login_prompt=True) to avoid input waiting, and with zero delays
    set_week(
        driver,
        url="https://example.com",
        strategy="equal",
        weekdays=None,
        skip_login_prompt=True,
        delay=0.0,
        close_delay=0.0,
        post_randomization=0.0,
        week_specs=["0"],
    )

    # Count updates applied via send_keys across all elements
    total_updates = sum(e.update_calls for e in hours_elems)
    # date1: 2 updates; date2: 2 updates (elements d and e), element c remains ~1.0
    assert total_updates == 4
    # Verify final values reflect the strategy results
    # date1 -> [2.0, 2.0]
    assert [e.value for e in hours_elems[:2]] == ["2.0", "2.0"]
    # date2 -> [1.0, 1.0, 1.0]
    assert [e.value for e in hours_elems[2:]] == ["1.0", "1.0", "1.0"]


def test_reset_week_sets_zero_values(monkeypatch):
    # Monkeypatch WebDriverWait and input to avoid waiting
    from planta_filler import core as core_mod
    monkeypatch.setattr(core_mod, "WebDriverWait", DummyWait)
    monkeypatch.setattr(core_mod, "_assert_planta_pulse_title", lambda d: None)
    # Patch builtins.input used in reset_week
    import builtins
    monkeypatch.setattr(builtins, "input", lambda *args, **kwargs: "")

    date1 = "2024-01-01"
    date2 = "2024-01-02"
    hours_elems = [
        make_hours_element(f"load-field-a-{date1}", "1.25"),
        make_hours_element(f"load-field-b-{date1}", "0.75"),
        make_hours_element(f"load-field-c-{date2}", "3.00"),
    ]
    driver = FakeDriver(hours_elements=hours_elems, target_elements=[])

    reset_week(
        driver,
        url="https://example.com",
        weekdays=None,
        delay=0.0,
        close_delay=0.0,
    )

    # All elements should be set to '0'
    assert [e.value for e in hours_elems] == ["0", "0", "0"]
    # And send_keys should have been called for each element
    assert sum(e.update_calls for e in hours_elems) == 3


def test_set_week_multiple_specs_navigate_and_fill(monkeypatch):
    # Monkeypatch WebDriverWait to avoid waiting
    from planta_filler import core as core_mod
    monkeypatch.setattr(core_mod, "WebDriverWait", DummyWait)
    monkeypatch.setattr(core_mod, "_assert_planta_pulse_title", lambda d: None)

    # Prepare hours/targets; same DOM used for both weeks in our fake driver
    dateA = "2024-01-01"
    dateB = "2024-01-02"

    hours_elems = [
        make_hours_element(f"load-field-a-{dateA}", "0.0"),
        make_hours_element(f"load-field-b-{dateA}", "0.0"),
        make_hours_element(f"load-field-c-{dateB}", "0.0"),
    ]

    target_elems = [
        make_target_element(dateA, "Anwesend: 2,0 h"),
        make_target_element(dateB, "Anwesend: 1,0 h"),
    ]

    driver = FakeDriver(hours_elements=hours_elems, target_elements=target_elems)

    # Week specs include current (0) and previous (-1); the code should click back arrow once to move to previous week
    set_week(
        driver,
        url="https://example.com",
        strategy="equal",
        weekdays=None,
        skip_login_prompt=True,
        delay=0.0,
        close_delay=0.0,
        post_randomization=0.0,
        week_specs=["0", "-1"],
    )

    # Verify that navigation clicked 1 time to go to the previous week
    assert driver.clicks[SELECTORS['navigation']['week_back']] == 1
    # And elements were filled twice (once per week). In this fake environment, we see cumulative updates
    assert sum(e.update_calls for e in hours_elems) >= 3
