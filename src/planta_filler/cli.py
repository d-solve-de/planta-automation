"""Command-line interface: parse arguments, validate them, run the workflow.

Usage::

    planta-filler --url https://planta.example.com/ [OPTIONS]
    python3 -m planta_filler --url ... [OPTIONS]
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .browser import end_driver, start_driver
from .config import (
    DEFAULT_CLOSE_DELAY,
    DEFAULT_DELAY,
    DEFAULT_HEADLESS,
    DEFAULT_POST_RANDOMIZATION,
    DEFAULT_STRATEGY,
    DEFAULT_URL,
    DEFAULT_USE_PERSISTENT_PROFILE,
    DEFAULT_WEEK,
    DEFAULT_WEEKDAYS,
    MAN_PAGE_FILE,
    PROFILE_DIR,
    VALID_STRATEGIES,
    WEEKDAY_NAMES,
)
from .core import RunOptions, run
from .exceptions import PlantaFillerError, ValidationError
from .validation import parse_int_list, validate_all_inputs
from .week_handler import format_week_display, parse_week_spec

log = logging.getLogger("planta_filler")

EPILOG = f"""
examples:
  planta-filler --url https://planta.example.com/
  planta-filler --url URL --strategy random --weekdays 0,2,4
  planta-filler --url URL --week=-1,0 --strategy copy_reference --reference-file ~/my_week.csv
  planta-filler --url URL --reset --week=-1
  planta-filler --url URL --export-reference ~/my_week.csv
  planta-filler --man

weekday codes: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun
persistent Firefox profile: {PROFILE_DIR}
"""


def render_man_page() -> str:
    template = MAN_PAGE_FILE.read_text(encoding="utf-8")
    return template.format(
        version=__version__,
        default_url=DEFAULT_URL or "(none, --url is required)",
        default_strategy=DEFAULT_STRATEGY,
        default_weekdays=",".join(map(str, DEFAULT_WEEKDAYS)),
        default_week=DEFAULT_WEEK,
        default_delay=DEFAULT_DELAY,
        default_close_delay=DEFAULT_CLOSE_DELAY,
        default_persistent=str(DEFAULT_USE_PERSISTENT_PROFILE),
        default_headless=str(DEFAULT_HEADLESS),
        default_post_randomization=DEFAULT_POST_RANDOMIZATION,
        profile_dir=PROFILE_DIR,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="planta-filler",
        description="Fill PLANTA timesheets automatically by distributing attendance hours across task rows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--man", action="store_true", help="show the full manual page and exit")

    target = parser.add_argument_group("what to fill")
    target.add_argument("--url", default=DEFAULT_URL, help="PLANTA URL (required unless a default is configured)")
    target.add_argument(
        "--week",
        default=DEFAULT_WEEK,
        help="week(s) to process: offset like 0, -1, 2 or ISO week like 2024-W05; "
        "several as one comma-separated argument, e.g. --week=-2,-1,0 (default: %(default)s)",
    )
    target.add_argument(
        "--weekdays",
        default=",".join(map(str, DEFAULT_WEEKDAYS)),
        help="comma-separated weekdays to process, 0=Mon .. 6=Sun (default: %(default)s)",
    )
    target.add_argument(
        "--exclude",
        default="",
        metavar="INDICES",
        help="comma-separated zero-based task row indices that are never changed",
    )

    how = parser.add_argument_group("how to fill")
    how.add_argument("--strategy", choices=VALID_STRATEGIES, default=DEFAULT_STRATEGY, help="(default: %(default)s)")
    how.add_argument(
        "--reference-file",
        metavar="PATH",
        help="CSV with weights for copy_reference (default: the packaged example file)",
    )
    how.add_argument(
        "--post-randomization",
        type=float,
        default=DEFAULT_POST_RANDOMIZATION,
        metavar="FACTOR",
        help="jitter every value by up to FACTOR of itself, 0.0 <= FACTOR < 1.0 (default: %(default)s)",
    )
    how.add_argument("--reset", action="store_true", help="set the selected cells to 0 instead of filling them")
    how.add_argument(
        "--export-reference",
        metavar="PATH",
        help="write the values currently in PLANTA for the selected week to PATH as a reference CSV and exit",
    )

    browser = parser.add_argument_group("browser")
    browser.add_argument(
        "--persistent",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_USE_PERSISTENT_PROFILE,
        help=f"keep the login in a Firefox profile under {PROFILE_DIR}",
    )
    browser.add_argument(
        "--headless", action="store_true", default=DEFAULT_HEADLESS, help="run Firefox without a window"
    )
    browser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY, help="seconds between field updates (default: %(default)s)"
    )
    browser.add_argument(
        "--close-delay",
        type=float,
        default=DEFAULT_CLOSE_DELAY,
        help="seconds to keep the browser open at the end (default: %(default)s)",
    )

    output = parser.add_argument_group("output")
    output.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    output.add_argument("-q", "--quiet", action="store_true", help="only show warnings and errors")
    return parser


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout, force=True)
    if not verbose:  # selenium is chatty at DEBUG
        logging.getLogger("selenium").setLevel(logging.WARNING)


def options_from_args(args: argparse.Namespace) -> RunOptions:
    """Validate the parsed arguments and turn them into :class:`RunOptions`."""
    try:
        weekdays = parse_int_list(args.weekdays, "--weekdays")
        exclude_indices = parse_int_list(args.exclude, "--exclude")
    except ValidationError as exc:
        raise ValidationError(f"Validation failed:\n  - {exc}") from exc

    validated = validate_all_inputs(
        url=args.url,
        strategy=args.strategy,
        weekdays=weekdays,
        delay=args.delay,
        close_delay=args.close_delay,
        week=args.week,
        post_randomization=args.post_randomization,
        exclude_indices=exclude_indices,
        reference_file=args.reference_file,
    )
    interactive = not args.headless and sys.stdin.isatty()
    return RunOptions(
        url=validated["url"],
        week_specs=validated["week_specs"],
        weekdays=validated["weekdays"],
        strategy=validated["strategy"],
        post_randomization=validated["post_randomization"],
        reference_file=validated["reference_file"],
        exclude_indices=validated["exclude_indices"],
        delay=validated["delay"],
        close_delay=validated["close_delay"],
        reset=args.reset,
        export_reference=args.export_reference,
        interactive=interactive,
    )


def print_summary(options: RunOptions, headless: bool, persistent: bool) -> None:
    weeks = ", ".join(format_week_display(*parse_week_spec(spec)) for spec in options.week_specs)
    action = "EXPORT" if options.export_reference else "RESET" if options.reset else "FILL"
    lines = [
        "=" * 70,
        "PLANTA TIMESHEET AUTOMATION",
        "=" * 70,
        f"URL:          {options.url}",
        f"Week(s):      {weeks}",
        f"Weekdays:     {', '.join(WEEKDAY_NAMES[d] for d in options.weekdays or [])}",
        f"Action:       {action}",
    ]
    if action == "FILL":
        lines.append(f"Strategy:     {options.strategy}")
        if options.strategy == "copy_reference":
            lines.append(f"Reference:    {options.reference_file or 'packaged default'}")
        lines.append(f"Post-random.: {options.post_randomization}")
    if action == "EXPORT":
        lines.append(f"Export to:    {options.export_reference}")
    if options.exclude_indices:
        lines.append(f"Excluded:     rows {options.exclude_indices}")
    lines += [
        f"Browser:      {'headless' if headless else 'visible'}, {'persistent' if persistent else 'temporary'} profile",
        f"Delays:       {options.delay}s between fields, {options.close_delay}s before closing",
        "=" * 70,
    ]
    log.info("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.man:
        print(render_man_page())
        return 0

    configure_logging(verbose=args.verbose, quiet=args.quiet)
    try:
        options = options_from_args(args)
    except ValidationError as exc:
        log.error("\n❌ %s", exc)
        return 2

    print_summary(options, headless=args.headless, persistent=args.persistent)

    try:
        driver = start_driver(headless=args.headless, use_persistent_profile=args.persistent)
    except PlantaFillerError as exc:
        log.error("\n❌ %s", exc)
        return 1
    try:
        run(driver, options)
    except PlantaFillerError as exc:
        log.error("\n❌ %s", exc)
        return 1
    except KeyboardInterrupt:
        log.warning("\nInterrupted, closing the browser.")
        return 130
    finally:
        end_driver(driver)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
