# ============================================================================
# DEFAULT CONFIGURATION FOR PLANTA FILLER
# ============================================================================

# Strategy for distributing hours
# Options: 'random', 'equal', 'copy_reference'
DEFAULT_STRATEGY = 'equal'

# Weekdays to process (0=Monday, 6=Sunday)
# [0, 1, 2, 3, 4] = Monday through Friday
DEFAULT_WEEKDAYS = [0, 1, 2, 3, 4]

# Delay between field updates in seconds
DEFAULT_DELAY = 0.2

# Seconds to wait before closing browser (time to verify changes)
DEFAULT_CLOSE_DELAY = 20.0

# Use persistent Firefox profile to save login between sessions
# Profile location: ~/.selenium_profiles/planta_firefox/
DEFAULT_USE_PERSISTENT_PROFILE = True

# Run browser in headless mode (no visible window)
DEFAULT_HEADLESS = False

# Default reference file containing hour distributions for the week
DEFAULT_REFERENCE_FILE = 'default_reference.csv'

# Default exclude pattern (empty list means no exclusions)
# Example: [1, 0, 0, 1] would exclude indices 0 and 3
DEFAULT_EXCLUDE_VALUES = []