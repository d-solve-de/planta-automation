# How-to recipes

Short answers to specific tasks. Replace `URL` with your PLANTA URL. All commands
assume you logged in once (see the [first-run tutorial](tutorial-first-run.md)).

## Fill only some days

```bash
planta-filler --url URL --weekdays 0,2,4        # Monday, Wednesday, Friday
planta-filler --url URL --weekdays $(date +%u | awk '{print $1-1}')   # today (Linux/macOS)
```

Weekday codes: 0 = Monday … 6 = Sunday.

## Catch up on past weeks

```bash
planta-filler --url URL --week=-1               # last week
planta-filler --url URL --week=-4,-3,-2,-1      # the last four weeks, oldest first
planta-filler --url URL --week 2026-W05         # a specific ISO week
```

Pass several weeks as **one** argument. Use the `--week=...` form: without the `=`,
a value starting with `-` can be mistaken for an option.

## Prepare next week

```bash
planta-filler --url URL --week=1
```

## Keep certain rows untouched

```bash
planta-filler --url URL --exclude 0,3
```

Row indices are zero-based, top to bottom. Excluded rows keep their values and reduce
the hours distributed over the other rows. `--exclude` also applies to `--reset`.

## Make values look less uniform

```bash
planta-filler --url URL --strategy random                       # fully random split
planta-filler --url URL --strategy equal --post-randomization 0.2   # ±20 % jitter, exact total
```

The jitter factor must be below 1.0 so no value can become negative.

## Reuse your typical week

See [tutorial-reference-file.md](tutorial-reference-file.md). Short version:

```bash
planta-filler --url URL --week=-1 --export-reference ~/planta/my_week.csv   # once
planta-filler --url URL --strategy copy_reference --reference-file ~/planta/my_week.csv
```

## Reset days to zero

```bash
planta-filler --url URL --reset                 # current week, Mon–Fri
planta-filler --url URL --reset --week=-1 --weekdays 4
```

## Run without a browser window

```bash
planta-filler --url URL --headless --close-delay 0
```

Headless runs need a stored login. If none exists, the run stops with "The timesheet
did not appear"; run `planta-filler --url URL --login-only` once with a visible browser.

## Run on a schedule

Because the login is persisted, a cron job or systemd timer can run the tool. Example
crontab entry for every weekday at 17:30, filling the current week:

```cron
30 17 * * 1-5 /usr/local/bin/planta-filler --url URL --headless --close-delay 0 >> ~/planta-filler.log 2>&1
```

Use the absolute path to `planta-filler` (`which planta-filler`) and make sure the
cron environment can find Firefox and geckodriver (`PATH=` line in the crontab).
Sessions expire eventually; when the log shows "The timesheet did not appear", log in
again with `--login-only`.

## Use a different or temporary profile

```bash
planta-filler --url URL --no-persistent         # log in every time, nothing stored
```

The profile directory is `~/.selenium_profiles/planta_firefox/`. Delete it to force a
fresh login.

## Slow or flaky network

```bash
planta-filler --url URL --delay 0.5 --close-delay 30
```

`--delay` is the pause after every typed cell; PLANTA needs a moment to save each one.

## See what is going on

```bash
planta-filler --url URL --verbose               # debug output
planta-filler --url URL --quiet                 # warnings and errors only
planta-filler --man                             # full manual
```

## Use it from Python

```python
from planta_filler import RunOptions, end_driver, run, start_driver

driver = start_driver(headless=True)
try:
    run(driver, RunOptions(url="https://planta.example.com/", week_specs=["-1", "0"], strategy="random"))
finally:
    end_driver(driver)
```

`RunOptions` mirrors the CLI options; see `src/planta_filler/core.py`.
