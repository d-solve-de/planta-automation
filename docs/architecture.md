# Architecture

planta-filler is small on purpose: roughly 1,500 lines of Python in twelve modules.
This page explains how they fit together so that changes land in the right place.

## Module map

```
src/planta_filler/
├── cli.py               argparse → validation → RunOptions → core.run()
├── core.py              the workflow (open, navigate weeks, fill / reset / export)
├── browser.py           Selenium: start_driver, end_driver, PlantaPage
├── calculations.py      fill_day(): maps a strategy result onto real task rows
├── strategies.py        equal / random / copy_reference, STRATEGIES registry
├── reference_handler.py ReferenceWeek: read and write reference CSVs
├── validation.py        validate_*(): user input checks, ValidationError
├── week_handler.py      week specs, ISO week arithmetic, weekday filtering
├── config.py            all defaults, limits, timeouts and CSS selectors
├── exceptions.py        PlantaFillerError and subclasses
├── __init__.py          __version__ and the public API
├── __main__.py          python -m planta_filler
└── data/                default_reference.csv, man_page.txt (template)
```

## Data flow of one run

```
argv
 │  cli.build_parser().parse_args()
 ▼
argparse.Namespace
 │  cli.options_from_args()  → validation.validate_all_inputs()   (exit 2 on error)
 ▼
core.RunOptions
 │  browser.start_driver()                                        (exit 1 on error)
 ▼
core.run(driver, options)
 ├─ PlantaPage(driver)
 ├─ open_timesheet(): get URL, check title, wait for inputs, prompt for login if interactive
 ├─ load_reference(): read the CSV once (copy_reference only)
 └─ for spec in iter_weeks(): click the week arrows to reach the spec
      ├─ fill_visible_week():  page.read_hours() + page.read_target_hours()
      │      for each working day: calculations.fill_day() → page.write_hours() per changed cell
      ├─ reset_visible_week(): same, but every non-excluded cell becomes 0
      └─ export_visible_week(): page.read_hours() → reference_handler.save_reference_week()
 │  wait_before_close()
 ▼
browser.end_driver()
```

## Layers and their rules

| Layer | Modules | May import | Must not |
|---|---|---|---|
| Pure logic | `strategies`, `calculations`, `week_handler`, `reference_handler`, `validation` | `config`, `exceptions` | touch Selenium or print |
| Browser | `browser` | selenium, `config`, `exceptions` | know about strategies or weeks |
| Workflow | `core` | everything above through `PlantaPage` | import selenium directly |
| Interface | `cli`, `__main__` | `core`, `browser`, `validation`, `config` | contain business logic |

Because `core` only talks to `PlantaPage`, the whole workflow runs in the unit tests
against `tests/conftest.py::FakeDriver`; no browser is started.

## Key concepts

**Week specs.** `"0"`, `"-1"`, `"2026-W05"`. `week_handler.week_offset_from_today()`
turns a spec into a number of weeks relative to the current week; `core.iter_weeks()`
clicks the difference between the current and the target offset, so weeks can be
listed in any order.

**Hour fields.** `PlantaPage.read_hours()` returns `{date: [HourField(field_id, value), ...]}`
in DOM order. The date is taken from the input id, which ends with `YYYY-MM-DD`.
Row index `i` in `--exclude` refers to position `i` of that list.

**Target hours.** `PlantaPage.read_target_hours()` reads the attendance box of
each day (`div.load` with a class `att-YYYYMMDD`). Days with 0 h are skipped.

**Value encoding in `calculations.fill_day()`.** `-1` marks a blank cell; the
exclude mask uses `1` for rows that must not change. With `override_mode=True`
(the CLI's behaviour) every non-excluded cell is treated as blank and rewritten;
with `False` only blank cells are filled and existing values are kept. Kept values
reduce the hours handed to the strategy.

**Strategies** return values for the *free* rows only and always sum to the given
hours (`enforce_exact_sum()` pushes the rounding residual onto the largest value).
`copy_reference` receives the reference weights of the free rows; if they are
unusable, `fill_day()` falls back to `equal`.

**Reference files** are parsed once into a `ReferenceWeek` (label → weights).
`for_weekday()` resolves German/English labels, single-column files and positional
columns, and validates the row count. The tool never writes to a reference file
except through `--export-reference`.

**Errors.** Everything expected derives from `PlantaFillerError`. `cli.main()` maps
`ValidationError` to exit code 2 and any other `PlantaFillerError` to exit code 1,
always closing the browser. Unexpected exceptions propagate with a traceback, which is
what you want when a selector silently stopped matching.

**Logging.** Modules log through `logging.getLogger(__name__)`; `cli.configure_logging()`
prints messages to stdout. Library users can configure logging themselves.

## Design decisions

- **Selectors in one dict.** PLANTA UI changes should only require edits to
  `config.SELECTORS`, plus the manual checklist.
- **Override mode by default.** The CLI rewrites every non-excluded cell so that a run
  is idempotent: running twice yields the same timesheet. Protect manual entries
  with `--exclude`.
- **No writes into the installed package.** Older versions rewrote the packaged
  reference file when the row count changed; that breaks read-only installs and
  surprises users. Mismatches now fall back with a warning.
- **Validation before the browser.** Starting Firefox takes seconds; every argument
  is checked first and all problems are reported together.
- **Version in one place.** `__version__` in `__init__.py`; `pyproject.toml` reads it
  dynamically and the release workflow checks it against the git tag.
