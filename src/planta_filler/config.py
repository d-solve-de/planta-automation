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

DEFAULT_URL = ''
DEFAULT_STRATEGY = 'random'
DEFAULT_WEEKDAYS = [0, 1, 2, 3, 4]
DEFAULT_DELAY = 0.2
DEFAULT_CLOSE_DELAY = 10.0
DEFAULT_USE_PERSISTENT_PROFILE = True
DEFAULT_HEADLESS = False
DEFAULT_REFERENCE_FILE = 'default_reference.csv'
DEFAULT_EXCLUDE_VALUES = []
DEFAULT_PRECISION = 2
DEFAULT_RETRIES = 5
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
        'day_back': 'i.fas.fa-chevron-left',
        'day_forward': 'i.fas.fa-chevron-right',
        'today_button': 'div.label:contains("Heute")',
    },
}
