"""Hour distribution strategies.

Every strategy takes the hours to distribute and the number of free slots and
returns a list of values (already rounded to ``precision``) whose sum equals
``total_hours`` exactly. Strategies know nothing about PLANTA; the
:mod:`calculations` module maps their output onto the real task rows.

To add a strategy, implement a function with the signature

    def my_strategy(total_hours: float, slots: int, precision: int = 2, **kwargs) -> list[float]

and register it in :data:`STRATEGIES`. Then add its name to
``VALID_STRATEGIES`` in :mod:`config`.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence


def _check_hours_and_slots(total_hours: float, slots: int) -> None:
    if not isinstance(slots, int) or isinstance(slots, bool):
        raise TypeError(f"slots must be int, got {type(slots).__name__}")
    if slots <= 0:
        raise ValueError("slots must be a positive integer")
    if total_hours < 0:
        raise ValueError("total_hours must be non-negative")


def validate_hours_and_slots(total_hours: float, slots: int, precision: int = 2) -> list[float] | None:
    """Validate inputs and short-circuit the trivial single-slot case.

    Returns a ready result for ``slots == 1`` and ``None`` otherwise.
    """
    _check_hours_and_slots(total_hours, slots)
    if slots == 1:
        return [round(total_hours, precision)]
    return None


def enforce_exact_sum(total_hours: float, values: Sequence[float], precision: int = 2) -> list[float]:
    """Round ``values`` and push the rounding residual onto the largest value.

    Choosing the largest value keeps every entry non-negative and makes the
    correction deterministic.
    """
    if not values:
        return []
    rounded = [round(v, precision) for v in values]
    diff = round(total_hours - sum(rounded), precision)
    if diff:
        index = max(range(len(rounded)), key=lambda i: rounded[i])
        rounded[index] = round(rounded[index] + diff, precision)
    assert math.isclose(sum(rounded), total_hours, abs_tol=10**-precision), (
        f"sum {sum(rounded)} does not match total_hours {total_hours}"
    )
    return rounded


def distribute_equal(total_hours: float, slots: int, precision: int = 2, **_: object) -> list[float]:
    """Spread the hours evenly.

    >>> distribute_equal(8.0, 4)
    [2.0, 2.0, 2.0, 2.0]
    >>> sorted(distribute_equal(10.0, 3))
    [3.33, 3.33, 3.34]
    """
    shortcut = validate_hours_and_slots(total_hours, slots, precision)
    if shortcut is not None:
        return shortcut
    return enforce_exact_sum(total_hours, [total_hours / slots] * slots, precision)


def distribute_random(total_hours: float, slots: int, precision: int = 2, retries: int = 5, **_: object) -> list[float]:
    """Draw random weights and scale them so the sum matches ``total_hours``.

    >>> len(distribute_random(8.0, 4))
    4
    """
    shortcut = validate_hours_and_slots(total_hours, slots, precision)
    if shortcut is not None:
        return shortcut
    for _ in range(retries):
        weights = [random.uniform(0.0, 1.0) for _ in range(slots)]
        weight_sum = sum(weights)
        if weight_sum > 0:
            return enforce_exact_sum(total_hours, [total_hours * w / weight_sum for w in weights], precision)
    raise ValueError(f"random weights were all zero after {retries} retries")


def copy_reference_day(
    total_hours: float, slots: int, reference_day: Sequence[float], precision: int = 2, **_: object
) -> list[float]:
    """Scale the proportions of ``reference_day`` to ``total_hours``.

    ``reference_day`` must already be trimmed to the free slots.

    >>> copy_reference_day(10.0, 4, [0, 1, 1, 2])
    [0.0, 2.5, 2.5, 5.0]
    """
    if len(reference_day) != slots:
        raise ValueError(f"reference day has {len(reference_day)} entries but {slots} slots are free")
    shortcut = validate_hours_and_slots(total_hours, slots, precision)
    if shortcut is not None:
        return shortcut
    weights = [max(0.0, float(v)) for v in reference_day]
    weight_sum = sum(weights)
    if weight_sum <= 0:
        raise ValueError("reference day contains no positive weights")
    return enforce_exact_sum(total_hours, [total_hours * w / weight_sum for w in weights], precision)


StrategyFn = Callable[..., list[float]]

STRATEGIES: dict[str, StrategyFn] = {
    "equal": distribute_equal,
    "random": distribute_random,
    "copy_reference": copy_reference_day,
}

# Backwards-compatible alias.
strategies = STRATEGIES
