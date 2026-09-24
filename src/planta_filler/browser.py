"""Everything that talks to Selenium and the PLANTA DOM.

:func:`start_driver` / :func:`end_driver` manage the Firefox process.
:class:`PlantaPage` wraps a WebDriver and exposes the handful of operations
the workflow needs (read hours, write a field, move by a week). All CSS
selectors come from :data:`planta_filler.config.SELECTORS`, so a PLANTA UI
change should only require edits there.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import EXPECTED_TITLE_SUBSTRING, PROFILE_DIR, SELECTORS
from .exceptions import BrowserError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class HourField:
    """One hours input cell: its DOM id and the value currently shown."""

    field_id: str
    value: float


def start_driver(
    headless: bool = False,
    use_persistent_profile: bool = True,
    profile_dir: Path | str = PROFILE_DIR,
):
    """Start Firefox. With a persistent profile the login survives between runs."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    if use_persistent_profile:
        profile_path = Path(profile_dir).expanduser()
        profile_path.mkdir(parents=True, exist_ok=True)
        options.add_argument("-profile")
        options.add_argument(str(profile_path))
        log.debug("Using Firefox profile %s", profile_path)
    try:
        return webdriver.Firefox(options=options)
    except WebDriverException as exc:
        raise BrowserError(
            "Could not start Firefox. Make sure Firefox and geckodriver are installed "
            f"and geckodriver is on your PATH. Original error: {exc.msg or exc}"
        ) from exc


def end_driver(driver) -> None:
    try:
        driver.quit()
    except Exception:
        log.debug("Ignoring error while closing the browser", exc_info=True)


def _to_float(raw: object) -> float:
    text = str(raw or "").strip().replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        log.warning("Could not parse hours value %r, treating it as 0", raw)
        return 0.0


class PlantaPage:
    """High-level access to the PLANTA timesheet currently shown in ``driver``."""

    def __init__(self, driver, selectors: dict = SELECTORS):
        self.driver = driver
        self.selectors = selectors

    # --- navigation -----------------------------------------------------------

    def open(self, url: str) -> None:
        self.driver.get(url)
        self.check_title()

    def check_title(self) -> None:
        title = (getattr(self.driver, "title", "") or "").lower()
        if EXPECTED_TITLE_SUBSTRING not in title:
            raise BrowserError(
                f"The page title {title!r} does not look like PLANTA Pulse. "
                "Check the URL and make sure you are connected to the VPN if one is required."
            )

    def wait_for_timesheet(self, timeout: float) -> bool:
        """Return True once the hours inputs are present, False on timeout."""
        locator = (By.CSS_SELECTOR, self.selectors["selectors"]["hours_input"])
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            return False
        return True

    def wait_for_any_date(self, dates: Sequence[str], timeout: float) -> bool:
        """Return True once an hours input for one of ``dates`` (``YYYY-MM-DD``) exists."""
        base = self.selectors["selectors"]["hours_input"]
        selector = ", ".join(f"{base}[id$='{date}']" for date in dates)
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            return False
        return True

    def go_weeks(self, delta: int) -> None:
        """Move the visible week by ``delta`` weeks (negative = into the past)."""
        if delta == 0:
            return
        key = "week_forward" if delta > 0 else "week_back"
        selector = self.selectors["navigation"][key]
        for _ in range(abs(delta)):
            arrow = self.driver.find_element(By.CSS_SELECTOR, selector)
            try:
                arrow.click()
            except WebDriverException:
                # The icon can be covered by an overlay; a JavaScript click still reaches it.
                log.debug("Native click on %s failed, using JavaScript click", selector, exc_info=True)
                self.driver.execute_script("arguments[0].click();", arrow)

    # --- reading --------------------------------------------------------------

    def read_target_hours(self) -> dict[str, float]:
        """Attendance hours per date (``YYYY-MM-DD``) taken from the day header boxes."""
        date_regex = re.compile(self.selectors["patterns"]["date_attr_regex"])
        result: dict[str, float] = {}
        for div in self.driver.find_elements(By.CSS_SELECTOR, self.selectors["selectors"]["target_hours_div"]):
            match = date_regex.search(div.get_attribute("class") or "")
            if not match:
                continue
            raw = match.group(1)
            date = f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
            numbers = re.findall(r"\d+\.?\d*", (div.text or "").replace(",", "."))
            if numbers:
                result[date] = float(numbers[0])
        return result

    def read_hours(self) -> dict[str, list[HourField]]:
        """Current values of every hours input, grouped by date in DOM order."""
        id_regex = re.compile(self.selectors["patterns"]["field_id_date_regex"])
        result: dict[str, list[HourField]] = {}
        for element in self.driver.find_elements(By.CSS_SELECTOR, self.selectors["selectors"]["hours_input"]):
            field_id = element.get_attribute("id") or ""
            match = id_regex.search(field_id)
            if not match:
                continue
            value = self.driver.execute_script("return arguments[0].value;", element)
            result.setdefault(match.group(1), []).append(HourField(field_id, _to_float(value)))
        return result

    # --- writing --------------------------------------------------------------

    def write_hours(self, field_id: str, value: float | str) -> bool:
        """Type ``value`` into a field and blur it so PLANTA saves it. Returns False if not editable."""
        field = self.driver.find_element(By.ID, field_id)
        if not (field.is_displayed() and field.is_enabled()):
            log.warning("Field %s is not editable, skipping", field_id)
            return False
        field.clear()
        field.send_keys(str(value))
        self.driver.execute_script("arguments[0].blur();", field)
        return True
