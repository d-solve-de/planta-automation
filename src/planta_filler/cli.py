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
    VALID_STRATEGIES
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
        '--man',
        action='store_true',
        help='Show detailed manual page'
    )
    
    parser.add_argument(
        '--week',
        type=str,
        default='0',
        help='Week to process: YYYY-WNN, or offset (-1=last week, 0=current, 1=next)'
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
    
    try:
        year, week = parse_week_spec(args.week)
        week_display = format_week_display(year, week)
    except ValueError as e:
        print(f"\n❌ Invalid week specification: {e}")
        sys.exit(1)
    
    print("="*70)
    print("PLANTA TIMESHEET AUTOMATION")
    print("="*70)
    print(f"URL:         {args.url}")
    print(f"Week:        {week_display}")
    print(f"Action:      {'RESET' if args.reset else 'FILL'}")
    if not args.reset:
        print(f"Strategy:    {args.strategy.upper()}")
    if weekdays:
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        selected = ', '.join(weekday_names[d] for d in weekdays)
        print(f"Weekdays:    {selected}")
    print(f"Delay:       {args.delay}s")
    print(f"Close delay: {args.close_delay}s")
    print("="*70 + "\n")
    
    driver = start_driver(headless=args.headless, use_persistent_profile=args.persistent)
    
    try:
        if args.reset:
            reset_week(driver, args.url, weekdays, args.delay, args.close_delay)
        else:
            set_week(
                driver,
                url=args.url,
                strategy=args.strategy,
                weekdays=weekdays,
                skip_login_prompt=args.persistent,
                delay=args.delay,
                close_delay=args.close_delay
            )
    finally:
        end_driver(driver)


if __name__ == '__main__':
    main()
