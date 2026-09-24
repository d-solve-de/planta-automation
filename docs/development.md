# Development guide

## Setup

```bash
git clone https://github.com/d-solve-de/planta-automation.git
cd planta-automation
python3 -m venv .venv && source .venv/bin/activate
make dev            # pip install -e ".[dev]"  (pytest, ruff, build, twine)
```

Run the CLI from the checkout with `planta-filler ...` (editable install) or
`python3 -m planta_filler ...`.

## Everyday commands

| Command | Purpose |
|---|---|
| `make check` | ruff lint, ruff format check, pytest (what CI runs) |
| `make test` | tests only |
| `make lint` / `make format` | check / auto-fix style |
| `make build` | sdist + wheel into `dist/`, verified with `twine check` |
| `make clean` | remove build artifacts and caches |
| `make help` | list all targets |

Without `make`: `ruff check src tests`, `ruff format src tests`, `python3 -m pytest`.

## Tests

- `tests/conftest.py` provides `FakeDriver`, `FakeElement`, `hours_element()` and
  `target_element()`. They implement just enough of the WebDriver API for
  `PlantaPage`, so `core` and `browser` are tested without Firefox.
- `pytest` also runs the doctests in `src/` (`--doctest-modules`).
- Tests that depend on "today" inject a fixed date (`parse_week_spec(spec, today)`) or
  monkeypatch `core.week_offset_from_today`.
- Anything that needs a real PLANTA instance goes into
  [manual-test-checklist.md](manual-test-checklist.md), not into `tests/`.

## Adding a strategy

1. Implement it in `strategies.py`:
   ```python
   def distribute_front_loaded(total_hours, slots, precision=2, **_):
       shortcut = validate_hours_and_slots(total_hours, slots, precision)
       if shortcut is not None:
           return shortcut
       weights = [slots - i for i in range(slots)]
       return enforce_exact_sum(total_hours, [total_hours * w / sum(weights) for w in weights], precision)
   ```
   Accept `**kwargs` so `fill_day()` can pass `retries` and future options.
2. Register it: `STRATEGIES["front_loaded"] = distribute_front_loaded`.
3. Add `"front_loaded"` to `VALID_STRATEGIES` in `config.py`.
4. If it needs extra data (like `copy_reference` needs a reference day), add the
   branch in `calculations.fill_day()`.
5. Document it in `data/man_page.txt` and `docs/cli-reference.md`; add tests in
   `tests/test_strategies.py` and a `CHANGELOG.md` entry.

## Adding a CLI option

1. Add the argument in `cli.build_parser()` (choose the right group).
2. Validate it in `validation.py` and wire it into `validate_all_inputs()` if it needs
   checking.
3. Add a field to `core.RunOptions` and set it in `cli.options_from_args()`.
4. Use it in `core.py`.
5. Show it in `cli.print_summary()` if it changes what happens.
6. Document it in `data/man_page.txt`, `docs/cli-reference.md`; test it in
   `tests/test_cli.py` (parsing) and `tests/test_core.py` (behaviour).

## When PLANTA's UI changes

All DOM knowledge is in `config.SELECTORS` and the two regexes next to it:

- `hours_input`: the per-cell inputs; their `id` must end with the ISO date.
- `target_hours_div`: the attendance box per day; the date is in a class `att-YYYYMMDD`.
- `navigation.week_back` / `week_forward`: the arrows that move exactly one week.

Inspect the new markup in Firefox's developer tools, adjust the selectors, then run
the [manual checklist](manual-test-checklist.md) against a test account. Update the
fake elements in `tests/conftest.py` if the id or class conventions changed.

## Code style

- `ruff` handles formatting and linting (line length 120, rules in `pyproject.toml`).
- `from __future__ import annotations` in every module; keep Python 3.9 compatibility
  (no `match`, no `X | Y` at runtime outside annotations).
- Public functions have a docstring that says what they return; comments explain *why*.
- Raise `PlantaFillerError` subclasses for expected failures. Let unexpected ones propagate.
- Log with `log.info/warning/debug`; do not `print()` outside `cli.py` and the login prompt.

## Repository layout

```
.github/workflows/   ci.yml (lint, tests, build) and python-publish-pypi.yml
docs/                this documentation
examples/            reference-files/ templates
src/planta_filler/   the package
tests/               pytest suite
Dockerfile, docker-compose.yml, .env.example
Makefile, pyproject.toml, MANIFEST.in
CHANGELOG.md, CONTRIBUTING.md, README.md, LICENSE
```

## Releasing

See [releasing.md](releasing.md).
