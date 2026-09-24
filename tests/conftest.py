"""Shared fixtures: an in-memory fake of the PLANTA page for browser-free tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from planta_filler.config import SELECTORS  # noqa: E402


class FakeElement:
    def __init__(self, element_id=None, value="", class_attr="", text=""):
        self.element_id = element_id
        self.value = value
        self.class_attr = class_attr
        self.text = text
        self.send_keys_calls = 0
        self.clicks = 0

    def get_attribute(self, name):
        return {"id": self.element_id, "class": self.class_attr}.get(name)

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def clear(self):
        self.value = ""

    def send_keys(self, text):
        self.send_keys_calls += 1
        self.value = str(text)

    def click(self):
        self.clicks += 1


class FakeDriver:
    """Just enough of the WebDriver API for PlantaPage."""

    def __init__(self, hours_elements=(), target_elements=(), title="PLANTA Pulse - Zeiterfassung"):
        self.hours_elements = list(hours_elements)
        self.target_elements = list(target_elements)
        self.title = title
        self.by_id = {e.element_id: e for e in self.hours_elements if e.element_id}
        self.nav = {
            SELECTORS["navigation"]["week_back"]: FakeElement(),
            SELECTORS["navigation"]["week_forward"]: FakeElement(),
        }
        self.visited = []
        self.quit_called = False

    def get(self, url):
        self.visited.append(url)

    def quit(self):
        self.quit_called = True

    def find_elements(self, by, selector):
        if selector == SELECTORS["selectors"]["hours_input"]:
            return self.hours_elements
        if selector == SELECTORS["selectors"]["target_hours_div"]:
            return self.target_elements
        return []

    def find_element(self, by, selector):
        if selector in self.nav:
            return self.nav[selector]
        if selector == SELECTORS["selectors"]["hours_input"] and self.hours_elements:
            return self.hours_elements[0]
        if selector in self.by_id:
            return self.by_id[selector]
        from selenium.common.exceptions import NoSuchElementException

        raise NoSuchElementException(selector)

    def execute_script(self, script, element):
        return element.value

    @property
    def back_clicks(self):
        return self.nav[SELECTORS["navigation"]["week_back"]].clicks

    @property
    def forward_clicks(self):
        return self.nav[SELECTORS["navigation"]["week_forward"]].clicks


def hours_element(date, name, value):
    return FakeElement(element_id=f"load-field-{name}-{date}", value=str(value))


def target_element(date, hours_text):
    return FakeElement(class_attr=f"load att-{date.replace('-', '')}", text=hours_text)


@pytest.fixture
def fake_driver_factory():
    return FakeDriver


@pytest.fixture
def make_hours_element():
    return hours_element


@pytest.fixture
def make_target_element():
    return target_element
