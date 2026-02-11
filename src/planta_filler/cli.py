# =============================================================================
# cli.py - Command Line Interface
# =============================================================================
# This module provides the command-line interface for the PLANTA Filler.
# It handles argument parsing, input validation, and orchestrates the
# automation workflow.
#
# Entry points:
# - main(): Main CLI entry point (python3 -m planta_filler)
# - print_man_page(): Display full manual page
#
# Usage: python3 -m planta_filler [OPTIONS]
# =============================================================================

import argparse
import sys
from pathlib import Path

from .core import start_driver, end_driver, set_week, reset_week
from .config import (
    DEFAULT_URL, DEFAULT_STRATEGY, DEFAULT_WEEKDAYS, DEFAULT_DELAY,
    DEFAULT_CLOSE_DELAY, DEFAULT_USE_PERSISTENT_PROFILE, DEFAULT_HEADLESS,
    VALID_STRATEGIES, DEFAULT_POST_RANDOMIZATION
)
from .validation import validate_all_inputs, ValidationError
from .week_handler import parse_week_spec, format_week_display


def print_man_page():
    man_page_path = Path(__file__).parent / 'data' / 'man_page.txt'
    with open(man_page_path, 'r') as f:
        man_page_template = f.read()
    
    man_page = man_page_template.format(
        default_url=DEFAULT_URL,
        default_strategy=DEFAULT_STRATEGY,
        default_weekdays=','.join(map(str, DEFAULT_WEEKDAYS)),
        default_delay=DEFAULT_DELAY,
        default_close_delay=DEFAULT_CLOSE_DELAY,
        default_persistent=str(DEFAULT_USE_PERSISTENT_PROFILE),
        default_headless=str(DEFAULT_HEADLESS)
    )
    
    print(man_page)
    sys.exit(0)


def main():
    if '--man' in sys.argv:
        print_man_page()
    
    parser = argparse.ArgumentParser(
        description='PLANTA Timesheet Automation - Automatic timesheet filling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Use defaults (fill Mon-Fri with equal strategy)
  python3 -m planta_filler

  # Fill with random distribution
  python3 -m planta_filler --strategy random

  # Fill only Mon, Wed, Fri
  python3 -m planta_filler --weekdays 0,2,4
  
  # Reset to zero
  python3 -m planta_filler --reset
  
  # Use persistent profile (saves login)
  python3 -m planta_filler --persistent

  # Fill last week
  python3 -m planta_filler --week -1

  # Show full manual
  python3 -m planta_filler --man

Current defaults:
  URL:         {DEFAULT_URL}
  Strategy:    {DEFAULT_STRATEGY}
  Weekdays:    {','.join(map(str, DEFAULT_WEEKDAYS))} (Mon-Fri)
  Delay:       {DEFAULT_DELAY}s
  Close delay: {DEFAULT_CLOSE_DELAY}s

Weekday codes: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default=DEFAULT_URL,
        help=f'PLANTA URL (default: {DEFAULT_URL})'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        choices=VALID_STRATEGIES,
        default=DEFAULT_STRATEGY,
        help=f'Distribution strategy (default: {DEFAULT_STRATEGY})'
    )
    
    parser.add_argument(
        '--weekdays',
        type=str,
        default=','.join(map(str, DEFAULT_WEEKDAYS)),
        help=f"Comma-separated weekdays (default: {','.join(map(str, DEFAULT_WEEKDAYS))} = Mon-Fri)"
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset hours to 0 instead of filling'
    )
    
    parser.add_argument(
        '--persistent',
        action='store_true',
        default=DEFAULT_USE_PERSISTENT_PROFILE,
        help=f'Use persistent Firefox profile (default: {DEFAULT_USE_PERSISTENT_PROFILE})'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=DEFAULT_HEADLESS,
        help=f'Run in headless mode (default: {DEFAULT_HEADLESS})'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=DEFAULT_DELAY,
        help=f'Delay between field updates in seconds (default: {DEFAULT_DELAY})'
    )
    
    parser.add_argument(
        '--close-delay',
        type=float,
        default=DEFAULT_CLOSE_DELAY,
        help=f'Delay before closing browser in seconds (default: {DEFAULT_CLOSE_DELAY})'
    )

    parser.add_argument(
        '--post-randomization',
        type=float,
        default=DEFAULT_POST_RANDOMIZATION,
        help='Post-randomization factor (0.0-<1.0) applied to fill values for natural variation'
    )

    parser.add_argument(
        '--reference-file',
        type=str,
        default=None,
        help='Full path to reference CSV (single-day or whole-week). If omitted, uses the default packaged file.'
    )

    parser.add_argument(
        '--exclude',
        type=str,
        default=None,
        help='Comma-separated zero-based row indices to exclude from filling (applies to all processed days)'
    )
    
    parser.add_argument(
        '--man',
        action='store_true',
        help='Show detailed manual page'
    )
    
    parser.add_argument(
        '--week',
        type=str,
        default='0',
        help='Week(s) to process: YYYY-WNN or offset (e.g., -1,0 for last and current)'
    )
    
    args = parser.parse_args()
    
    if args.weekdays:
        weekdays = [int(d.strip()) for d in args.weekdays.split(',')]
    else:
        weekdays = DEFAULT_WEEKDAYS
    
    try:
        validate_all_inputs(
            strategy=args.strategy,
            weekdays=weekdays,
            delay=args.delay,
            close_delay=args.close_delay,
            url=args.url
        )
    except ValidationError as e:
        print(f"\n❌ Validation Error:\n{e}")
        sys.exit(1)
    
    # Prepare multiple week specs (comma separated allowed, preserve order)
    week_specs = [w.strip() for w in args.week.split(',') if w.strip()]
    
    try:
        # Validate that all week specs are parseable (in order)
        for w in week_specs:
            parse_week_spec(w)
    except ValueError as e:
        print(f"\n❌ Invalid week specification: {e}")
        sys.exit(1)
    
    # Display summary (use first week for header if multiple)
    y0, w0 = parse_week_spec(week_specs[0])
    week_display = format_week_display(y0, w0)
    
    print("="*70)
    print("PLANTA TIMESHEET AUTOMATION")
    print("="*70)
    print(f"URL:         {args.url}")
    print(f"Week:        {week_display}" + (" (and others)" if len(week_specs) > 1 else ""))
    print(f"Action:      {'RESET' if args.reset else 'FILL'}")
    if not args.reset:
        print(f"Strategy:    {args.strategy.upper()}")
        print(f"Post-randomization: {args.post_randomization}")
        if args.strategy == 'copy_reference':
            print(f"Reference file: {args.reference_file or 'DEFAULT'}")
    if weekdays:
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        selected = ', '.join(weekday_names[d] for d in weekdays)
        print(f"Weekdays:    {selected}")
    print(f"Delay:       {args.delay}s")
    print(f"Close delay: {args.close_delay}s")
    if args.exclude:
        print(f"Excludes:    {args.exclude}")
    if args.strategy == 'copy_reference':
        print(f"Reference:   {args.reference_file or 'DEFAULT'}")
    print("="*70 + "\n")
    
    driver = start_driver(headless=args.headless, use_persistent_profile=args.persistent)
    
    # Parse exclude indices
    exclude_indices = None
    if args.exclude:
        try:
            exclude_indices = [int(x.strip()) for x in args.exclude.split(',') if x.strip() != '']
        except ValueError:
            print("\n❌ Invalid exclude specification: must be comma-separated integers (0-based row indices)")
            sys.exit(1)
    
    try:
        if args.reset:
            reset_week(
                driver,
                args.url,
                weekdays,
                args.delay,
                args.close_delay,
                skip_login_prompt=args.persistent,
                week_specs=week_specs,
                exclude_indices=exclude_indices,
            )
        else:
            set_week(
                driver,
                url=args.url,
                strategy=args.strategy,
                weekdays=weekdays,
                skip_login_prompt=args.persistent,
                delay=args.delay,
                close_delay=args.close_delay,
                post_randomization=args.post_randomization,
                week_specs=week_specs,
                reference_day=None,
                reference_file=args.reference_file,
                exclude_indices=exclude_indices,
            )
    finally:
        end_driver(driver)


if __name__ == '__main__':
    main()
