import copy
import random
from strategies import strategies

def apply_fill_values(current_values:list[float], exclude_values:list[int], fill_values:list[float], slots:int, post_randomization=0.2, precision:int=2):
    # NOTE: post randomization applies to all values, also the excluded ones
    """
    Fill only positions where:
      - current_values[i] == -1 (blank)
      - exclude_values[i] == 0 (not excluded)
    Leave excluded positions (exclude_values[i] == 1) untouched.
    """
    res = copy.deepcopy(current_values)
    if post_randomization:
        # [1, 2, 3, 0, 0]
        # # apply very basic randomization - decrease one value randomly, increase another randomly
        # if len(fill_values) % 2 == 0:
        #     pass
        # else:
        #     # pick random index that is not included in randomization
        #     randomized_fill_values[0] = fill_values[0]
        assert post_randomization < 1, f"randomization parameter has to be lower than 1, so the values are guaranteed to be non-negative, got randomization parameter {post_randomization}"
        random_values = [value + round((post_randomization* random.uniform(-value, value)), 2) for value in fill_values] # add randomization to entries
        # ensure values still add up tot total_hours
        diff = sum(fill_values) - sum(random_values)
        if abs(diff) // len(random_values) >= 1/(10**precision): # first apply diff to all values the same
            random_values = [v + (diff/len(random_values)) for v in random_values]
        diff = sum(fill_values) - sum(random_values)
        indices_positive = [i for i, val in enumerate(random_values) if (val+diff) > 0]
        if indices_positive:
            random_index = random.choice(indices_positive)
            random_values[random_index] += diff
        assert sum(random_values) == sum(fill_values), f"Post randomization failed - sum does not add up got {random_values} with sum {sum(random_values)} but should be {sum(fill_values)}"
        fill_values = random_values
    
    fill_idx = 0
    for i, (cv, ex) in enumerate(zip(res, exclude_values)):
        if ex == 1:
            continue  # skip excluded positions
        if cv == -1:
            if fill_idx >= len(fill_values):
                raise ValueError(
                    f"Not enough fill_values: needed {slots}, got {len(fill_values)}"
                )
            res[i] = max(fill_values[fill_idx], 0)
            fill_idx += 1
    assert fill_idx == slots, f"Expected to fill {slots} blanks, filled {fill_idx}"
    res = [max(0.0,v) for v in res]
    return res

def fill_day(override_mode: bool, strategy: str, exclude_values: list[int], total_hours: float, current_values: list[float], retries: int, precision:int, reference_day = [], post_randomization=0):
    """
    looks up current values
    gets user input
    calculates values to be filled
    and returns all values that should be in the column
    
    assert that current_values is given in the following form:
    current_values = [1, 3, 2.5, -1, -1, 2.34, 0]
    -1 := empty, not set
    int := entry filled with the number

    override also uses the fill blanks only mode but with the blanks set accordingly

    current_values = [1,2,3,4,5,6,-1, -1]
    override_mode = True --> set all current values to -1:= empty cell
    --> then follow same logic as override_mode = False
    current_values = [-1,-1,-1,-1,-1,-1,-1, -1]
    exclude_values = [1,0,0,0,1,1, 0,  1]

    current_values = [1,2,3,4,5,6,-1, -1]
    exclude_values = [1,0,0,0,1,1, 0,  1]
    override_mode = False

    --> slots = count how many cells are -1 in current values and 0 in exclude values
    total_hours = total_hours - sum(current_values) where current_values != -1 # exclude already filled values
    fill calculated values where current_values == -1 and exclude_values = 0


    Test Cases:
    1) Fill two blanks equally, no excludes:
       total_hours = 8.0, current_values sum of filled = 3.0 -> distribute 5.0 over 2 slots
       >>> fill_day(False, "equal", [], 8.0, [1.0, -1, -1, 2.0], retries=5, precision=2)
       [1.0, 2.5, 2.5, 2.0]

    2) Override and fill all positions equally:
       override_mode=True sets all cells to -1, then 6.0 hours across 3 slots
       >>> fill_day(True, "equal", [0, 0, 0], 6.0, [2.0, 1.0, -1], retries=5, precision=2)
       [2.0, 2.0, 2.0]

    3) Exclude some already-filled positions; fill only non-excluded blanks:
       total_hours = 10.0, filled sum = 3.0 -> 7.0 over the 2 non-excluded blanks
       exclude_values marks indices 0 and 2 as excluded (they are already filled)
       >>> fill_day(False, "equal", [1, 0, 1, 0], 10.0, [2.0, -1, 1.0, -1], retries=5, precision=2)
       [2.0, 3.5, 1.0, 3.5]

    4) Copy from reference day over all 11 slots:
       The mock reference day is [0, 0, 1, 2, 0.0, 0.0, 1, 1, 1, 1, 1] (negatives become 0).
       Sum(ref) = 8, so with total_hours=8.0, values match the ref proportions.
       >>> fill_day(False, "copy_reference", [1,1,1]+[0]*8, 8.0, [-1]*11, retries=5, precision=2, reference_day=[1]*11)
       [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    5) Random strategy: check shape and sum (not exact values):
       >>> res = fill_day(False, "random", [], 8.0, [-1, -1, -1, -1], retries=10, precision=2)
       >>> len(res)
       4
       >>> round(sum(res), 2)
       8.0

    6) test post randomization
    >>> math.isclose(sum(fill_day(False, "equal", [], 8.0, [1.0, -1, -1, 2.0], retries=5, precision=2, post_randomization=0.2)), 8)
    True

       total_hours = 10.0, filled sum = 3.0 -> 7.0 over the 2 non-excluded blanks
       exclude_values marks indices 0 and 2 as excluded (they are already filled)
       >>> res = fill_day(False, "equal", [1, 0, 1, 0], 10.0, [2.0, -1, 1.0, -1], retries=5, precision=2)
       >>> len(res)
       4
       >>> round(sum(res), 2)
       10.0
       >>> res[0], res[2]
       (2.0, 1.0)
    """
    assert all(isinstance(v, (int, float)) for v in current_values), "All values must be int or float"
    
    if exclude_values == []: # if no values should be excluded set exclude values all to zero
        exclude_values = [0 for _ in range(len(current_values))]

    assert len(current_values) == len(exclude_values), f"the len(current_values) = {len(current_values)} does not match len(exclude_values)= {len(exclude_values)}"
    
    if override_mode:
        current_values = [-1] * len(current_values)
     # slots: count entries that are blank (-1) and not excluded (0)
    slots = sum(1 for cv, ex in zip(current_values, exclude_values) if cv == -1 and ex == 0)

    # hours_to_distribute: subtract already filled values from total_hours
    hours_to_distribute = total_hours - sum(v for v in current_values if v != -1)
    hours_to_distribute = round(max(0.0, hours_to_distribute), precision)
    
    if strategy in strategies.keys():
        pass
    else:
        raise KeyError(f"strategy {strategy} not defined")
    # Compute the fill_values according to the strategy
    if strategy == "equal":
        fill_values = strategies['equal'](hours_to_distribute, slots, precision)
    elif strategy == "random":
        fill_values = strategies['random'](hours_to_distribute, slots, precision, retries)
    elif strategy == "copy_reference":
        try:
            # reference day has to be cut away where exclude = 1
            reference_day = [v if v >= 0 else 0.0 for v in reference_day]
            applied_exclude_reference_day = [v for v, exc, current in zip(reference_day, exclude_values, current_values) if exc == 0 and current == -1]
            fill_values = strategies['copy_reference'](hours_to_distribute, slots, applied_exclude_reference_day, precision)
        except Exception as e:
            fill_values = strategies['equal'](hours_to_distribute, slots, precision)
    else:
        raise ValueError(f"Strategy: {strategy} unknown")

    res = apply_fill_values(current_values, exclude_values, fill_values, slots, post_randomization, precision)
    assert sum(res) == total_hours, f"calculated values do not add up, got {sum(res)}, should: {total_hours}"
    return res