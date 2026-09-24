import pytest

from planta_filler.strategies import (
    STRATEGIES,
    copy_reference_day,
    distribute_equal,
    distribute_random,
    enforce_exact_sum,
    validate_hours_and_slots,
)


def test_distribute_equal_exact_and_non_exact():
    assert distribute_equal(8.0, 4) == [2.0, 2.0, 2.0, 2.0]
    assert sorted(distribute_equal(2.25, 2)) == [1.12, 1.13]
    assert sorted(distribute_equal(10.0, 3)) == [3.33, 3.33, 3.34]


def test_distribute_equal_single_slot_and_zero_hours():
    assert distribute_equal(8.123, 1) == [8.12]
    assert distribute_equal(0.0, 3) == [0.0, 0.0, 0.0]


def test_distribute_random_length_sum_and_non_negative():
    for _ in range(20):
        res = distribute_random(8.0, 4)
        assert len(res) == 4
        assert round(sum(res), 2) == 8.0
        assert all(v >= 0 for v in res)


def test_copy_reference_day_proportions():
    assert copy_reference_day(10.0, 4, [0, 1, 1, 2]) == [0.0, 2.5, 2.5, 5.0]
    assert copy_reference_day(8.0, 1, [3]) == [8.0]


def test_copy_reference_day_rejects_bad_reference():
    with pytest.raises(ValueError):
        copy_reference_day(10.0, 4, [1, 1, 1])
    with pytest.raises(ValueError):
        copy_reference_day(10.0, 2, [0, 0])


def test_enforce_exact_sum_pushes_residual_onto_largest_value():
    assert enforce_exact_sum(5.0, [1.111, 1.111, 2.111], precision=2) == [1.11, 1.11, 2.78]
    assert enforce_exact_sum(1.0, [], precision=2) == []


def test_validate_hours_and_slots_behaviour():
    with pytest.raises(ValueError):
        validate_hours_and_slots(-1.0, 2)
    with pytest.raises(ValueError):
        validate_hours_and_slots(1.0, 0)
    with pytest.raises(TypeError):
        validate_hours_and_slots(1.0, 2.5)
    assert validate_hours_and_slots(2.345, 1, precision=2) == [2.35]
    assert validate_hours_and_slots(2.0, 2) is None


def test_strategy_registry():
    assert set(STRATEGIES) == {"random", "equal", "copy_reference"}
