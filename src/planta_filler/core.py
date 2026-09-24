"""The automation workflow: open PLANTA, walk through the requested weeks and
fill, reset or export each one.

The functions here only know :class:`~planta_filler.browser.PlantaPage`; they
never touch Selenium directly, which keeps them testable with a fake page.
"""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .browser import PlantaPage
from .calculations import BLANK, fill_day
from .config import (
    DEFAULT_CLOSE_DELAY,
    DEFAULT_DELAY,
    DEFAULT_PRECISION,
    DEFAULT_REFERENCE_FILE,
    DEFAULT_RETRIES,
    SELECTORS,
    WEEKDAY_NAMES,
)
from .exceptions import LoginRequiredError, ReferenceFileError
from .reference_handler import (
    WEEKDAY_HEADERS,
    ReferenceWeek,
    create_default_reference,
    load_reference_week,
    save_reference_week,
)
from .week_handler import filter_dates_by_weekdays, week_offset_from_today, weekday_of

log = logging.getLogger(__name__)


@dataclass
class RunOptions:
    """Everything the workflow needs; built by the CLI after validation."""

    url: str
    week_specs: list[str] = field(default_factory=lambda: ["0"])
    weekdays: list[int] | None = None
    strategy: str = "equal"
    post_randomization: float = 0.0
    reference_file: str | None = None
    exclude_indices: list[int] = field(default_factory=list)
    delay: float = DEFAULT_DELAY
    close_delay: float = DEFAULT_CLOSE_DELAY
    reset: bool = False
    export_reference: str | None = None
    interactive: bool = True
    precision: int = DEFAULT_PRECISION
    retries: int = DEFAULT_RETRIES


# --- building blocks ---------------------------------------------------------


def open_timesheet(page: PlantaPage, url: str, interactive: bool = True) -> None:
    """Open the URL and make sure the timesheet is visible, prompting for login if needed."""
    page.open(url)
    timeouts = SELECTORS["timeouts"]
    if page.wait_for_timesheet(timeouts["presence_seconds"]):
        return
    if not interactive:
        raise LoginRequiredError(
            "The timesheet did not appear. You are probably not logged in. "
            "Run once without --headless (and with --persistent) to log in interactively."
        )
    print("\n⏸️  Please log in in the browser window, then press ENTER here to continue...", flush=True)
    input()
    if not page.wait_for_timesheet(timeouts["after_login_seconds"]):
        raise LoginRequiredError("The timesheet still did not appear after login. Check the URL and your account.")


def iter_weeks(page: PlantaPage, week_specs: list[str]) -> Iterator[str]:
    """Navigate to every requested week in order and yield its spec once it is visible."""
    current_offset = 0
    for spec in week_specs:
        target = week_offset_from_today(spec)
        page.go_weeks(target - current_offset)
        current_offset = target
        yield spec


def exclude_mask(exclude_indices: list[int], num_slots: int) -> list[int]:
    return [1 if i in exclude_indices else 0 for i in range(num_slots)]


def load_reference(options: RunOptions) -> ReferenceWeek | None:
    """Load the reference file once; ``None`` means "fall back to equal weights"."""
    if options.strategy != "copy_reference":
        return None
    path = options.reference_file or DEFAULT_REFERENCE_FILE
    try:
        reference = load_reference_week(path)
    except ReferenceFileError as exc:
        log.warning("Reference file unusable (%s); every day falls back to equal weights", exc)
        return None
    log.info("Reference file: %s (%d rows, columns %s)", path, reference.num_rows, ", ".join(reference.labels))
    return reference


def _reference_for_day(reference: ReferenceWeek | None, date: str, num_slots: int) -> list[float]:
    if reference is None:
        return create_default_reference(num_slots)
    try:
        return reference.for_weekday(weekday_of(date), num_slots)
    except ReferenceFileError as exc:
        log.warning("%s: %s; falling back to equal weights", date, exc)
        return create_default_reference(num_slots)


def _apply_values(page: PlantaPage, fields, new_values: list[float], delay: float) -> int:
    changes = 0
    for hour_field, new_value in zip(fields, new_values):
        if abs(new_value - hour_field.value) <= 10**-DEFAULT_PRECISION / 2:
            continue
        if page.write_hours(hour_field.field_id, new_value):
            changes += 1
            time.sleep(delay)
    return changes


# --- per-week operations ---------------------------------------------------------


def fill_visible_week(page: PlantaPage, options: RunOptions, reference: ReferenceWeek | None = None) -> int:
    """Fill every selected working day of the week on screen. Returns the number of changed cells."""
    hours = page.read_hours()
    targets = page.read_target_hours()
    dates = filter_dates_by_weekdays(sorted(hours), options.weekdays)
    working_dates = [d for d in dates if targets.get(d, 0.0) > 0]
    log.info("Processing %d working day(s) with strategy %s", len(working_dates), options.strategy.upper())

    total_changes = 0
    for date in working_dates:
        fields = hours[date]
        current = [f.value for f in fields]
        target = targets[date]
        reference_day = (
            _reference_for_day(reference, date, len(fields)) if options.strategy == "copy_reference" else None
        )
        new_values = fill_day(
            current,
            target,
            options.strategy,
            exclude_values=exclude_mask(options.exclude_indices, len(fields)),
            override_mode=True,
            reference_day=reference_day,
            post_randomization=options.post_randomization,
            precision=options.precision,
            retries=options.retries,
        )
        log.info(
            "📅 %s (%s) target %.2fh, current %.2fh -> %s (sum %.2fh)",
            date,
            WEEKDAY_NAMES[weekday_of(date)],
            target,
            sum(current),
            new_values,
            sum(new_values),
        )
        changes = _apply_values(page, fields, new_values, options.delay)
        log.info("   ✅ %d change(s) applied", changes)
        total_changes += changes
    return total_changes


def reset_visible_week(page: PlantaPage, options: RunOptions) -> int:
    """Set every selected, non-excluded cell of the visible week to 0."""
    hours = page.read_hours()
    dates = filter_dates_by_weekdays(sorted(hours), options.weekdays)
    log.info("Resetting %d day(s)", len(dates))
    total_changes = 0
    for date in dates:
        fields = hours[date]
        mask = exclude_mask(options.exclude_indices, len(fields))
        kept = [f.value if excluded else 0.0 for f, excluded in zip(fields, mask)]
        changes = _apply_values(page, fields, kept, options.delay)
        log.info("   ✅ %s reset (%d change(s))", date, changes)
        total_changes += changes
    return total_changes


def export_visible_week(page: PlantaPage, path: str | Path, weekdays: list[int] | None = None) -> Path:
    """Save the values currently on screen as a whole-week reference CSV."""
    hours = page.read_hours()
    dates = filter_dates_by_weekdays(sorted(hours), weekdays)
    if not dates:
        raise ReferenceFileError("No days with hours inputs are visible; nothing to export")
    columns = {WEEKDAY_HEADERS[weekday_of(d)][0]: [f.value for f in hours[d]] for d in dates}
    row_counts = {len(v) for v in columns.values()}
    if len(row_counts) != 1:
        raise ReferenceFileError(f"Days have different numbers of task rows ({sorted(row_counts)}); cannot export")
    written = save_reference_week(path, columns)
    log.info("Exported %d day(s) x %d rows to %s", len(columns), row_counts.pop(), written)
    return written


def wait_before_close(seconds: float) -> None:
    if seconds <= 0:
        return
    log.info("⏳ Keeping the browser open for %.0f seconds so you can verify the result...", seconds)
    for remaining in range(int(seconds), 0, -1):
        if sys.stdout.isatty():
            print(f"   Closing in {remaining:3d} s", end="\r", flush=True)
        time.sleep(1)
    if sys.stdout.isatty():
        print(" " * 30, end="\r")


# --- entry point -----------------------------------------------------------------


def run(driver, options: RunOptions) -> int:
    """Execute the whole workflow on an already started driver. Returns the number of changed cells."""
    page = PlantaPage(driver)
    open_timesheet(page, options.url, options.interactive)

    if options.export_reference:
        if len(options.week_specs) != 1:
            raise ReferenceFileError("--export-reference works with exactly one week")
        for _ in iter_weeks(page, options.week_specs):
            export_visible_week(page, options.export_reference, options.weekdays)
        return 0

    reference = load_reference(options)
    total = 0
    for spec in iter_weeks(page, options.week_specs):
        log.info("\n=== Week %s ===", spec)
        if options.reset:
            total += reset_visible_week(page, options)
        else:
            total += fill_visible_week(page, options, reference)

    log.info("\n✅ Done: %d cell(s) changed", total)
    wait_before_close(options.close_delay)
    return total


__all__ = [
    "BLANK",
    "RunOptions",
    "export_visible_week",
    "fill_visible_week",
    "iter_weeks",
    "open_timesheet",
    "reset_visible_week",
    "run",
]
