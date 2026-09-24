# Example reference files

Templates for the `copy_reference` strategy. Each file has 11 task rows and the
columns Monday to Friday (`Mo`–`Fr`); edit the row count to match your PLANTA
timesheet or create a file from real data with `--export-reference`.

| File | Idea |
|---|---|
| `new_reference.csv` | A full week with different projects per day |
| `planning_week.csv` | Only the third row (planning) gets hours |
| `first-days.csv` | Only the first row gets hours, e.g. onboarding |
| `travel-day.csv` | Only the fourth row gets hours, e.g. travel |
| `vacation-homecoming.csv` | Only the fifth row gets hours |

Usage:

```bash
planta-filler --url URL --strategy copy_reference --reference-file examples/reference-files/new_reference.csv
```

Format details: [docs/reference-file-format.md](../../docs/reference-file-format.md).
