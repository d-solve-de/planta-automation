# Copilot Instructions for planta-automation

## Project Overview
Selenium-based automation for PLANTA timesheet filling. Automates hour distribution across tasks using configurable strategies, running headlessly or with Firefox UI. Published as PyPI package `planta-filler`.

## Architecture

```
src/planta_filler/
├── __init__.py       # Package exports
├── __main__.py       # Entry: python3 -m planta_filler
├── cli.py            # main(), CLI argument parsing
├── core.py           # Selenium browser control (start_driver, set_week, reset_week)
├── calculations.py   # fill_day() - orchestrates strategy execution
├── strategies.py     # Strategy implementations (equal, random, copy_reference)
├── config.py         # Single source of truth for defaults + SELECTORS
├── validation.py     # Input validation
├── week_handler.py   # Week parsing and navigation
├── reference_handler.py  # Reference day file handling
└── data/
    ├── man_page.txt
    └── default_reference.csv
```

**Data Flow:** CLI args → `main()` → `validate_all_inputs()` → `start_driver()` → `set_week()`/`reset_week()` → reads DOM → `fill_day()` → strategy function → Selenium writes → `end_driver()`

## Key Conventions

### Strategy Pattern
All distribution strategies follow this signature in strategies.py:
```python
def strategy_name(total_hours: float, slots: int, precision: int=2, ...) -> list[float]
```
Register new strategies in the `strategies` dict, add case in `fill_day()`, update `VALID_STRATEGIES` in `config.py`.

### fill_day() Value Encoding
- `-1` = empty/blank cell (to be filled)
- `0` or positive float = existing value
- `exclude_values` list uses `1` = excluded, `0` = include

### Configuration
- All defaults and CSS selectors in `config.py` (single source of truth)
- No docstrings in code - all documentation in README.md
- Purpose comments at top of each file only

### Code Style
- Use relative imports within package (from .config import ...)
- All commands use python3
- Each feature gets its own local commit

## Development Commands

```bash
# Run from source
python3 -m planta_filler --url URL

# Install in editable mode
pip3 install -e .

# Show full man page
python3 -m planta_filler --man
```

## Common Modifications

- **Add new strategy**: Implement in `strategies.py`, add to `strategies` dict, add case in `fill_day()`, update `VALID_STRATEGIES` in `config.py`
- **Change selectors**: Update `SELECTORS` dict in `config.py`
- **Add CLI option**: Modify `argparse` section in `cli.py`, update `man_page.txt`
- **Change defaults**: Update `config.py`
- **Add CLI option**: Modify `argparse` section in `main()`, update `man_page.txt`
- **Change defaults**: Update `config.py`
