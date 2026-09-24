"""Reading and writing reference CSV files for the ``copy_reference`` strategy.

Whole-week format (recommended)::

    ,Mo,Di,Mi,Do,Fr
    1,6.00,4.00,3.00,2.00,0.00
    2,1.00,1.00,2.00,2.00,0.00

The first column is a row index and is ignored. Header labels may be German
or English, abbreviated or full (``Mo``/``Mon``/``Monday``), any case. A file
with a single value column is applied to every weekday.

Values are *weights*: only their ratio matters, the day total always comes
from PLANTA's attendance hours.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .config import DEFAULT_REFERENCE_FILE
from .exceptions import ReferenceFileError

WEEKDAY_HEADERS = {
    0: ("Mo", "Mon", "Monday", "Montag"),
    1: ("Di", "Tue", "Tuesday", "Dienstag"),
    2: ("Mi", "Wed", "Wednesday", "Mittwoch"),
    3: ("Do", "Thu", "Thursday", "Donnerstag"),
    4: ("Fr", "Fri", "Friday", "Freitag"),
    5: ("Sa", "Sat", "Saturday", "Samstag"),
    6: ("So", "Sun", "Sunday", "Sonntag"),
}
DEFAULT_WEEK_LABELS = ("Mo", "Di", "Mi", "Do", "Fr")


def _parse_float(cell: str) -> float:
    cell = cell.strip().replace(",", ".")
    if not cell:
        return 0.0
    try:
        return float(cell)
    except ValueError as exc:
        raise ReferenceFileError(f"not a number: {cell!r}") from exc


@dataclass
class ReferenceWeek:
    """Parsed reference file: one list of weights per header label."""

    columns: dict[str, list[float]] = field(default_factory=dict)
    source: str = ""

    @property
    def labels(self) -> list[str]:
        return list(self.columns)

    @property
    def num_rows(self) -> int:
        return len(next(iter(self.columns.values()))) if self.columns else 0

    def for_weekday(self, weekday_index: int, num_slots: int | None = None) -> list[float]:
        """Weights for a weekday (0 = Monday), checked against ``num_slots``."""
        column = self._column_for(weekday_index)
        if column is None:
            raise ReferenceFileError(f"{self.source}: no column for weekday {weekday_index} (labels: {self.labels})")
        if num_slots is not None and len(column) != num_slots:
            raise ReferenceFileError(
                f"{self.source}: reference has {len(column)} rows but PLANTA shows {num_slots} task rows"
            )
        return list(column)

    def _column_for(self, weekday_index: int) -> list[float] | None:
        wanted = {label.lower() for label in WEEKDAY_HEADERS.get(weekday_index, ())}
        for label, values in self.columns.items():
            if label.lower() in wanted:
                return values
        if len(self.columns) == 1:  # single-day file applies to every weekday
            return next(iter(self.columns.values()))
        labels = self.labels
        if len(labels) > 1 and weekday_index < len(labels):  # positional fallback
            return self.columns[labels[weekday_index]]
        return None


def load_reference_week(filepath: str | Path) -> ReferenceWeek:
    path = Path(filepath).expanduser()
    if not path.is_file():
        raise ReferenceFileError(f"reference file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
    if len(rows) < 2 or len(rows[0]) < 2:
        raise ReferenceFileError(f"{path}: expected a header row and at least one data row with values")
    header = [cell.strip() for cell in rows[0]]
    columns: dict[str, list[float]] = {}
    for col_idx in range(1, len(header)):
        label = header[col_idx] or f"col{col_idx}"
        values = []
        for row_number, row in enumerate(rows[1:], start=2):
            if col_idx >= len(row):
                raise ReferenceFileError(f"{path}: line {row_number} has too few columns")
            try:
                values.append(_parse_float(row[col_idx]))
            except ReferenceFileError as exc:
                raise ReferenceFileError(f"{path}: line {row_number}: {exc}") from exc
        columns[label] = values
    return ReferenceWeek(columns=columns, source=str(path))


def load_reference_for_weekday(filepath: str | Path | None, weekday_index: int, num_slots: int) -> list[float]:
    """Convenience wrapper: load the file and pick the weekday column."""
    return load_reference_week(filepath or DEFAULT_REFERENCE_FILE).for_weekday(weekday_index, num_slots)


def create_default_reference(num_slots: int) -> list[float]:
    """Equal weights, the fallback when no usable reference exists."""
    return [1.0] * max(0, num_slots)


def save_reference_week(filepath: str | Path, columns: dict[str, Sequence[float]]) -> Path:
    """Write a whole-week reference file; returns the written path."""
    path = Path(filepath).expanduser()
    labels = list(columns)
    if not labels:
        raise ValueError("at least one column is required")
    num_rows = len(columns[labels[0]])
    if any(len(columns[label]) != num_rows for label in labels):
        raise ValueError("all columns must have the same number of rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["", *labels])
        for row_idx in range(num_rows):
            writer.writerow([str(row_idx + 1), *(f"{columns[label][row_idx]:.2f}" for label in labels)])
    return path


def write_reference_template(filepath: str | Path, num_slots: int, labels: Sequence[str] = DEFAULT_WEEK_LABELS) -> Path:
    """Create a whole-week file with equal weights, ready to be edited."""
    return save_reference_week(filepath, {label: create_default_reference(num_slots) for label in labels})
