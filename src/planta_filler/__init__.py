# =============================================================================
# planta_filler - PLANTA Timesheet Automation
# =============================================================================
# This package automates filling timesheets in PLANTA by distributing working
# hours across tasks using configurable strategies. It uses Selenium to control
# Firefox and can run headlessly or with visible browser UI.
#
# Main entry point: python3 -m planta_filler
# =============================================================================

__version__ = "1.0.0"
__author__ = "PLANTA Automation Team"

from .core import start_driver, end_driver, set_week, reset_week
from .calculations import fill_day
from .strategies import strategies
from .config import (
    DEFAULT_URL, DEFAULT_STRATEGY, DEFAULT_WEEKDAYS,
    DEFAULT_DELAY, DEFAULT_CLOSE_DELAY, VALID_STRATEGIES
)
