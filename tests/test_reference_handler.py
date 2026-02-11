from pathlib import Path

from planta_filler.reference_handler import (
    load_reference_day,
    save_reference_day,
    ensure_reference_file,
    create_default_reference,
)


def test_create_default_reference_lengths():
    assert create_default_reference(0) == []
    assert create_default_reference(3) == [1.0, 1.0, 1.0]


def test_save_and_load_reference_day_roundtrip(tmp_path):
    path = tmp_path / "ref.csv"
    values = [1.0, 0.5, 2.25]
    save_reference_day(str(path), values, weekday_name="Mo")
    loaded = load_reference_day(str(path), num_slots=3)
    assert loaded == [1.0, 0.5, 2.25]


def test_load_reference_day_missing_creates_default(tmp_path):
    # When file missing and num_slots provided -> default
    loaded = load_reference_day(str(tmp_path / "missing.csv"), num_slots=2)
    assert loaded == [1.0, 1.0]


def test_ensure_reference_file_creates_and_backups(tmp_path):
    path = tmp_path / "ref.csv"

    # Create when missing
    ensure_reference_file(str(path), 2)
    assert path.exists()
    assert load_reference_day(str(path), 2) == [1.0, 1.0]

    # Backup and recreate when slot count changes
    ensure_reference_file(str(path), 3)
    assert path.exists() and (path.with_suffix('.csv.bak')).exists()
    assert load_reference_day(str(path), 3) == [1.0, 1.0, 1.0]
