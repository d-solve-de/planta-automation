"""planta_filler - automatic timesheet filling for PLANTA Pulse.

The package drives Firefox through Selenium, reads the attendance hours of
every day and distributes them over the task rows with a chosen strategy.

Command line: ``planta-filler --url https://planta.example.com/`` or
``python3 -m planta_filler ...``. See :mod:`planta_filler.cli`.

Programmatic use::

    from planta_filler import RunOptions, run, start_driver, end_driver

    driver = start_driver(headless=False)
    try:
        run(driver, RunOptions(url="https://planta.example.com/", strategy="equal"))
    finally:
        end_driver(driver)
"""

__version__ = "0.2.0"
__author__ = "Felix Paul"

from .browser import PlantaPage, end_driver, start_driver
from .calculations import fill_day
from .core import RunOptions, run
from .exceptions import (
    BrowserError,
    LoginRequiredError,
    PlantaFillerError,
    ReferenceFileError,
    ValidationError,
)
from .strategies import STRATEGIES

__all__ = [
    "STRATEGIES",
    "BrowserError",
    "LoginRequiredError",
    "PlantaFillerError",
    "PlantaPage",
    "ReferenceFileError",
    "RunOptions",
    "ValidationError",
    "__version__",
    "end_driver",
    "fill_day",
    "run",
    "start_driver",
]
