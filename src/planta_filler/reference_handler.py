# =============================================================================
# reference_handler.py - Reference Week/Day File Management
# =============================================================================
# This module handles loading, saving, and auto-adapting reference files
# for the copy_reference strategy. Reference files can contain a single day
# or a whole week. A whole-week file has a header row with an index column
# followed by one column per weekday.
# =============================================================================

import csv
from pathlib import Path
from .config import DEFAULT_REFERENCE_FILE

# Supported weekday header names (German and English abbreviations and full names)
WEEKDAY_HEADERS = {
    0: ["Mo", "Mon", "Monday"],
    1: ["Di", "Tue", "Tuesday"],
    2: ["Mi", "Wed", "Wednesday"],
    3: ["Do", "Thu", "Thursday"],
    4: ["Fr", "Fri", "Friday"],
    5: ["Sa", "Sat", "Saturday"],
    6: ["So", "Sun", "Sunday"],
}

    
def _read_csv(filepath: str) -> list[list[str]]:
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        return list(reader)


def load_reference_day(filepath: str = '', num_slots: int = 0) -> list:
    """Load a single-day reference from a file with exactly one data column.
    Falls back to default if file missing or lengths mismatch.
    """
    if filepath == '':
        filepath = DEFAULT_REFERENCE_FILE
    rows = _read_csv(filepath)
    if len(rows) < 2:
        return create_default_reference(num_slots) if num_slots else []
    header = rows[0]
    # Expect at least index + one value column
    if len(header) < 2:
        return create_default_reference(num_slots) if num_slots else []
    values = []
    for row in rows[1:]:
        if len(row) >= 2:
            try:
                val = float(row[1].strip()) if row[1].strip() else 0.0
            except ValueError:
                val = 0.0
            values.append(val)
    if num_slots and len(values) != num_slots:
        return create_default_reference(num_slots)
    return values


def load_reference_week(filepath: str) -> dict:
    """Load a whole-week reference file.
    Returns a dict mapping weekday header to list of values.
    The first column is an index; subsequent columns are weekdays.
    """
    rows = _read_csv(filepath)
    if len(rows) < 2:
        return {}
    header = rows[0]
    if len(header) < 3:
        # Not a week-format; treat as single-day with the given header
        return {header[1] if len(header) > 1 else "Mo": load_reference_day(filepath, 0)}
    # Build columns from header starting at col=1
    result = {}
    for col_idx in range(1, len(header)):
        day_name = header[col_idx].strip()
        values = []
        for row in rows[1:]:
            if len(row) > col_idx:
                try:
                    val = float(row[col_idx].strip()) if row[col_idx].strip() else 0.0
                except ValueError:
                    val = 0.0
                values.append(val)
        result[day_name] = values
    return result


def load_reference_for_weekday(filepath: str, weekday_index: int, num_slots: int) -> list:
    """Load the reference column for the given weekday from a week file.
    Supports German/English headers and full names; case-insensitive.
    If header label is not found but the file appears to be a week file (>=3 columns),
    select the column by position (weekday_index + 1). If a valid reference cannot be
    derived (missing file, malformed, or dimension mismatch), raise ValueError so the
    caller can explicitly fall back and report it.
    """
    rows = _read_csv(filepath)
    if not rows:
        raise ValueError(f"Reference file missing or unreadable: {filepath}")
    header = rows[0]
    # Normalize header labels
    norm_header = [h.strip().lower() for h in header]
    labels = {lbl.lower() for lbl in WEEKDAY_HEADERS.get(weekday_index, [])}
    col_idx = None
    for i in range(1, len(norm_header)):
        if norm_header[i] in labels:
            col_idx = i
            break
    # If not found by label, try positional selection for week-style files
    if col_idx is None and len(header) >= 3:
        pos_idx = 1 + weekday_index
        if pos_idx < len(header):
            col_idx = pos_idx
    if col_idx is None:
        # Fall back to single-day style (second column); if that fails dimensionally, raise
        values = load_reference_day(filepath, num_slots)
        if num_slots and len(values) != num_slots:
            raise ValueError(f"Reference file malformed or wrong dimensions: {filepath}")
        return values
    values = []
    for row in rows[1:]:
        if len(row) > col_idx:
            try:
                val = float(row[col_idx].strip()) if row[col_idx].strip() else 0.0
            except ValueError:
                val = 0.0
            values.append(val)
    if num_slots and len(values) != num_slots:
        raise ValueError(f"Reference dimension mismatch: expected {num_slots}, got {len(values)} in {filepath}")
    return values


def create_default_reference(num_slots: int) -> list:
    if num_slots <= 0:
        return []
    return [1.0] * num_slots


def save_reference_day(filepath: str, values: list, weekday_name: str = "Mo") -> None:
    path = Path(filepath)
    rows = [["", weekday_name]]
    for i, val in enumerate(values, 1):
        rows.append([str(i), f"{val:.2f}"])
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def ensure_reference_file(filepath: str, num_slots: int) -> str:
    """Ensure a reference file exists and has the expected slot count.
    For week files, we check the first weekday column's length.

    If we need to create a new default file due to missing or wrong dimensions and
    the given path is not already inside the package data dir, we will write the
    new file into the package data directory (next to the default file) and return
    that path instead, leaving the original path untouched.
    """
    path = Path(filepath)
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    default_path = Path(DEFAULT_REFERENCE_FILE).resolve()

    if not path.exists():
        default_values = create_default_reference(num_slots)
        # Only redirect to data dir for the default packaged file
        if path.resolve() == default_path:
            target_path = default_path
        else:
            target_path = path
        save_reference_day(str(target_path), default_values)
        return str(target_path)
    rows = _read_csv(filepath)
    if not rows or len(rows) < 2:
        default_values = create_default_reference(num_slots)
        target_path = default_path if path.resolve() == default_path else path
        save_reference_day(str(target_path), default_values)
        return str(target_path)
    header = rows[0]
    # Determine a sample column to validate length: prefer second column
    sample_col = 1 if len(header) > 1 else None
    if sample_col is None:
        default_values = create_default_reference(num_slots)
        target_path = default_path if path.resolve() == default_path else path
        save_reference_day(str(target_path), default_values)
        return str(target_path)
    current_values = []
    for row in rows[1:]:
        if len(row) > sample_col:
            try:
                val = float(row[sample_col].strip()) if row[sample_col].strip() else 0.0
            except ValueError:
                val = 0.0
            current_values.append(val)
    if len(current_values) != num_slots:
        backup_path = path.with_suffix('.csv.bak')
        if path.exists():
            path.rename(backup_path)
        default_values = create_default_reference(num_slots)
        target_path = default_path if path.resolve() == default_path else path
        save_reference_day(str(target_path), default_values)
        return str(target_path)
    return str(path)
