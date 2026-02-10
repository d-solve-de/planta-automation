# =============================================================================
# strategies.py - Hour Distribution Strategies
# =============================================================================
# This module contains all distribution strategies for allocating hours across
# task slots. Each strategy takes total hours and number of slots, returning
# a list of values that sum exactly to total_hours.
#
# Available strategies:
# - distribute_equal: Equal distribution across all slots
# - distribute_random: Random distribution with scaling
# - copy_reference_day: Proportional copy from reference day
#
# Strategy function signature:
#   def strategy_name(total_hours: float, slots: int, precision: int=2, ...) -> list[float]
#
# Main functions:
# - validate_hours_and_slots(): Input validation helper
# - enforce_exact_sum(): Ensures values sum exactly to total_hours
# - distribute_equal(): Equal distribution
# - distribute_random(): Random distribution
# - copy_reference_day(): Copy from reference proportions
# =============================================================================

import random
import math
"""
thes strategies presented here all get the total_hours worked at the day and the number of slots 
and returns an array filled with values according to the strategy
the values are not in the right format to be filled in the cells in planta already, it is only a list of values to be used
"""

def validate_hours_and_slots(total_hours: float, slots: int, precision: int=2):
    if slots <= 0:
        raise ValueError("slots must be a positive integer")
    if total_hours < 0:
        raise ValueError("total_hours must be non-negative")
    if not isinstance(slots, int):
        raise TypeError(f"slots must be int, got {type(slots).__name__}")
    
    if slots == 0:
        return []
    if slots == 1:
        return [round(total_hours,precision)]
    return None

def enforce_exact_sum(total_hours: float, values: list, precision: int=2):
    if values == []:
        return values
    values = [round(v, precision) for v in values]
    diff = (total_hours - sum(values))
    if diff == 0:
        return values
    else:
        if abs(diff) > 0:
            index = random.randint(0, len(values)-1)
            values[index] = round((values[index] + diff),precision)
        assert sum(values) == total_hours, f"total_hours should match the sum of values but total_hours={total_hours} vs. sum(values)={sum(values)}"
        return values

def distribute_equal(total_hours: float, slots: int, precision: int=2):
    """
    >>> distribute_equal(8,1)
    [8]

    Exact division: 8 hours, 4 slots -> 2.0 each, sum 8.0
    >>> distribute_equal(8.0, 4)
    [2.0, 2.0, 2.0, 2.0]

    Non-exact division: 10 hours, 3 slots
    Base is round(10/3, 2) = 3.33,
    sum is corrected to 10.0 by adjusting the last value.
    >>> sorted(distribute_equal(10.0, 3))
    [3.33, 3.33, 3.34]

    >>> sorted(distribute_equal(2.25, 2))
    [1.12, 1.13]
    """
    result = validate_hours_and_slots(total_hours, slots, precision) 
    if result is not None:
        return result 
    
    base = (total_hours / slots)
    values = [base] * slots
    return enforce_exact_sum(total_hours, values, precision)

def distribute_random(total_hours, slots, precision: int=2, retries = 5):
    """Generate random numbers around equal distribution
    at the moment this is bullshit
    >>> distribute_random(8,1)
    [8]

    Exact division: 8 hours, 4 slots -> 2.0 each, sum 8.0
    >>> len(distribute_random(8.0, 4)) 
    4
    """
    result = validate_hours_and_slots(total_hours, slots, precision) 
    if result is not None:
        return result
    
    for _ in range(retries):
        values = [round(random.uniform(0, total_hours), precision) for _ in range(slots)]
        current_sum = sum(values)     # Scale to exact sum
        if current_sum > 0:
            values = [v * (total_hours / current_sum) for v in values]
            return enforce_exact_sum(total_hours, values, precision)
    raise ValueError(f"random values were all zero which is not allowed, please try again ({retries} many retries were performed already)")

def copy_reference_day(total_hours: float, slots: int, reference_day: list, precision:int=2):
    """
    expects to get only the parts of the reference day relevant - not the whole reference day
    """
    """
    Zero slots -> empty list:
    >>> copy_reference_day(8,1, [1])
    [8]

    >>> copy_reference_day(8.0, 4, [1,1,1,1])
    [2.0, 2.0, 2.0, 2.0]

    >>> copy_reference_day(10.0, 4, [0,1,1,2])
    [0.0, 2.5, 2.5, 5.0]
    """
    assert len(reference_day) == slots, f"reference day is not of same length as number of slots got: {len(reference_day)} vs. {slots}"
    result = validate_hours_and_slots(total_hours, slots)
    if result is not None:
        return result
    values = [total_hours * v / sum(reference_day) for v in reference_day]
    return enforce_exact_sum(total_hours, values, precision)

strategies = {'random': distribute_random, 'equal': distribute_equal, 'copy_reference': copy_reference_day}