"""Validation of user input before any browser is started.

Each ``validate_*`` function returns the (possibly normalised) value or raises
:class:`ValidationError`. :func:`validate_all_inputs` runs them all and reports
every problem at once.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .config import (
    MAX_DELAY,
    MAX_PRECISION,
    MIN_DELAY,
    VALID_STRATEGIES,
    VALID_WEEKDAYS,
)
from .exceptions import ValidationError
from .week_handler import parse_week_specs

__all__ = [
    "ValidationError",
    "parse_int_list",
    "validate_all_inputs",
    "validate_delay",
    "validate_exclude_indices",
    "validate_post_randomization",
    "validate_precision",
    "validate_reference_file",
    "validate_strategy",
    "validate_url",
    "validate_week_specs",
    "validate_weekdays",
]


def parse_int_list(text: str | None, name: str) -> list[int]:
    """Parse ``"0, 2,4"`` into ``[0, 2, 4]``; empty input gives ``[]``."""
    if text is None or not text.strip():
        return []
    values = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError as exc:
            raise ValidationError(f"{name} must be comma-separated integers, got {part!r}") from exc
    return values


def validate_strategy(strategy: str) -> str:
    if strategy not in VALID_STRATEGIES:
        raise ValidationError(f"Invalid strategy {strategy!r}. Must be one of: {', '.join(VALID_STRATEGIES)}")
    return strategy


def validate_weekdays(weekdays: Sequence[int]) -> list[int]:
    if not weekdays:
        raise ValidationError("At least one weekday is required")
    for day in weekdays:
        if day not in VALID_WEEKDAYS:
            raise ValidationError(f"Invalid weekday {day}. Must be 0-6 (0=Mon, 6=Sun)")
    return list(dict.fromkeys(weekdays))  # de-duplicate, keep order


def validate_delay(delay: float, name: str = "delay") -> float:
    if not MIN_DELAY <= delay <= MAX_DELAY:
        raise ValidationError(f"{name} must be between {MIN_DELAY} and {MAX_DELAY} seconds, got {delay}")
    return delay


def validate_url(url: str) -> str:
    if not url or not url.startswith(("http://", "https://")):
        raise ValidationError(f"URL must start with http:// or https://, got: {url!r}")
    return url


def validate_reference_file(filepath: str) -> str:
    """Check the file exists and return its absolute, ``~``-expanded path."""
    path = Path(filepath).expanduser()
    if path.suffix.lower() != ".csv":
        raise ValidationError(f"Reference file must be a .csv file, got: {filepath}")
    if not path.is_file():
        raise ValidationError(f"Reference file not found: {path}")
    return str(path.resolve())


def validate_exclude_indices(indices: Sequence[int]) -> list[int]:
    for index in indices:
        if index < 0:
            raise ValidationError(f"Exclude indices must be zero-based non-negative integers, got {index}")
    return sorted(set(indices))


def validate_post_randomization(factor: float) -> float:
    if not 0.0 <= factor < 1.0:
        raise ValidationError(f"post-randomization must be in the range [0.0, 1.0), got {factor}")
    return factor


def validate_precision(precision: int) -> int:
    if not 0 <= precision <= MAX_PRECISION:
        raise ValidationError(f"Precision must be between 0 and {MAX_PRECISION}, got: {precision}")
    return precision


def validate_week_specs(spec_string: str) -> list[str]:
    try:
        return parse_week_specs(spec_string)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def validate_all_inputs(
    *,
    url: str,
    strategy: str,
    weekdays: Sequence[int],
    delay: float,
    close_delay: float,
    week: str = "0",
    post_randomization: float = 0.0,
    exclude_indices: Sequence[int] = (),
    reference_file: str | None = None,
) -> dict:
    """Validate everything and return the normalised values.

    Raises a single :class:`ValidationError` listing all problems found.
    """
    errors: list[str] = []
    result: dict = {}

    checks = [
        ("url", lambda: validate_url(url)),
        ("strategy", lambda: validate_strategy(strategy)),
        ("weekdays", lambda: validate_weekdays(weekdays)),
        ("delay", lambda: validate_delay(delay, "delay")),
        ("close_delay", lambda: validate_delay(close_delay, "close-delay")),
        ("week_specs", lambda: validate_week_specs(week)),
        ("post_randomization", lambda: validate_post_randomization(post_randomization)),
        ("exclude_indices", lambda: validate_exclude_indices(exclude_indices)),
        ("reference_file", lambda: validate_reference_file(reference_file) if reference_file else None),
    ]
    for key, check in checks:
        try:
            result[key] = check()
        except ValidationError as exc:
            errors.append(str(exc))

    if errors:
        raise ValidationError("Validation failed:\n  - " + "\n  - ".join(errors))
    return result
