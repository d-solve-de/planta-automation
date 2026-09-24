# CLI reference

```
planta-filler --url URL [OPTIONS]
python3 -m planta_filler --url URL [OPTIONS]
```

Options are grouped like in `--help`. `planta-filler --man` prints the same
information as a manual page.

## What to fill

### `--url URL`
The PLANTA Pulse URL, e.g. `https://planta.example.com/`. Must start with `http://`
or `https://`. Required unless `DEFAULT_URL` in `config.py` is set.

### `--week SPEC[,SPEC...]` (default: `0`)
Weeks to process, in the given order. Each `SPEC` is either

- a relative offset: `0` current week, `-1` last week, `1` next week, `-4` four weeks ago, or
- an ISO week: `2026-W05` (also `2026-w5`).

Several weeks form **one** comma-separated argument. Always write `--week=-2,-1,0`
(with `=`) so the leading `-` is not read as an option.

```bash
planta-filler --url URL --week=-1
planta-filler --url URL --week=-2,-1,0
planta-filler --url URL --week 2026-W05
```

### `--weekdays DAYS` (default: `0,1,2,3,4`)
Comma-separated weekday codes: 0 Mon, 1 Tue, 2 Wed, 3 Thu, 4 Fri, 5 Sat, 6 Sun.
Days whose attendance hours are 0 are skipped even if listed.

### `--exclude INDICES`
Zero-based indices of task rows (top to bottom) that are never changed, both when
filling and when resetting. Excluded rows keep their value, which is subtracted from
the day's budget.

```bash
planta-filler --url URL --exclude 0,2
```

## How to fill

### `--strategy {equal,random,copy_reference}` (default: `equal`)

| Strategy | Behaviour | 8 h over 4 rows |
|---|---|---|
| `equal` | Same amount for every free row | `[2.0, 2.0, 2.0, 2.0]` |
| `random` | Random weights scaled to the total | `[1.37, 3.02, 0.61, 3.0]` |
| `copy_reference` | Proportions of the weekday column of a reference CSV | reference `[1, 1, 2, 0]` → `[2.0, 2.0, 4.0, 0.0]` |

The sum always equals the attendance hours of the day (minus excluded rows), rounded
to two decimals.

### `--reference-file PATH`
CSV with weights for `copy_reference`. `~` is expanded, relative paths are resolved
from the current directory, and the file must exist. Default: the packaged example
`src/planta_filler/data/default_reference.csv`. Format: [reference-file-format.md](reference-file-format.md).
If the file cannot be used for a day, that day falls back to `equal` and a warning is
printed.

### `--post-randomization FACTOR` (default: `0.0`)
Jitter every generated value by up to `FACTOR` of itself while keeping the exact day
total. Allowed range: `0.0 <= FACTOR < 1.0`. Works with every strategy.

### `--reset`
Set the selected cells to `0` instead of filling them. Honours `--week`,
`--weekdays` and `--exclude`.

### `--export-reference PATH`
Write the values currently shown in PLANTA for the selected week (one column per
selected weekday) to `PATH` as a reference CSV, then exit. Nothing is changed in
PLANTA. Exactly one `--week` value is allowed.

## Browser

### `--persistent` / `--no-persistent` (default: persistent)
Keep cookies and the login in the Firefox profile `~/.selenium_profiles/planta_firefox/`.
With `--no-persistent` a temporary profile is used and you log in every time.

### `--headless`
Run Firefox without a window. Requires an already logged-in persistent profile; when
the timesheet does not appear the run fails with exit code 1 instead of waiting for
input.

### `--login-only`
Open PLANTA, wait until the timesheet is visible (prompting for the login if needed)
and exit without changing any hours. Use it once to prepare the profile for headless
or scheduled runs.

### `--delay SECONDS` (default: `0.2`, range 0–60)
Pause after each typed cell so PLANTA can save it. Increase on slow connections.

### `--close-delay SECONDS` (default: `10`, range 0–60)
How long the browser stays open after the run so you can verify the result.

## Output

| Option | Effect |
|---|---|
| `-v`, `--verbose` | debug output, including Selenium logs |
| `-q`, `--quiet` | warnings and errors only |
| `--version` | print the version and exit |
| `--man` | print the manual page and exit |
| `-h`, `--help` | print the short help and exit |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | runtime failure: Firefox/geckodriver missing, wrong page, not logged in, PLANTA error |
| 2 | invalid arguments (all problems are listed at once) |
| 130 | interrupted with Ctrl+C |

## Login behaviour

1. The URL is opened and the page title is checked for "PLANTA Pulse".
2. The tool waits up to 10 s for the timesheet inputs.
3. If they do not appear and the run is interactive (visible browser, terminal
   attached), it asks you to log in and press ENTER, then waits up to 60 s more.
4. Otherwise it stops with "The timesheet did not appear".

Timeouts live in `SELECTORS["timeouts"]` in `config.py`.
