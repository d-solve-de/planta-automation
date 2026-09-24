# Manual Test Checklist

This checklist helps you verify all CLI parameters and core behaviors manually in a running PLANTA environment.

Prerequisites
- Python 3.8+
- Firefox installed
- geckodriver on PATH
- Your PLANTA URL (HTTPS recommended)
- Optional: a safe/test PLANTA account to avoid modifying production data

Conventions used below
- Replace <URL> with your PLANTA base URL (e.g., https://planta.example.com/)
- Use a visible browser first (omit --headless) unless stated otherwise

1) Basic run (defaults)
- Command:
  - python3 -m planta_filler --url <URL>
- Expect:
  - Browser opens and navigates to <URL>
  - You are prompted to log in (if not using --persistent)
  - Current week is processed (Mon–Fri by default)
  - Fields are updated and blur events fired; see confirmation prints

2) --strategy
- equal:
  - python3 -m planta_filler --url <URL> --strategy equal
  - Expect equal distribution per day’s target (e.g., 8.0 → [2.0,2.0,2.0,2.0])
- random:
  - python3 -m planta_filler --url <URL> --strategy random
  - Expect varying values that sum to the target
- copy_reference:
  - Ensure default_reference.csv exists (src/planta_filler/data or project root if you override)
  - python3 -m planta_filler --url <URL> --strategy copy_reference
  - Expect values proportional to the reference pattern

3) --weekdays
- Monday only:
  - python3 -m planta_filler --url <URL> --strategy equal --weekdays 0
  - Expect only Monday fields updated
- Mon, Wed, Fri:
  - python3 -m planta_filler --url <URL> --strategy equal --weekdays 0,2,4
  - Expect only those days updated

4) --week (single)
- Last week:
  - python3 -m planta_filler --url <URL> --week -1 --strategy equal
  - Expect the previous week is shown and processed
- Specific ISO week:
  - python3 -m planta_filler --url <URL> --week 2026-W06 --strategy equal
  - Expect week 6 of 2026 is shown and processed

5) --week (multiple / ordered)
- Current then last:
  - python3 -m planta_filler --url <URL> --week 0,-1 --strategy equal
  - Expect the current week is processed first, then one click to previous week, then processed
- Two previous weeks then current:
  - python3 -m planta_filler --url <URL> --week -2,-1,0 --strategy equal
  - Expect sequential navigation one week at a time in the given order with updates at each step

6) --reset
- Reset current week:
  - python3 -m planta_filler --url <URL> --reset --week 0
  - Expect all hour inputs set to 0 for days included by --weekdays (default Mon–Fri)

7) --persistent
- First run:
  - python3 -m planta_filler --url <URL> --persistent
  - Log in once; close completes; rerun the same command
- Second run:
  - Expect login to be skipped (session reused)

8) --headless
- Command:
  - python3 -m planta_filler --url <URL> --headless --persistent
- Expect no visible browser; values still updated

9) --delay and --close-delay
- Faster updates:
  - python3 -m planta_filler --url <URL> --strategy equal --delay 0.05 --close-delay 0
  - Expect quicker typing and immediate close
- Slower updates:
  - python3 -m planta_filler --url <URL> --strategy equal --delay 0.5 --close-delay 5
  - Expect visibly slower typing and a 5-second post-run window

10) --post-randomization
- Command:
  - python3 -m planta_filler --url <URL> --strategy equal --post-randomization 0.2
- Expect values slightly adjusted around equal distribution while sums remain exact (e.g., [2.0,2.0,2.0,2.0] → ~[2.01,1.98,2.02,1.99])

11) Combined example (complex)
- Command:
  - python3 -m planta_filler --url <URL> \
    --strategy copy_reference \
    --week 0,-1 \
    --weekdays 0,2,4 \
    --post-randomization 0.1 \
    --delay 0.1 \
    --close-delay 3
- Expect:
  - Current week Mon,Wed,Fri processed according to reference with slight variation
  - Navigates back one week and repeats
  - Waits 3 seconds before closing

12) Help / Manual
- Help:
  - python3 -m planta_filler --help
- Manual page:
  - python3 -m planta_filler --man

13) Negative tests (validate error handling)
- Invalid URL:
  - python3 -m planta_filler --url not-a-url
  - Expect validation error: URL must start with http:// or https://
- Invalid strategy:
  - python3 -m planta_filler --url <URL> --strategy not-a-strategy
  - Expect validation error listing valid strategies
- Invalid weekdays:
  - python3 -m planta_filler --url <URL> --weekdays 0,8
  - Expect validation error (weekdays must be 0–6)
- Invalid week spec:
  - python3 -m planta_filler --url <URL> --week ABC
  - Expect invalid week specification error and exit

Notes
- Navigation uses the previous/next week controls and moves one week per click.
- If your PLANTA instance uses different selectors for week navigation or input fields, update src/planta_filler/config.py accordingly.
- For copy_reference strategy, ensure your default_reference.csv aligns with the number of task rows (the code auto-adapts when possible).
