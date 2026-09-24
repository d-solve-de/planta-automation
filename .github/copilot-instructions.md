# Copilot instructions for planta-automation

Python package `planta-filler` (import name `planta_filler`): Selenium/Firefox
automation that fills PLANTA Pulse timesheets. Full docs live in `docs/`; read
`docs/architecture.md` before changing the structure.

## Layout

```
src/planta_filler/
├── cli.py              argparse -> validation -> RunOptions -> core.run()
├── core.py             workflow: open_timesheet, iter_weeks, fill/reset/export a week
├── browser.py          Selenium only: start_driver/end_driver, PlantaPage (DOM access)
├── calculations.py     fill_day(): map a strategy result onto the real task rows
├── strategies.py       equal / random / copy_reference, registered in STRATEGIES
├── reference_handler.py  read/write reference CSVs (ReferenceWeek)
├── validation.py       validate_* functions raising ValidationError
├── week_handler.py     week spec parsing, ISO week helpers
├── config.py           all defaults, limits and CSS selectors
├── exceptions.py       PlantaFillerError hierarchy
└── data/               default_reference.csv, man_page.txt
tests/                  pytest; conftest.py provides FakeDriver (no real browser)
docs/                   user and maintainer documentation
```

## Conventions

- Only `browser.py` imports Selenium. `core.py` works against `PlantaPage`, so it is
  testable with `tests/conftest.py::FakeDriver`.
- Defaults and selectors are defined once in `config.py`; the CLI, the man page and
  the docs read them from there.
- Raise subclasses of `PlantaFillerError`; `cli.main()` turns them into messages and
  exit codes (2 = invalid input, 1 = runtime failure).
- Value encoding in `calculations.py`: `-1` = blank cell, exclude mask `1` = never touch.
- Type hints with `from __future__ import annotations`; Python 3.9 compatible.
- Formatting and linting: `ruff` (config in `pyproject.toml`, line length 120).
- Every behaviour change needs a test and a `CHANGELOG.md` entry under `[Unreleased]`.
- Version is defined once in `src/planta_filler/__init__.py` (`__version__`).

## Common tasks

- New strategy: implement in `strategies.py` with signature
  `fn(total_hours, slots, precision=2, **kwargs) -> list[float]`, register it in
  `STRATEGIES`, add the name to `VALID_STRATEGIES` in `config.py`, document it in
  `data/man_page.txt` and `docs/cli-reference.md`, add tests.
- New CLI option: `cli.build_parser()`, then `options_from_args()` / `RunOptions`,
  validation in `validation.py`, man page, `docs/cli-reference.md`, tests in
  `tests/test_cli.py`.
- PLANTA UI changed: update `SELECTORS` in `config.py`; run
  `docs/manual-test-checklist.md` against a test account.

## Commands

```bash
make dev      # editable install with dev tools
make check    # ruff check + ruff format --check + pytest
make build    # sdist + wheel + twine check
planta-filler --man
```
