import math

import pytest

from planta_filler.calculations import apply_fill_values, apply_post_randomization, fill_day


def test_fill_blanks_only_equal():
    assert fill_day([1.0, -1, -1, 2.0], 8.0, "equal", override_mode=False) == [1.0, 2.5, 2.5, 2.0]


def test_override_rewrites_everything():
    assert fill_day([2.0, 1.0, -1], 6.0, "equal") == [2.0, 2.0, 2.0]


def test_excluded_rows_are_kept_and_reduce_the_budget():
    res = fill_day([2.0, 5.0, 1.0, 5.0], 10.0, "equal", exclude_values=[1, 0, 1, 0])
    assert res == [2.0, 3.5, 1.0, 3.5]


def test_no_free_slots_returns_kept_values():
    assert fill_day([2.0, 3.0], 10.0, "equal", exclude_values=[1, 1]) == [2.0, 3.0]


def test_over_booked_kept_rows_distribute_zero():
    assert fill_day([9.0, -1], 8.0, "equal", exclude_values=[1, 0]) == [9.0, 0.0]


def test_copy_reference_uses_only_free_rows():
    res = fill_day([-1] * 4, 8.0, "copy_reference", exclude_values=[1, 0, 0, 0], reference_day=[5, 1, 1, 2])
    assert res == [0.0, 2.0, 2.0, 4.0]


def test_copy_reference_falls_back_to_equal_when_reference_unusable():
    res = fill_day([-1, -1, -1, -1], 10.0, "copy_reference", reference_day=[1, 2, 3])
    assert res == [2.5, 2.5, 2.5, 2.5]
    res = fill_day([-1, -1], 10.0, "copy_reference", reference_day=[0, 0])
    assert res == [5.0, 5.0]


def test_random_strategy_shape_and_sum():
    res = fill_day([-1, -1, -1, -1], 8.0, "random")
    assert len(res) == 4
    assert round(sum(res), 2) == 8.0


def test_unknown_strategy_and_bad_input():
    with pytest.raises(KeyError):
        fill_day([-1], 8.0, "nope")
    with pytest.raises(TypeError):
        fill_day(["a"], 8.0, "equal")
    with pytest.raises(ValueError):
        fill_day([-1, -1], 8.0, "equal", exclude_values=[0])


def test_post_randomization_keeps_sum_and_sign():
    for _ in range(20):
        res = fill_day([1.0, -1, -1, 2.0], 8.0, "equal", override_mode=False, post_randomization=0.5)
        assert math.isclose(sum(res), 8.0, abs_tol=0.01)
        assert all(v >= 0 for v in res)
        assert res[0] == 1.0 and res[3] == 2.0


def test_apply_post_randomization_bounds():
    assert apply_post_randomization([2.0, 2.0], 0.0) == [2.0, 2.0]
    with pytest.raises(ValueError):
        apply_post_randomization([2.0], 1.0)


def test_apply_fill_values_mismatch_raises():
    with pytest.raises(ValueError):
        apply_fill_values([-1, -1], [0, 0], [1.0])
