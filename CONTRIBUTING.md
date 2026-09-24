# Contributing

Thanks for helping to improve planta-filler.

## Quick setup

```bash
git clone https://github.com/d-solve-de/planta-automation.git
cd planta-automation
python3 -m venv .venv && source .venv/bin/activate
make dev      # pip install -e ".[dev]"
make check    # ruff + pytest, the same as CI
```

The full developer guide, including how the code is organised and how to add a
strategy or update a selector, is in [docs/development.md](docs/development.md) and
[docs/architecture.md](docs/architecture.md).

## Pull requests

1. Create a branch from `main`.
2. Keep the change focused; one topic per pull request.
3. Add or update tests in `tests/`. Everything that does not need a real browser must
   be covered by a test that uses the fake driver from `tests/conftest.py`.
4. Run `make check`; CI runs the same commands on Python 3.9 to 3.13.
5. Add a line to the `[Unreleased]` section of `CHANGELOG.md`.
6. Open the pull request with a short description of *why* the change is needed.

## Reporting a bug

Please include the command you ran (without your URL or credentials), the full
output (`--verbose` helps), your operating system, and the versions of Python,
Firefox, geckodriver and planta-filler (`planta-filler --version`).

## Manual testing against PLANTA

Changes to `browser.py` or the selectors in `config.py` cannot be verified by the
unit tests. Use the checklist in
[docs/manual-test-checklist.md](docs/manual-test-checklist.md) against a test
account before opening the pull request and mention what you tested.
