# planta-filler documentation

## For users

| Document | What it covers |
|---|---|
| [Installation](installation.md) | pip, from source, Firefox and geckodriver, Docker/Podman |
| [Tutorial: your first run](tutorial-first-run.md) | Log in once, fill a week, check the result |
| [Tutorial: build and use a reference week](tutorial-reference-file.md) | `copy_reference` end to end, including `--export-reference` |
| [How-to recipes](how-to.md) | Catch up on past weeks, exclude rows, add variation, schedule runs, reset days |
| [CLI reference](cli-reference.md) | Every option with defaults and examples |
| [Reference file format](reference-file-format.md) | The CSV format for `copy_reference` |
| [Docker and Podman](docker.md) | Build the image, log in once, run headless |
| [Troubleshooting](troubleshooting.md) | Error messages and what to do |

## For maintainers

| Document | What it covers |
|---|---|
| [Architecture](architecture.md) | Modules, data flow, design decisions |
| [Development](development.md) | Setup, tests, lint, adding strategies or options, updating selectors |
| [Releasing to PyPI](releasing.md) | Versioning, changelog, tagging, trusted publishing, TestPyPI, manual fallback |
| [Manual test checklist](manual-test-checklist.md) | What to verify against a real PLANTA instance |

The short manual is also built in: `planta-filler --man`.
