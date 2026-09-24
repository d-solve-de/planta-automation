# Reference file format

Reference files feed the `copy_reference` strategy. They are plain CSV files.

## Whole-week format (recommended)

```csv
,Mo,Di,Mi,Do,Fr
1,0.00,0.00,0.00,0.00,1.00
2,6.00,4.00,3.00,2.00,0.00
3,1.00,1.00,2.00,2.00,0.00
4,0.00,0.20,0.00,0.20,0.00
5,0.00,1.00,1.00,1.00,4.00
```

- **Header row:** the first cell is empty (or any text), the following cells name
  weekdays. Accepted labels, case-insensitive:

  | Weekday | Labels |
  |---|---|
  | Monday | `Mo`, `Mon`, `Monday`, `Montag` |
  | Tuesday | `Di`, `Tue`, `Tuesday`, `Dienstag` |
  | Wednesday | `Mi`, `Wed`, `Wednesday`, `Mittwoch` |
  | Thursday | `Do`, `Thu`, `Thursday`, `Donnerstag` |
  | Friday | `Fr`, `Fri`, `Friday`, `Freitag` |
  | Saturday | `Sa`, `Sat`, `Saturday`, `Samstag` |
  | Sunday | `So`, `Sun`, `Sunday`, `Sonntag` |

  Columns may be in any order and days may be missing; a missing weekday falls back
  to equal weights with a warning.
- **Data rows:** one per task row, in the order PLANTA shows them. The first column
  is a row index and is ignored; number it however you like.
- **Values are weights.** Only the ratio within a column matters. `6,4,0` and
  `3,2,0` produce the same result. Negative values are treated as 0.
  Decimal point or decimal comma (`1,5` inside quotes) both work; empty cells are 0.
- The number of data rows must equal the number of task rows in PLANTA, otherwise
  the day falls back to equal weights.

## Single-column format

A file with exactly one value column applies that column to every weekday:

```csv
,Pattern
1,3
2,1
3,0
```

## Unlabelled columns

If no header label matches but the file has several value columns, the columns are
used positionally: the first value column is Monday, the second Tuesday, and so on.

## Creating a file

- Export a week you filled by hand:
  `planta-filler --url URL --week=-1 --export-reference ~/planta/my_week.csv`
- Start from the templates in [`examples/reference-files/`](../examples/reference-files)
  (11 rows, edit to your row count).
- From Python: `planta_filler.reference_handler.write_reference_template("my_week.csv", num_slots=11)`.

## How the weights are applied

For a day with attendance hours `T`, weekday column `w` and free (non-excluded)
rows `F`:

1. Take the weights of the free rows: `w_F`.
2. Each free row gets `T_free * w_i / sum(w_F)`, where `T_free` is `T` minus the
   hours kept in excluded rows.
3. Values are rounded to two decimals; the rounding residual goes to the largest value
   so the total is exact.
4. If `sum(w_F)` is 0 (all free rows have weight 0) the free rows share the hours
   equally.

Excluded rows (`--exclude`) are removed *before* normalisation, so the remaining rows
keep their relative proportions.
