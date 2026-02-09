# PLANTA Timesheet Automation

Selenium-based automation for PLANTA timesheet filling. Automates hour distribution across tasks using configurable strategies, running headlessly or with Firefox UI.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with defaults (fill current week Mon-Fri with equal strategy)
python planta_filler.py

# Show full manual
python planta_filler.py --man
```

## Features

- **Multiple distribution strategies**: equal, random, random_noise, copy_reference
- **Week navigation**: Fill current, past, or future weeks
- **Persistent login**: Save Firefox session between runs
- **Headless mode**: Run without visible browser window
- **Input validation**: Comprehensive validation of all parameters

## Usage Examples

```bash
# Fill with random noise (natural-looking values)
python planta_filler.py --strategy random_noise

# Fill specific weekdays only
python planta_filler.py --weekdays 0,2,4  # Mon, Wed, Fri

# Fill last week
python planta_filler.py --week -1

# Fill specific week
python planta_filler.py --week 2024-W05

# Reset all hours to zero
python planta_filler.py --reset

# Run headless with persistent profile
python planta_filler.py --headless --persistent
```

## Strategies

| Strategy | Description |
|----------|-------------|
| `equal` | Distributes hours equally across all tasks |
| `random` | Random distribution with variance |
| `random_noise` | Equal distribution with small random variations for natural look |
| `copy_reference` | Copies proportions from reference day file |

## Configuration

All defaults are defined in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_URL` | `https://pze.rz.bankenit.de/` | PLANTA URL |
| `DEFAULT_STRATEGY` | `equal` | Distribution strategy |
| `DEFAULT_WEEKDAYS` | `[0,1,2,3,4]` | Mon-Fri |
| `DEFAULT_DELAY` | `0.1` | Seconds between field updates |
| `DEFAULT_CLOSE_DELAY` | `3.0` | Seconds before browser closes |

CSS selectors for PLANTA DOM elements are in `planta_selectors.yaml`.

## Project Structure

```
planta_filler.py      # Entry point, CLI, Selenium browser control
├── calculations.py   # fill_day() - orchestrates strategy execution
├── strategies.py     # Strategy implementations
├── config.py         # Default configuration values
├── validation.py     # Input validation
├── week_handler.py   # Week parsing and navigation
├── reference_handler.py  # Reference day file handling
├── planta_selectors.yaml # CSS selectors for PLANTA DOM
├── man_page.txt      # Man page template
└── default_reference.csv # Reference hour distributions
```

## Data Flow

```
CLI args → main() → set_week()/reset_week()
                          ↓
         reads DOM via get_hours_per_day() + get_target_hours_per_day()
                          ↓
                    calls fill_day()
                          ↓
                   strategy function
                          ↓
              writes to input fields via Selenium
```

## Key Conventions

### Value Encoding in fill_day()
- `-1` = empty/blank cell (to be filled)
- `0` or positive float = existing value
- `exclude_values`: `1` = excluded, `0` = include

### Strategy Function Signature
All strategies in `strategies.py` follow:
```python
def strategy_name(total_hours: float, slots: int, precision: int=2, ...) -> list[float]
```

### Sum Enforcement
All strategies must sum exactly to `total_hours`. Use `enforce_exact_sum()` to correct rounding errors.

## Requirements

- Python 3.7+
- Firefox browser
- geckodriver ([download](https://github.com/mozilla/geckodriver/releases))

## Installation

```bash
pip install selenium pyyaml

# Download geckodriver and add to PATH
```

## Persistent Profile

First run requires manual login. Using `--persistent` saves Firefox profile to `~/.selenium_profiles/planta_firefox/` for automatic login on subsequent runs.

## License

MIT License
