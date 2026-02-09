import csv
from pathlib import Path
from config import DEFAULT_REFERENCE_FILE


def load_reference_day(filepath: str = None, num_slots: int = None) -> list:
    if filepath is None:
        filepath = DEFAULT_REFERENCE_FILE
    
    path = Path(filepath)
    
    if not path.exists():
        if num_slots:
            return create_default_reference(num_slots)
        return []
    
    with open(path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        if num_slots:
            return create_default_reference(num_slots)
        return []
    
    header = rows[0]
    if len(header) < 2:
        return create_default_reference(num_slots) if num_slots else []
    
    values = []
    for row in rows[1:]:
        if len(row) >= 2:
            try:
                val = float(row[1].strip()) if row[1].strip() else 0.0
                values.append(val)
            except ValueError:
                values.append(0.0)
    
    if num_slots and len(values) != num_slots:
        return create_default_reference(num_slots)
    
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
    path = Path(filepath)
    
    if not path.exists():
        default_values = create_default_reference(num_slots)
        save_reference_day(filepath, default_values)
        return filepath
    
    current_values = load_reference_day(filepath, None)
    if len(current_values) != num_slots:
        backup_path = path.with_suffix('.csv.bak')
        if path.exists():
            path.rename(backup_path)
        default_values = create_default_reference(num_slots)
        save_reference_day(filepath, default_values)
    
    return filepath
