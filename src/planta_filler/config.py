"""Central configuration: defaults, limits and PLANTA DOM selectors.

Every tunable value lives here so behaviour can be changed without touching
the logic modules. The CLI reads the ``DEFAULT_*`` values for its argument
defaults, the browser layer reads ``SELECTORS``.
"""

from __future__ import annotations

from pathlib import Path

# --- Paths -----------------------------------------------------------------

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
DEFAULT_REFERENCE_FILE = str(DATA_DIR / "default_reference.csv")
MAN_PAGE_FILE = DATA_DIR / "man_page.txt"
PROFILE_DIR = Path.home() / ".selenium_profiles" / "planta_firefox"

# --- CLI defaults ------------------------------------------------------------

DEFAULT_URL = ""
DEFAULT_STRATEGY = "equal"
DEFAULT_WEEKDAYS = [0, 1, 2, 3, 4]  # Monday .. Friday
DEFAULT_WEEK = "0"  # current ISO week
DEFAULT_DELAY = 0.2  # seconds between two field updates
DEFAULT_CLOSE_DELAY = 10.0  # seconds the browser stays open after the run
DEFAULT_USE_PERSISTENT_PROFILE = True
DEFAULT_HEADLESS = False
DEFAULT_POST_RANDOMIZATION = 0.0
DEFAULT_PRECISION = 2  # decimals PLANTA accepts in an hours field
DEFAULT_RETRIES = 5  # attempts for the random strategy before giving up

# --- Validation limits -----------------------------------------------------

VALID_STRATEGIES = ["equal", "random", "copy_reference"]
VALID_WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]
MIN_DELAY = 0.0
MAX_DELAY = 60.0
MAX_PRECISION = 10

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# --- Browser / DOM ---------------------------------------------------------

# Substring expected in the page title once the correct PLANTA instance is open.
EXPECTED_TITLE_SUBSTRING = "planta pulse"

SELECTORS = {
    "selectors": {
        # One input per task row and day; its id ends with the ISO date.
        "hours_input": "input.load-input",
        # Per-day box carrying the attendance ("Anwesend") hours; the date is
        # encoded in a class named ``att-YYYYMMDD``.
        "target_hours_div": 'div.load[class*="att-"]',
    },
    "patterns": {
        "date_attr_regex": r"att-(\d{8})",
        "field_id_date_regex": r"(\d{4}-\d{2}-\d{2})$",
    },
    "timeouts": {
        # Seconds to wait for the timesheet inputs after opening the URL.
        "presence_seconds": 10,
        # Seconds to wait for the inputs after the user confirmed a manual login.
        "after_login_seconds": 60,
        # Seconds to wait for the inputs of the target week after clicking a week arrow.
        "navigation_seconds": 10,
    },
    "navigation": {
        # These arrows move the visible timesheet by one whole week.
        "week_back": "i.fas.fa-chevron-left",
        "week_forward": "i.fas.fa-chevron-right",
    },
}
