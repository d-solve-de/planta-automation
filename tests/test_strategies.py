import math
import pytest

from planta_filler.strategies import (
    distribute_equal,
    distribute_random,
    copy_reference_day,
    enforce_exact_sum,
    validate_hours_and_slots,
    strategies,
)


def test_distribute_equal_exact_and_non_exact():
    assert distribute_equal(8.0, 4) == [2.0, 2.0, 2.0, 2.0]
    assert sorted(distribute_equal(2.25, 2)) == [1.12, 1.13]


def test_distribute_random_length_and_sum():
    res = distribute_random(8.0, 4)
    assert len(res) == 4
    assert round(sum(res), 2) == 8.0


def test_copy_reference_day_proportions():
    res = copy_reference_day(10.0, 4, [0, 1, 1, 2])
    assert res == [0.0, 2.5, 2.5, 5.0]


def test_enforce_exact_sum_adjusts_to_total():
    values = [1.111, 1.111, 1.111]
    out = enforce_exact_sum(5.0, values, precision=2)
    assert round(sum(out), 2) == 5.0


def test_validate_hours_and_slots_behaviour():
    # negative hours
    with pytest.raises(ValueError):
        validate_hours_and_slots(-1.0, 2)
    # zero/negative slots
    with pytest.raises(ValueError):
        validate_hours_and_slots(1.0, 0)
    # non-int slots
    with pytest.raises(TypeError):
        validate_hours_and_slots(1.0, 2.5)
    # one slot returns list with total rounded
    assert validate_hours_and_slots(2.345, 1, precision=2) == [2.35]


def test_strategies_dict_contains_expected():
    assert set(["random", "equal", "copy_reference"]).issubset(set(strategies.keys()))
