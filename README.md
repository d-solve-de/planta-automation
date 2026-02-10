# PLANTA Timesheet Automation

Selenium-based automation for PLANTA timesheet filling. Automates hour distribution across tasks using configurable strategies, running headlessly or with Firefox UI.

## Installation

### From PyPI (recommended)
```bash
pip3 install planta-filler
```

### From Source
```bash
git clone https://github.com/yourusername/planta-automation.git
cd planta-automation
pip3 install -e .
```

### Requirements
- Python 3.8+
- Firefox browser
- geckodriver ([download](https://github.com/mozilla/geckodriver/releases))

## Quick Start

```bash
# Run with defaults (fill current week Mon-Fri with equal strategy)
python3 -m planta_filler --url https://your-planta-url.com/

# Show full manual
python3 -m planta_filler --man
```

## Main Functions

| Function | Module | Description |
|----------|--------|-------------|
| `main()` | cli.py | CLI entry point, argument parsing and orchestration |
| `set_week()` | core.py | Fill hours for a week using specified strategy |
| `reset_week()` | core.py | Reset all hours to zero for specified days |
| `fill_day()` | calculations.py | Calculate hour distribution for a single day |
| `distribute_equal()` | strategies.py | Equal distribution across all slots |
| `distribute_random()` | strategies.py | Random distribution with scaling |
| `copy_reference_day()` | strategies.py | Copy proportions from reference file |
| `validate_all_inputs()` | validation.py | Validate all CLI inputs before execution |
| `parse_week_spec()` | week_handler.py | Parse week specification (YYYY-WNN or offset) |
| `ensure_reference_file()` | reference_handler.py | Auto-adapt reference file dimensions |

## Automatic Reference File Dimension Adaptation

**Yes**, the reference file is automatically adapted when the number of task rows in PLANTA changes:

1. When `copy_reference` strategy is used, the system reads the current number of slots from PLANTA
2. If the reference file has a different number of rows, it:
   - Creates a backup of the old file (`.csv.bak`)
   - Generates a new reference file with equal weights for all slots
3. This ensures the script never fails due to dimension mismatch

See `reference_handler.py` → `ensure_reference_file()` for implementation.

---

## Typical Use Cases

### 1. Daily Timesheet Filling
Fill today's timesheet with equal distribution:
```bash
python3 -m planta_filler --url https://planta.example.com/ --weekdays $(date +%w)
```

### 2. Weekly Batch Fill
Fill entire work week (Mon-Fri) at once:
```bash
python3 -m planta_filler --url https://planta.example.com/
```

### 3. Catch Up on Past Week
Forgot to fill last week? Fill it retroactively:
```bash
python3 -m planta_filler --url https://planta.example.com/ --week -1
```

### 4. Prepare Next Week
Pre-fill next week's timesheet:
```bash
python3 -m planta_filler --url https://planta.example.com/ --week 1
```

### 5. Realistic-Looking Values
Use random strategy for natural-looking distributions:
```bash
python3 -m planta_filler --url https://planta.example.com/ --strategy random
```

### 6. Consistent Patterns
Use reference day for consistent project hour ratios:
```bash
python3 -m planta_filler --url https://planta.example.com/ --strategy copy_reference
```

### 7. Clean Slate
Reset all hours to zero before fresh entry:
```bash
python3 -m planta_filler --url https://planta.example.com/ --reset
```

### 8. Headless Server Automation
Run on server without display:
```bash
python3 -m planta_filler --url https://planta.example.com/ --headless --persistent
```

---

## Parameter Reference with Examples

### `--url URL`
**Required.** PLANTA URL to access.

```bash
# Your company's PLANTA instance
python3 -m planta_filler --url https://pze.company.com/

# Test environment
python3 -m planta_filler --url https://pze-test.company.com/
```

### `--strategy {equal,random,copy_reference}`
Hour distribution strategy. Default: `equal`

```bash
# Equal distribution: 8h across 4 tasks → [2.0, 2.0, 2.0, 2.0]
python3 -m planta_filler --url URL --strategy equal

# Random distribution: 8h across 4 tasks → [1.5, 2.3, 2.1, 2.1]
python3 -m planta_filler --url URL --strategy random

# Copy from reference file with proportional scaling
python3 -m planta_filler --url URL --strategy copy_reference
```

### `--weekdays DAYS`
Comma-separated weekdays (0=Mon, 6=Sun). Default: `0,1,2,3,4` (Mon-Fri)

```bash
# Monday only
python3 -m planta_filler --url URL --weekdays 0

# Mon, Wed, Fri
python3 -m planta_filler --url URL --weekdays 0,2,4

# Tuesday and Thursday
python3 -m planta_filler --url URL --weekdays 1,3

# Full week including weekend
python3 -m planta_filler --url URL --weekdays 0,1,2,3,4,5,6

# Today only (using shell command substitution)
python3 -m planta_filler --url URL --weekdays $(python3 -c "from datetime import datetime; print(datetime.now().weekday())")
```

### `--week SPEC`
Week to process. Default: `0` (current week)

```bash
# Current week
python3 -m planta_filler --url URL --week 0

# Last week
python3 -m planta_filler --url URL --week -1

# Two weeks ago
python3 -m planta_filler --url URL --week -2

# Next week
python3 -m planta_filler --url URL --week 1

# Specific week (ISO format)
python3 -m planta_filler --url URL --week 2024-W05

# First week of 2025
python3 -m planta_filler --url URL --week 2025-W01
```

### `--reset`
Reset hours to 0 instead of filling. Default: false

```bash
# Reset current week
python3 -m planta_filler --url URL --reset

# Reset only Friday
python3 -m planta_filler --url URL --reset --weekdays 4

# Reset last week
python3 -m planta_filler --url URL --reset --week -1
```

### `--persistent`
Use persistent Firefox profile to save login. Default: true

```bash
# First run: browser opens, you log in manually
python3 -m planta_filler --url URL --persistent

# Subsequent runs: already logged in
python3 -m planta_filler --url URL --persistent

# Force fresh login (no persistent profile)
python3 -m planta_filler --url URL --no-persistent
```

Profile saved at: `~/.selenium_profiles/planta_firefox/`

### `--headless`
Run browser without visible window. Default: false

```bash
# Visible browser (watch automation)
python3 -m planta_filler --url URL

# Headless mode (background)
python3 -m planta_filler --url URL --headless

# Headless with persistent login (server automation)
python3 -m planta_filler --url URL --headless --persistent
```

### `--delay SECONDS`
Delay between field updates. Default: `0.2`

```bash
# Fast (may miss fields on slow connections)
python3 -m planta_filler --url URL --delay 0.05

# Normal speed
python3 -m planta_filler --url URL --delay 0.2

# Slow (for unreliable networks)
python3 -m planta_filler --url URL --delay 0.5

# Very slow (debugging)
python3 -m planta_filler --url URL --delay 1.0
```

### `--close-delay SECONDS`
Seconds to wait before closing browser. Default: `10.0`

```bash
# Close immediately
python3 -m planta_filler --url URL --close-delay 0

# Quick verification
python3 -m planta_filler --url URL --close-delay 5

# Long verification time
python3 -m planta_filler --url URL --close-delay 30

# Very long (for manual review)
python3 -m planta_filler --url URL --close-delay 60
```

### `--man`
Show detailed manual page.

```bash
python3 -m planta_filler --man
```

---

## Project Structure

```
planta-automation/
├── src/
│   └── planta_filler/
│       ├── __init__.py       # Package initialization, exports
│       ├── __main__.py       # Entry point: python3 -m planta_filler
│       ├── cli.py            # Command-line interface
│       ├── core.py           # Selenium browser control
│       ├── calculations.py   # Day filling orchestration
│       ├── strategies.py     # Distribution strategies
│       ├── config.py         # Default configuration
│       ├── validation.py     # Input validation
│       ├── week_handler.py   # Week parsing
│       ├── reference_handler.py  # Reference file management
│       └── data/
│           ├── man_page.txt
│           └── default_reference.csv
├── pyproject.toml           # Package configuration
├── README.md
├── LICENSE
└── requirements.txt
```

## Data Flow

```
CLI args → main() → validate_all_inputs()
                          ↓
              start_driver() → Firefox
                          ↓
              set_week() / reset_week()
                          ↓
      get_hours_per_day() + get_target_hours_per_day()
                          ↓
                    fill_day()
                          ↓
         strategy function (equal/random/copy_reference)
                          ↓
              Selenium writes to input fields
                          ↓
                    end_driver()
```

## Configuration Reference

Edit `src/planta_filler/config.py` to change defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_URL` | `''` | PLANTA URL (empty = must specify) |
| `DEFAULT_STRATEGY` | `'equal'` | Distribution strategy |
| `DEFAULT_WEEKDAYS` | `[0,1,2,3,4]` | Mon-Fri |
| `DEFAULT_DELAY` | `0.2` | Seconds between field updates |
| `DEFAULT_CLOSE_DELAY` | `10.0` | Seconds before browser closes |
| `DEFAULT_USE_PERSISTENT_PROFILE` | `True` | Save login between runs |
| `DEFAULT_HEADLESS` | `False` | Run without visible browser |
| `VALID_STRATEGIES` | `['random', 'equal', 'copy_reference']` | Available strategies |

## License

MIT License


# TODOs

- add the parameter post randomization for the user to choose via cli and change the code accodringly to set the parameter correctly when calling fill_day