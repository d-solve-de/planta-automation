import pytest

from planta_filler.config import DEFAULT_REFERENCE_FILE
from planta_filler.exceptions import ReferenceFileError
from planta_filler.reference_handler import (
    ReferenceWeek,
    create_default_reference,
    load_reference_for_weekday,
    load_reference_week,
    save_reference_week,
    write_reference_template,
)


def test_packaged_default_file_is_valid():
    ref = load_reference_week(DEFAULT_REFERENCE_FILE)
    assert ref.labels == ["Mo", "Di", "Mi", "Do", "Fr"]
    assert ref.num_rows == 11
    assert ref.for_weekday(4)[0] == 1.0


def test_create_default_reference_lengths():
    assert create_default_reference(0) == []
    assert create_default_reference(3) == [1.0, 1.0, 1.0]


def test_roundtrip(tmp_path):
    path = tmp_path / "ref.csv"
    save_reference_week(path, {"Mo": [1.0, 0.5], "Di": [2.0, 2.25]})
    assert path.read_text().splitlines()[0] == ",Mo,Di"
    ref = load_reference_week(path)
    assert ref.for_weekday(0, 2) == [1.0, 0.5]
    assert ref.for_weekday(1) == [2.0, 2.25]


def test_labels_are_matched_case_insensitively_in_german_and_english(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text(",monday,TUE,Mittwoch\n1,1,2,3\n2,4,5,6\n")
    ref = load_reference_week(path)
    assert ref.for_weekday(0) == [1.0, 4.0]
    assert ref.for_weekday(1) == [2.0, 5.0]
    assert ref.for_weekday(2) == [3.0, 6.0]


def test_single_column_file_applies_to_every_weekday(tmp_path):
    path = tmp_path / "day.csv"
    path.write_text(",values\n1,1.5\n2,0.5\n")
    assert load_reference_for_weekday(path, 3, 2) == [1.5, 0.5]


def test_positional_fallback_and_missing_weekday(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text(",a,b\n1,1,2\n")
    ref = load_reference_week(path)
    assert ref.for_weekday(1) == [2.0]
    with pytest.raises(ReferenceFileError):
        ref.for_weekday(6)


def test_dimension_mismatch_raises(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text(",Mo\n1,1\n2,1\n")
    with pytest.raises(ReferenceFileError, match="2 rows"):
        load_reference_for_weekday(path, 0, 3)


def test_malformed_files_raise(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(ReferenceFileError, match="not found"):
        load_reference_week(missing)
    empty = tmp_path / "empty.csv"
    empty.write_text(",Mo\n")
    with pytest.raises(ReferenceFileError):
        load_reference_week(empty)
    bad = tmp_path / "bad.csv"
    bad.write_text(",Mo\n1,abc\n")
    with pytest.raises(ReferenceFileError, match="line 2"):
        load_reference_week(bad)
    short = tmp_path / "short.csv"
    short.write_text(",Mo,Di\n1,1\n")
    with pytest.raises(ReferenceFileError, match="too few columns"):
        load_reference_week(short)


def test_decimal_comma_is_accepted(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text(',Mo\n1,"1,5"\n')
    assert load_reference_week(path).for_weekday(0) == [1.5]


def test_write_reference_template(tmp_path):
    path = write_reference_template(tmp_path / "sub" / "template.csv", 3)
    ref = load_reference_week(path)
    assert ref.labels == ["Mo", "Di", "Mi", "Do", "Fr"]
    assert ref.for_weekday(2, 3) == [1.0, 1.0, 1.0]


def test_save_validates_columns(tmp_path):
    with pytest.raises(ValueError):
        save_reference_week(tmp_path / "x.csv", {})
    with pytest.raises(ValueError):
        save_reference_week(tmp_path / "x.csv", {"Mo": [1], "Di": [1, 2]})


def test_reference_week_empty():
    assert ReferenceWeek().num_rows == 0
