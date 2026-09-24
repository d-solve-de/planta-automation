# Tutorial: build and use a reference week

`equal` and `random` do not know which projects you actually work on. The
`copy_reference` strategy does: it takes the *proportions* of a reference week and
scales them to each day's attendance hours. This tutorial shows the fastest way to
create such a file from a week you filled by hand, and how to use it from then on.

Prerequisites: the [first-run tutorial](tutorial-first-run.md) (you are logged in
and know the summary output).

## Step 1: fill one week by hand in PLANTA

Pick a typical week and enter the hours manually in PLANTA, exactly as you want them
distributed. Only the ratio per day matters later; 6h/2h and 3h/1h describe the same
split.

## Step 2: export that week as a reference file

```bash
planta-filler --url https://planta.example.com/ --week=-1 --export-reference ~/planta/my_week.csv
```

`--week` selects the week you filled (here: last week). The tool reads the values
from PLANTA, writes the CSV and exits without changing anything:

```
Exported 5 day(s) x 11 rows to /home/you/planta/my_week.csv
```

Open the file. It looks like this (one column per weekday, one line per task row in
the order PLANTA shows them):

```csv
,Mo,Di,Mi,Do,Fr
1,0.00,0.00,0.00,0.00,1.00
2,0.00,0.00,0.00,0.00,0.00
3,6.00,4.00,3.00,2.00,0.00
4,1.00,1.00,2.00,2.00,0.00
5,0.00,0.20,0.00,0.20,0.00
6,0.00,1.00,1.00,1.00,4.00
```

You can also write the file from scratch; the format is described in
[reference-file-format.md](reference-file-format.md), and
[`examples/reference-files/`](../examples/reference-files) contains templates.

## Step 3: adjust the weights

Edit the numbers in any text editor or spreadsheet (save as CSV). Common tweaks:

- A row that must always get a fixed share on Fridays: put the share in the `Fr` column only.
- A row that should never be filled by the tool: set it to `0.00` everywhere, or protect it
  with `--exclude` at run time (see below).
- A single pattern for every day: keep just one value column, e.g. `,Pattern` in the header.

Rows must stay in PLANTA's order and the number of lines must match the number of
task rows. If a project is added or removed in PLANTA, export again or edit the file.

## Step 4: use the reference

```bash
planta-filler --url https://planta.example.com/ --strategy copy_reference --reference-file ~/planta/my_week.csv
```

For each day the tool takes the column of that weekday, scales it to the attendance
hours and types the result:

```
Reference file: /home/you/planta/my_week.csv (11 rows, columns Mo, Di, Mi, Do, Fr)
📅 2026-09-21 (Mon) target 7.50h, current 0.00h -> [0.0, 0.0, 6.43, 1.07, 0.0, 0.0] (sum 7.50h)
```

Add `--post-randomization 0.1` if the numbers should not look like a copy every week.

## Step 5: protect rows that are already correct

Say row 0 (the first task row) holds a fixed meeting slot you booked manually.
Exclude it and the tool distributes the *remaining* hours over the other rows:

```bash
planta-filler --url https://planta.example.com/ --strategy copy_reference \
  --reference-file ~/planta/my_week.csv --exclude 0
```

Indices are zero-based and count the task rows from the top.

## What happens when the file does not fit

If the file is missing, malformed, or has a different number of rows than PLANTA,
the tool prints a warning and falls back to equal weights for the affected days. It
never modifies your file. Run `--export-reference` again to get a file with the
current row count.

## Recommended daily command

Once you are happy with the file, this is a good standing command:

```bash
planta-filler --url https://planta.example.com/ --strategy copy_reference \
  --reference-file ~/planta/my_week.csv --post-randomization 0.05 --close-delay 5
```

See [how-to.md](how-to.md) for running it on a schedule or headless.
