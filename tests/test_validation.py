import pytest

from planta_filler.validation import (
    validate_strategy,
    validate_weekdays,
    validate_delay,
    validate_url,
    validate_reference_file,
    validate_exclude_values,
    validate_precision,
    validate_all_inputs,
    ValidationError,
)


def test_validate_strategy_and_weekdays_ok():
    assert validate_strategy("equal") == "equal"
    assert validate_weekdays([0, 2, 4]) == [0, 2, 4]


def test_validate_strategy_invalid():
    with pytest.raises(ValidationError):
        validate_strategy("not-a-strategy")


def test_validate_weekdays_invalid():
    with pytest.raises(ValidationError):
        validate_weekdays([0, 7])


def test_validate_delay_bounds_and_invalid():
    assert validate_delay(0.0) == 0.0
    assert validate_delay(60.0) == 60.0
    with pytest.raises(ValidationError):
        validate_delay(-0.1)
    with pytest.raises(ValidationError):
        validate_delay(60.1)


def test_validate_url_valid_and_invalid():
    assert validate_url("https://example.com") == "https://example.com"
    with pytest.raises(ValidationError):
        validate_url("ftp://example.com")


def test_validate_reference_file_must_exist(tmp_path):
    csv_path = tmp_path / "ref.csv"
    csv_path.write_text("col,val\n1,1.0\n")
    assert validate_reference_file(str(csv_path)) == str(csv_path)
    with pytest.raises(ValidationError):
        validate_reference_file(str(tmp_path / "missing.csv"))
    with pytest.raises(ValidationError):
        validate_reference_file(str(tmp_path / "ref.txt"))


def test_validate_exclude_values_checks_length_and_values():
    assert validate_exclude_values([], 3) == []
    with pytest.raises(ValidationError):
        validate_exclude_values([0, 1], 3)
    with pytest.raises(ValidationError):
        validate_exclude_values([0, 2, 1], 3)


def test_validate_precision():
    assert validate_precision(2) == 2
    with pytest.raises(ValidationError):
        validate_precision(11)


def test_validate_all_inputs_collects_errors():
    with pytest.raises(ValidationError) as exc:
        validate_all_inputs(
            strategy="not-a-strategy",
            weekdays=[0, 8],
            delay=-1,
            close_delay=1000,
            url="bad",
            reference_file="nonexistent.csv",
        )
    # Contains multiple bullet lines
    assert "Validation failed:" in str(exc.value)
