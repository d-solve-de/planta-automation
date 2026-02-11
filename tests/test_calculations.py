import math

from planta_filler.calculations import fill_day, apply_fill_values


def test_fill_day_equal_basic():
    res = fill_day(False, "equal", [], 8.0, [1.0, -1, -1, 2.0], retries=5, precision=2)
    assert res == [1.0, 2.5, 2.5, 2.0]


def test_fill_day_override_equal():
    res = fill_day(True, "equal", [0, 0, 0], 6.0, [2.0, 1.0, -1], retries=5, precision=2)
    assert res == [2.0, 2.0, 2.0]


def test_fill_day_exclude_and_copy_reference_fallback():
    # copy_reference with mismatched reference_day should fallback to equal
    res = fill_day(
        False,
        "copy_reference",
        [1, 0, 1, 0],
        10.0,
        [2.0, -1, 1.0, -1],
        retries=5,
        precision=2,
        reference_day=[1, 2, 3],  # wrong length to trigger exception path
    )
    assert len(res) == 4
    assert round(sum(res), 2) == 10.0
    assert res[0] == 2.0 and res[2] == 1.0


def test_apply_fill_values_with_post_randomization_sum():
    current_values = [1.0, -1, -1, 2.0]
    exclude_values = [0, 0, 0, 0]
    fill_values = [2.5, 2.5]
    res = apply_fill_values(current_values, exclude_values, fill_values, slots=2, post_randomization=0.2, precision=2)
    # Sum after fill should equal sum of previously filled (1.0 + 2.0) plus sum of fill_values
    assert math.isclose(sum(res), 3.0 + sum(fill_values), rel_tol=1e-9)
