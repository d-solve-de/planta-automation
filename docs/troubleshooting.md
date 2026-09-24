# Troubleshooting

Run with `--verbose` to see more detail. Messages below are printed by the tool.

## "Could not start Firefox"

Firefox or geckodriver is missing or not on the `PATH`.

```bash
firefox --version        # or firefox-esr --version
geckodriver --version
```

Install whatever is missing ([installation.md](installation.md)). On Linux servers
without a display, `--headless` is required. Snap-packaged Firefox on Ubuntu often
does not work with geckodriver; install the `.deb` from Mozilla's PPA or use the
[container image](docker.md).

## "The page title ... does not look like PLANTA Pulse"

The URL opened, but the page is not PLANTA: wrong URL, a portal or VPN login page, or
a network error page. Open the URL in a normal browser to check; connect to the VPN
first if PLANTA is internal.

## "The timesheet did not appear. You are probably not logged in."

Headless or non-interactive run without a stored session. Log in once with a visible
browser:

```bash
planta-filler --url URL --login-only
```

If it happens with a visible browser too, the timesheet page may need a click after
login or the selectors changed ([development.md](development.md#when-plantas-ui-changes)).

## The login prompt appears on every run

The persistent profile is not being used. Check that you did not pass
`--no-persistent`, that `~/.selenium_profiles/planta_firefox/` is writable, and that
you are not running from a different user or container each time. Sessions also
expire server-side; logging in again is normal every few days or weeks.

## Values appear in the browser but are gone after the run

PLANTA saves a cell when it loses focus; on a slow connection the save may not finish
before the next cell. Increase the delay:

```bash
planta-filler --url URL --delay 0.5
```

## "Validation failed" (exit code 2)

The message lists every problem. Typical causes:

- `--week -1,-2` without `=`: write `--week=-1,-2`.
- `--weekdays 7`: weekday codes are 0 (Monday) to 6 (Sunday).
- `--post-randomization 1`: the factor must be below 1.0.
- `--reference-file` path does not exist or does not end in `.csv`.

## Reference file warnings

- *"reference has N rows but PLANTA shows M task rows"*: the file no longer matches
  your projects. Export a new one: `--export-reference PATH`.
- *"no column for weekday"*: the header has no label for that day and the file is
  not single-column; see [reference-file-format.md](reference-file-format.md).
- *"reference file not found"* with the default file: reinstall the package.

The affected days are filled with equal weights; nothing else is changed.

## "PLANTA shows ... but week ... was requested; week navigation did not work"

The week arrows were clicked but the page still showed another week when the tool
was about to write, so it stopped without changing that week. Usually the page was
slow: run again, or raise `SELECTORS["timeouts"]["navigation_seconds"]` in
`config.py`. If it happens every time, the arrow selectors in `config.py` no longer
match PLANTA's markup ([development.md](development.md#when-plantas-ui-changes)).

## Some days are skipped

Days with 0 attendance hours (weekends, holidays, sick leave) are skipped on purpose.
Days not in `--weekdays` are skipped as well.

## Firefox says the profile was used with a newer version

You copied a profile between machines or containers with different Firefox versions.
Start with `MOZ_ALLOW_DOWNGRADE=1` in the environment, or delete
`~/.selenium_profiles/planta_firefox/` and log in again.

## `python3 -m planta_filler` works but `planta-filler` is not found

The pip scripts directory is not on your `PATH`. Either use the module form, or add
`~/.local/bin` (Linux/macOS) or Python's `Scripts` directory (Windows) to `PATH`, or
install with `pipx`.

## Still stuck?

Open an issue at <https://github.com/d-solve-de/planta-automation/issues> with the
command (without URL and credentials), the `--verbose` output and the versions of
Python, Firefox, geckodriver and planta-filler.
