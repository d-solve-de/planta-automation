"""Turn a strategy result into the full list of values for one day.

Value encoding used throughout this module:

* ``current_values[i] == -1`` means the cell is blank and may be filled.
* any other value is an existing entry.
* ``exclude_values[i] == 1`` marks a row that must never be touched.

:func:`fill_day` decides which cells are free, asks the strategy for that many
values and writes them back into the right positions. Rows that are kept
(excluded or, without override, already filled) reduce the hours that are
distributed so the day total still matches the target.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from .config import DEFAULT_PRECISION, DEFAULT_RETRIES
from .strategies import STRATEGIES, enforce_exact_sum

BLANK = -1


def _free_slot_indices(working_values: Sequence[float], exclude_values: Sequence[int]) -> list[int]:
    return [
        i for i, (value, excluded) in enumerate(zip(working_values, exclude_values)) if value == BLANK and not excluded
    ]


def apply_post_randomization(values: Sequence[float], factor: float, precision: int = DEFAULT_PRECISION) -> list[float]:
    """Jitter each value by up to ``factor`` of itself, keeping the exact sum.

    ``factor`` must be in ``[0, 1)`` so values stay non-negative.
    """
    if not values or factor <= 0:
        return list(values)
    if factor >= 1:
        raise ValueError(f"post_randomization must be below 1, got {factor}")
    jittered = [v + factor * random.uniform(-v, v) for v in values]
    return enforce_exact_sum(round(sum(values), precision), jittered, precision)


def apply_fill_values(
    current_values: Sequence[float],
    exclude_values: Sequence[int],
    fill_values: Sequence[float],
    post_randomization: float = 0.0,
    precision: int = DEFAULT_PRECISION,
) -> list[float]:
    """Place ``fill_values`` into the blank, non-excluded positions of ``current_values``."""
    free = _free_slot_indices(current_values, exclude_values)
    if len(free) != len(fill_values):
        raise ValueError(f"{len(free)} free slots but {len(fill_values)} fill values were provided")
    values = apply_post_randomization(fill_values, post_randomization, precision)
    result = [max(0.0, float(v)) if v != BLANK else 0.0 for v in current_values]
    for index, value in zip(free, values):
        result[index] = max(0.0, round(value, precision))
    return result


def fill_day(
    current_values: Sequence[float],
    total_hours: float,
    strategy: str = "equal",
    *,
    exclude_values: Sequence[int] | None = None,
    override_mode: bool = True,
    reference_day: Sequence[float] | None = None,
    post_randomization: float = 0.0,
    precision: int = DEFAULT_PRECISION,
    retries: int = DEFAULT_RETRIES,
) -> list[float]:
    """Compute the values every task row of one day should end up with.

    With ``override_mode`` every non-excluded row is rewritten. Without it only
    blank rows (``-1``) are filled and existing entries are kept.

    >>> fill_day([1.0, -1, -1, 2.0], 8.0, "equal", override_mode=False)
    [1.0, 2.5, 2.5, 2.0]
    >>> fill_day([2.0, 1.0, -1], 6.0, "equal")
    [2.0, 2.0, 2.0]
    >>> fill_day([2.0, -1, 1.0, -1], 10.0, "equal", exclude_values=[1, 0, 1, 0], override_mode=False)
    [2.0, 3.5, 1.0, 3.5]
    """
    if strategy not in STRATEGIES:
        raise KeyError(f"strategy {strategy!r} not defined; choose one of {sorted(STRATEGIES)}")
    if not all(isinstance(v, (int, float)) for v in current_values):
        raise TypeError("current_values must contain numbers only")

    exclude = list(exclude_values) if exclude_values else [0] * len(current_values)
    if len(exclude) != len(current_values):
        raise ValueError(f"exclude_values has {len(exclude)} entries but current_values has {len(current_values)}")

    working = list(current_values)
    if override_mode:
        working = [BLANK if not excluded else value for value, excluded in zip(working, exclude)]

    free = _free_slot_indices(working, exclude)
    kept_hours = sum(v for v in working if v != BLANK)
    hours_to_distribute = round(max(0.0, total_hours - kept_hours), precision)

    if not free:
        return [max(0.0, float(v)) for v in working]

    if strategy == "copy_reference":
        fill_values = _copy_reference_fill(hours_to_distribute, free, reference_day, precision)
    else:
        fill_values = STRATEGIES[strategy](hours_to_distribute, len(free), precision=precision, retries=retries)

    return apply_fill_values(working, exclude, fill_values, post_randomization, precision)


def _copy_reference_fill(
    hours: float, free: list[int], reference_day: Sequence[float] | None, precision: int
) -> list[float]:
    """Use the reference proportions of the free rows; fall back to equal if unusable."""
    if reference_day is not None and len(reference_day) > max(free):
        trimmed = [max(0.0, float(reference_day[i])) for i in free]
        if sum(trimmed) > 0:
            return STRATEGIES["copy_reference"](hours, len(free), trimmed, precision=precision)
    return STRATEGIES["equal"](hours, len(free), precision=precision)
