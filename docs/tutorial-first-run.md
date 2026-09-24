# Tutorial: your first run

This tutorial takes about ten minutes. At the end, the current week of your PLANTA
timesheet is filled and the tool remembers your login for the next time.

You need planta-filler installed (see [installation.md](installation.md)) and the URL
of your PLANTA Pulse instance, for example `https://planta.example.com/`. If PLANTA is
only reachable through a VPN, connect to it first.

## Step 1: log in once

```bash
planta-filler --url https://planta.example.com/ --login-only
```

A Firefox window opens. Because nothing is logged in yet, the tool waits and prints:

```
⏸️  Please log in in the browser window, then press ENTER here to continue...
```

Log in inside the browser as usual. When your timesheet is visible, switch back to
the terminal and press ENTER. The tool confirms:

```
✅ Logged in and timesheet visible; nothing was changed (--login-only)
```

The browser closes. Your session is now stored in a dedicated Firefox profile under
`~/.selenium_profiles/planta_firefox/` (this is what `--persistent`, the default,
does). Later runs, including headless ones, start without a login.

> Prefer not to store the session? Add `--no-persistent`; you will then log in on
> every run.

## Step 2: look at the plan before anything changes

Every run starts by printing a summary:

```
======================================================================
PLANTA TIMESHEET AUTOMATION
======================================================================
URL:          https://planta.example.com/
Week(s):      Week 39/2026 (Sep 21 - Sep 27)
Weekdays:     Mon, Tue, Wed, Thu, Fri
Action:       FILL
Strategy:     equal
Post-random.: 0.0
Browser:      visible, persistent profile
Delays:       0.2s between fields, 10.0s before closing
======================================================================
```

Read it once: it tells you which week and which days will be touched. Press
`Ctrl+C` if it is not what you expected; the browser is closed cleanly.

## Step 3: fill the current week

```bash
planta-filler --url https://planta.example.com/
```

Defaults: the current ISO week, Monday to Friday, strategy `equal`. For every day the
tool reads the attendance hours ("Anwesend") and the task rows, then types one value
per row so that the sum equals the attendance hours:

```
Processing 5 working day(s) with strategy EQUAL
📅 2026-09-21 (Mon) target 8.00h, current 0.00h -> [2.0, 2.0, 2.0, 2.0] (sum 8.00h)
   ✅ 4 change(s) applied
...
✅ Done: 20 cell(s) changed
⏳ Keeping the browser open for 10 seconds so you can verify the result...
```

Days with zero attendance hours (weekends, holidays, sick days) are skipped
automatically.

## Step 4: verify in PLANTA

While the countdown runs, look at the browser: the cells show the new values. PLANTA
saves a cell as soon as the input loses focus, which the tool triggers after every
value. If you want more time, run with `--close-delay 60`; if you do not need it, use
`--close-delay 0`.

## Step 5: undo, if needed

Set the same days back to zero:

```bash
planta-filler --url https://planta.example.com/ --reset
```

`--reset` respects `--week`, `--weekdays` and `--exclude` like a normal fill.

## What next?

- Try `--strategy random` for less uniform numbers, or `--post-randomization 0.1` to
  add a little variation to any strategy.
- Fill past weeks: `--week=-1` (last week), `--week=-3,-2,-1` (three weeks, oldest first).
- Build a reference week that mirrors how you really split your time:
  [tutorial-reference-file.md](tutorial-reference-file.md).
- Look up all options in [cli-reference.md](cli-reference.md).
