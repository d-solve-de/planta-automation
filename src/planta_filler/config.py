# =============================================================================
# config.py - Central Configuration for PLANTA Filler
# =============================================================================
# This module is the single source of truth for all default configuration
# values used throughout the application. Modify these values to change
# default behavior without touching the code.
#
# Configuration includes:
# - PLANTA URL and connection settings
# - Distribution strategy defaults
# - Browser automation timing
# - CSS selectors for PLANTA DOM elements
# =============================================================================

from pathlib import Path

DEFAULT_URL = ''
DEFAULT_STRATEGY = 'random'
DEFAULT_WEEKDAYS = [0, 1, 2, 3, 4]
DEFAULT_DELAY = 0.2
DEFAULT_CLOSE_DELAY = 10.0
DEFAULT_USE_PERSISTENT_PROFILE = True
DEFAULT_HEADLESS = False
# Absolute path to the packaged default reference CSV (whole-week format)
DEFAULT_REFERENCE_FILE = str((Path(__file__).parent / 'data' / 'default_reference.csv').resolve())
DEFAULT_EXCLUDE_VALUES = []
DEFAULT_PRECISION = 2
DEFAULT_RETRIES = 5
DEFAULT_POST_RANDOMIZATION = 0.0
VALID_STRATEGIES = ['random', 'equal', 'copy_reference']
VALID_WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]
MAX_DELAY = 60.0
MIN_DELAY = 0.0

SELECTORS = {
    'selectors': {
        'hours_input': 'input.load-input',
        'target_hours_div': 'div.load[class*="att-"]',
    },
    'patterns': {
        'date_attr_regex': r'att-(\d{8})',
    },
    'timeouts': {
        'presence_seconds': 10,
    },
    'navigation': {
        # These arrows navigate by whole weeks in PLANTA
        'week_back': 'i.fas.fa-chevron-left',
        'week_forward': 'i.fas.fa-chevron-right',
        'today_button': 'div.label:contains("Heute")',
        # Date picker input to validate visible week
        'week_picker_input': 'a.date-picker-input input.flatpickr-input',
    },
}
