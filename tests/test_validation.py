import pytest

from planta_filler.validation import (
    ValidationError,
    parse_int_list,
    validate_all_inputs,
    validate_delay,
    validate_exclude_indices,
    validate_post_randomization,
    validate_precision,
    validate_reference_file,
    validate_strategy,
    validate_url,
    validate_week_specs,
    validate_weekdays,
)


def test_parse_int_list():
    assert parse_int_list("0, 2,4,", "x") == [0, 2, 4]
    assert parse_int_list("", "x") == []
    assert parse_int_list(None, "x") == []
    with pytest.raises(ValidationError, match="--exclude"):
        parse_int_list("1,a", "--exclude")


def test_validate_strategy():
    assert validate_strategy("equal") == "equal"
    with pytest.raises(ValidationError):
        validate_strategy("not-a-strategy")


def test_validate_weekdays():
    assert validate_weekdays([0, 2, 4, 2]) == [0, 2, 4]
    with pytest.raises(ValidationError):
        validate_weekdays([0, 7])
    with pytest.raises(ValidationError):
        validate_weekdays([])


def test_validate_delay_bounds():
    assert validate_delay(0.0) == 0.0
    assert validate_delay(60.0) == 60.0
    with pytest.raises(ValidationError):
        validate_delay(-0.1)
    with pytest.raises(ValidationError, match="close-delay"):
        validate_delay(60.1, "close-delay")


def test_validate_url():
    assert validate_url("https://example.com") == "https://example.com"
    for bad in ("ftp://example.com", "", "example.com"):
        with pytest.raises(ValidationError):
            validate_url(bad)


def test_validate_reference_file_normalises_path(tmp_path, monkeypatch):
    csv_path = tmp_path / "ref.csv"
    csv_path.write_text("col,val\n1,1.0\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert validate_reference_file("~/ref.csv") == str(csv_path.resolve())
    with pytest.raises(ValidationError, match="not found"):
        validate_reference_file(str(tmp_path / "missing.csv"))
    (tmp_path / "ref.txt").write_text("x")
    with pytest.raises(ValidationError, match=r"\.csv"):
        validate_reference_file(str(tmp_path / "ref.txt"))


def test_validate_exclude_indices():
    assert validate_exclude_indices([3, 1, 1]) == [1, 3]
    with pytest.raises(ValidationError):
        validate_exclude_indices([-1])


def test_validate_post_randomization():
    assert validate_post_randomization(0.0) == 0.0
    assert validate_post_randomization(0.99) == 0.99
    for bad in (-0.1, 1.0):
        with pytest.raises(ValidationError):
            validate_post_randomization(bad)


def test_validate_precision():
    assert validate_precision(2) == 2
    with pytest.raises(ValidationError):
        validate_precision(11)


def test_validate_week_specs():
    assert validate_week_specs("0,-1, 2024-W05") == ["0", "-1", "2024-W05"]
    assert validate_week_specs("") == ["0"]
    with pytest.raises(ValidationError):
        validate_week_specs("abc")


def test_validate_all_inputs_collects_all_errors():
    with pytest.raises(ValidationError) as exc:
        validate_all_inputs(
            url="bad",
            strategy="not-a-strategy",
            weekdays=[0, 8],
            delay=-1,
            close_delay=1000,
            week="nope",
            post_randomization=2,
            exclude_indices=[-1],
            reference_file="nonexistent.csv",
        )
    message = str(exc.value)
    assert message.startswith("Validation failed:")
    assert message.count("\n  - ") == 9


def test_validate_all_inputs_returns_normalised_values():
    result = validate_all_inputs(
        url="https://x", strategy="equal", weekdays=[4, 0], delay=0, close_delay=0, week="-1,0", exclude_indices=[2, 2]
    )
    assert result["weekdays"] == [4, 0]
    assert result["week_specs"] == ["-1", "0"]
    assert result["exclude_indices"] == [2]
    assert result["reference_file"] is None
