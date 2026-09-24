# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-09-24

### Added
- `--login-only`: open PLANTA, wait for the login and exit without changing anything
  (prepares the persistent profile for headless and container runs).
- `--export-reference PATH`: save the values currently in PLANTA as a whole-week
  reference CSV.
- `--no-persistent` to disable the persistent Firefox profile (previously the flag
  could not be turned off).
- `--version`, `--verbose`, `--quiet`.
- Reference files accept German and English weekday labels, full names, decimal
  commas, and single-column files that apply to every weekday.
- Dockerfile, `docker-compose.yml` and a Makefile.
- CI workflow (ruff + pytest on Python 3.9–3.13 + build check); the publish workflow
  now runs the checks first, verifies that the tag matches the version, supports
  TestPyPI and creates a GitHub release.
- Documentation under `docs/` (tutorials, how-tos, CLI reference, architecture,
  releasing guide).

### Changed
- Default strategy is `equal` (the README always documented it that way; the code
  used `random`).
- All arguments are validated before the browser starts; invalid input exits with
  code 2, runtime failures with code 1.
- Login handling: the tool waits for the timesheet and only asks you to log in when
  it does not appear. Headless runs fail fast with a clear message instead of
  hanging on an invisible prompt.
- A reference file with the wrong number of rows no longer gets overwritten (the
  old code rewrote the file inside the installed package). The affected days fall
  back to equal weights and a warning is printed.
- Rounding residuals are pushed onto the largest value instead of a random one.
- Internal structure: Selenium access lives in `browser.py` (`PlantaPage`), the
  workflow in `core.py` (`run`, `RunOptions`), and errors derive from
  `PlantaFillerError`. `set_week`/`reset_week` were replaced by `run`.
- Personal example reference files moved from the package to `examples/reference-files/`.
- Requires Python 3.9 or newer (the 0.1.x code already failed to import on 3.8).

### Fixed
- `--exclude` was parsed after the browser had started; invalid values left a
  browser window open.
- `--reference-file` was not validated and `~` was not expanded.
- `__version__` disagreed with the version in `pyproject.toml`; the version is now
  defined once in `planta_filler/__init__.py`.
- Hours shown with a decimal comma were parsed as 0.

## [0.1.2] - 2026-03-31

- Documentation updates and version bump.

## [0.1.1] - 2026-03-30

- Multi-week processing, post-randomization, `--exclude`, weekly reference files.

## [0.1.0] - 2026-02-11

- First release on PyPI.

[Unreleased]: https://github.com/d-solve-de/planta-automation/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/d-solve-de/planta-automation/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/d-solve-de/planta-automation/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/d-solve-de/planta-automation/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/d-solve-de/planta-automation/releases/tag/v0.1.0
