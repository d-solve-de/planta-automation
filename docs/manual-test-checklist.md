# Manual test checklist

The unit tests cover everything except the real PLANTA DOM. Run this checklist against
a **test account** after changing `browser.py`, `config.SELECTORS`, or before a
release. Replace `URL` with your PLANTA URL.

Prerequisites: Python 3.9+, Firefox, geckodriver on `PATH`, `pip3 install -e .`.

| # | Command | Expect |
|---|---|---|
| 1 | `planta-filler --url URL --login-only` | Browser opens; prompt to log in; after ENTER "Logged in and timesheet visible"; browser closes. |
| 2 | `planta-filler --url URL --login-only` (again) | No prompt; finishes immediately (persistent profile works). |
| 3 | `planta-filler --url URL --close-delay 3` | Summary printed; Mon–Fri of the current week filled equally; sums equal the attendance hours; cells still hold the values after reload. |
| 4 | `planta-filler --url URL --strategy random` | Different values per row, exact day totals. |
| 5 | `planta-filler --url URL --strategy copy_reference --reference-file examples/reference-files/first-days.csv` | If the row count matches: proportions of the file; otherwise a warning and equal weights. |
| 6 | `planta-filler --url URL --weekdays 0,2` | Only Monday and Wednesday change. |
| 7 | `planta-filler --url URL --exclude 0` | First task row keeps its value; the rest shares the remaining hours. |
| 8 | `planta-filler --url URL --post-randomization 0.2` | Values vary around the equal split; totals still exact. |
| 9 | `planta-filler --url URL --week=-1` | Browser shows the previous week; that week is filled. |
| 10 | `planta-filler --url URL --week=-2,-1,0` | Navigates two weeks back, then forward one week at a time; each week filled. |
| 11 | `planta-filler --url URL --week 2026-W05` | That ISO week is shown and filled. |
| 12 | `planta-filler --url URL --reset --weekdays 4` | Friday cells are 0, other days untouched. |
| 13 | `planta-filler --url URL --export-reference /tmp/ref.csv` | CSV with one column per weekday and one line per task row; nothing changed in PLANTA. |
| 14 | `planta-filler --url URL --headless --close-delay 0` | No window; values updated (check in PLANTA). |
| 15 | `planta-filler --url URL --no-persistent` | Login prompt appears; nothing stored afterwards. |
| 16 | `planta-filler --url URL --delay 0.05 --close-delay 0` | Fast run; verify values were saved (increase delay if not). |
| 17 | `planta-filler --url https://example.com/` | Error about the page title, exit code 1, browser closed. |
| 18 | `planta-filler --url not-a-url --weekdays 0,8 --week x` | All three validation errors listed, exit code 2, no browser. |
| 19 | `Ctrl+C` during a run | "Interrupted", browser closed, exit code 130. |
| 20 | `planta-filler --help`, `--man`, `--version` | Help, manual and version printed. |

Note what you tested in the pull request description.
