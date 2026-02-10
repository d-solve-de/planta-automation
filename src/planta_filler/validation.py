# =============================================================================
# validation.py - Input Validation for PLANTA Filler
# =============================================================================
# This module provides comprehensive input validation for all CLI arguments
# and configuration values. It validates strategies, weekdays, delays, URLs,
# reference files, and exclude values before the automation runs.
#
# Main functions:
# - validate_all_inputs(): Validates all inputs at once, collecting errors
# - validate_strategy(): Checks if strategy is in VALID_STRATEGIES
# - validate_weekdays(): Ensures weekdays are 0-6
# - validate_delay(): Checks delay is within MIN_DELAY and MAX_DELAY
# - validate_url(): Ensures URL starts with http:// or https://
# =============================================================================

from pathlib import Path
from .config import VALID_STRATEGIES, VALID_WEEKDAYS, MAX_DELAY, MIN_DELAY


class ValidationError(Exception):
    pass


def validate_strategy(strategy: str) -> str:
    if strategy not in VALID_STRATEGIES:
        raise ValidationError(f"Invalid strategy '{strategy}'. Must be one of: {VALID_STRATEGIES}")
    return strategy


def validate_weekdays(weekdays: list) -> list:
    for day in weekdays:
        if day not in VALID_WEEKDAYS:
            raise ValidationError(f"Invalid weekday {day}. Must be 0-6 (0=Mon, 6=Sun)")
    return weekdays


def validate_delay(delay: float, name: str = "delay") -> float:
    if not (MIN_DELAY <= delay <= MAX_DELAY):
        raise ValidationError(f"{name} must be between {MIN_DELAY} and {MAX_DELAY}, got {delay}")
    return delay


def validate_reference_file(filepath: str) -> str:
    if not filepath.endswith('.csv'):
        raise ValidationError(f"Reference file must be .csv, got: {filepath}")
    path = Path(filepath)
    if not path.exists():
        raise ValidationError(f"Reference file not found: {filepath}")
    return filepath


def validate_exclude_values(exclude_values: list, num_slots: int) -> list:
    if not exclude_values:
        return exclude_values
    if len(exclude_values) != num_slots:
        raise ValidationError(f"exclude_values length ({len(exclude_values)}) must match number of slots ({num_slots})")
    for val in exclude_values:
        if val not in [0, 1]:
            raise ValidationError(f"exclude_values must contain only 0 or 1, got: {val}")
    return exclude_values


def validate_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        raise ValidationError(f"URL must start with http:// or https://, got: {url}")
    return url


def validate_precision(precision: int) -> int:
    if not (0 <= precision <= 10):
        raise ValidationError(f"Precision must be between 0 and 10, got: {precision}")
    return precision


def validate_all_inputs(
    strategy: str,
    weekdays: list,
    delay: float,
    close_delay: float,
    url: str,
    reference_file: str = None
) -> dict:
    errors = []
    
    try:
        validate_strategy(strategy)
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        validate_weekdays(weekdays)
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        validate_delay(delay, "delay")
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        validate_delay(close_delay, "close_delay")
    except ValidationError as e:
        errors.append(str(e))
    
    try:
        validate_url(url)
    except ValidationError as e:
        errors.append(str(e))
    
    if reference_file:
        try:
            validate_reference_file(reference_file)
        except ValidationError as e:
            errors.append(str(e))
    
    if errors:
        raise ValidationError("Validation failed:\n  - " + "\n  - ".join(errors))
    
    return {
        'strategy': strategy,
        'weekdays': weekdays,
        'delay': delay,
        'close_delay': close_delay,
        'url': url,
        'reference_file': reference_file
    }
