# Copilot Instructions for planta-automation

## Project Overview
Selenium-based automation for PLANTA timesheet filling. Automates hour distribution across tasks using configurable strategies, running headlessly or with Firefox UI.

## Architecture

```
planta_filler.py      # Entry point, CLI, Selenium browser control
├── calculations.py   # fill_day() - orchestrates strategy execution
├── strategies.py     # Strategy implementations (equal, random, random_noise, copy_reference)
├── config.py         # Single source of truth for defaults
├── validation.py     # Input validation
├── week_handler.py   # Week parsing and navigation
├── reference_handler.py  # Reference day file handling
├── planta_selectors.yaml # CSS selectors for PLANTA DOM
├── man_page.txt      # Man page template
└── default_reference.csv # Reference hour distributions
```

**Data Flow:** CLI args → `main()` → `set_week()`/`reset_week()` → reads DOM via `get_hours_per_day()` + `get_target_hours_per_day()` → calls `fill_day()` → strategy function → writes to input fields via Selenium

## Key Conventions

### Strategy Pattern
All distribution strategies follow this signature in strategies.py:
```python
def strategy_name(total_hours: float, slots: int, precision: int=2, ...) -> list[float]
```
Register new strategies in the `strategies` dict at the bottom of the file, then add case in `fill_day()`.

### fill_day() Value Encoding
- `-1` = empty/blank cell (to be filled)
- `0` or positive float = existing value
- `exclude_values` list uses `1` = excluded, `0` = include

### Configuration
- All defaults in `config.py` (single source of truth)
- CSS selectors in `planta_selectors.yaml`
- No documentation in code files - all docs in README.md

### Code Style
- No docstrings in Python files
- All documentation in README.md
- Each feature gets its own local commit

## Development Commands

```bash
# Run with defaults
python planta_filler.py

# Show full man page
python planta_filler.py --man
```

## Common Modifications

- **Add new strategy**: Implement in `strategies.py`, add to `strategies` dict, add case in `fill_day()`, update `VALID_STRATEGIES` in `config.py`
- **Change selectors**: Update only `planta_selectors.yaml`
- **Add CLI option**: Modify `argparse` section in `main()`, update `man_page.txt`
- **Change defaults**: Update `config.py`
