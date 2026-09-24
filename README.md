# planta-filler

Automatic timesheet filling for **PLANTA Pulse**. The tool opens your timesheet in
Firefox, reads the attendance hours of every day and distributes them over your task
rows, exactly as if you had typed them yourself.

[![PyPI](https://img.shields.io/pypi/v/planta-filler)](https://pypi.org/project/planta-filler/)
[![CI](https://github.com/d-solve-de/planta-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/d-solve-de/planta-automation/actions/workflows/ci.yml)
![Python](https://img.shields.io/pypi/pyversions/planta-filler)
![License](https://img.shields.io/pypi/l/planta-filler)

## Highlights

- **Three strategies:** `equal`, `random`, or `copy_reference` (reuse the proportions of a reference week).
- **Any week, any days:** current, past or future weeks (`--week=-2,-1,0`, `--week 2024-W05`), selected weekdays only.
- **Keeps what you protect:** exclude task rows (`--exclude 0,2`), add natural jitter (`--post-randomization 0.1`).
- **Log in once:** a persistent Firefox profile remembers your session; later runs work headless, on a server or in a container.
- **Build templates from real data:** `--export-reference` turns a manually filled week into a reference file.

## Install

```bash
pip3 install planta-filler
```

You also need [Firefox](https://www.mozilla.org/firefox/) and
[geckodriver](https://github.com/mozilla/geckodriver/releases) on your `PATH`.
Details, including Docker/Podman images: [docs/installation.md](docs/installation.md).

## Quick start

```bash
# 1. Log in once (a browser window opens; press ENTER in the terminal when the timesheet is visible)
planta-filler --url https://planta.example.com/ --login-only

# 2. Fill the current week Monday–Friday, equal hours per task row
planta-filler --url https://planta.example.com/

# Fill last week and the week before with random values
planta-filler --url https://planta.example.com/ --week=-2,-1 --strategy random

# Copy the proportions of your own reference week, with slight variation
planta-filler --url https://planta.example.com/ --strategy copy_reference \
  --reference-file ~/planta/my_week.csv --post-randomization 0.1

# Reset Friday of the current week to zero
planta-filler --url https://planta.example.com/ --reset --weekdays 4
```

`python3 -m planta_filler ...` works the same as `planta-filler ...`.
Run `planta-filler --man` for the full manual.

## Documentation

| I want to… | Read |
|---|---|
| install it (pip, from source, Docker/Podman) | [docs/installation.md](docs/installation.md) |
| fill my first week, step by step | [docs/tutorial-first-run.md](docs/tutorial-first-run.md) |
| build my own reference week and reuse it | [docs/tutorial-reference-file.md](docs/tutorial-reference-file.md) |
| solve a specific task (catch up, exclude rows, run on a schedule, …) | [docs/how-to.md](docs/how-to.md) |
| look up an option | [docs/cli-reference.md](docs/cli-reference.md) |
| understand the reference CSV format | [docs/reference-file-format.md](docs/reference-file-format.md) |
| run it in Docker or Podman | [docs/docker.md](docs/docker.md) |
| fix a problem | [docs/troubleshooting.md](docs/troubleshooting.md) |
| understand or change the code | [docs/architecture.md](docs/architecture.md), [docs/development.md](docs/development.md) |
| publish a new version to PyPI | [docs/releasing.md](docs/releasing.md) |

The documentation index is at [docs/README.md](docs/README.md).

## How it works

1. Firefox opens the PLANTA URL. With the default persistent profile you only log in once.
2. For each requested week the tool reads the attendance hours ("Anwesend") of every day and the current value of every task cell.
3. The chosen strategy computes a value per task row so that the day total matches the attendance hours; excluded rows are left untouched and reduce the budget.
4. Each changed cell is typed into the page and blurred, which makes PLANTA save it.
5. The browser stays open for `--close-delay` seconds so you can check the result.

Only the DOM selectors in `src/planta_filler/config.py` are PLANTA-specific.

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/development.md](docs/development.md). Changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License

MIT, see [LICENSE](LICENSE).
