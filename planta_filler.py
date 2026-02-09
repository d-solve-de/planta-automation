from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from calculations import fill_day
import csv

# Load configuration from config.py
try:
    from config import (
        DEFAULT_STRATEGY,
        DEFAULT_WEEKDAYS,
        DEFAULT_DELAY,
        DEFAULT_CLOSE_DELAY,
        DEFAULT_USE_PERSISTENT_PROFILE,
        DEFAULT_HEADLESS,
        DEFAULT_REFERENCE_FILE,
        DEFAULT_EXCLUDE_VALUES
    )
except ImportError:
    print("⚠️  Warning: config.py not found. Using fallback defaults.")
    DEFAULT_STRATEGY = 'copy_reference'
    DEFAULT_WEEKDAYS = [0, 1, 2, 3, 4]
    DEFAULT_DELAY = 0.2
    DEFAULT_CLOSE_DELAY = 20.0
    DEFAULT_USE_PERSISTENT_PROFILE = True
    DEFAULT_HEADLESS = False
    DEFAULT_REFERENCE_FILE = 'default_reference.csv'
    DEFAULT_EXCLUDE_VALUES = []




def read_csv_by_columns(filename):
    """Read CSV file and return data as list of columns.

    Args:
        filename: Path to CSV file

    Returns:
        List of columns, where each column is a list of values
    """
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Transpose rows to columns
    columns = list(zip(*rows))

    # Convert tuples to lists
    columns = [list(col) for col in columns]
    return columns



def load_reference_file(filename: str) -> Dict[int, List[float]]:
    """Load reference file and return as dict mapping weekday to hours list.

    The CSV format is:
    - First row: headers (ignored)
    - First column: row numbers (ignored)
    - Columns 1-5: Monday to Friday values

    Args:
        filename: Path to reference CSV file

    Returns:
        Dictionary mapping weekday index (0=Mon, 4=Fri) to list of hours
        Empty cells are converted to 0.0
    """
    columns = read_csv_by_columns(filename)

    # Skip first column (row numbers) and process columns 1-5 (Mon-Fri)
    reference_week = {}

    for weekday_idx in range(5):  # 0=Mon to 4=Fri
        col_idx = weekday_idx + 1  # +1 because first column is row numbers

        if col_idx < len(columns):
            # Skip first row (header) and convert values
            values = []
            for cell in columns[col_idx][1:]:  # Skip header row
                if cell.strip() == '':
                    values.append(0.0)
                else:
                    try:
                        values.append(float(cell.strip()))
                    except ValueError:
                        values.append(0.0)

            reference_week[weekday_idx] = values

    return reference_week



def indices_to_exclude_array(indices: List[int], length: int) -> List[int]:
    """Convert list of indices to exclude into binary array for fill_day().

    Args:
        indices: List of indices to exclude (e.g., [0, 2, 5])
        length: Total number of tasks

    Returns:
        Binary array where 1 means exclude, 0 means include
        Example: indices=[0,2,5], length=8 -> [1,0,1,0,0,1,0,0]
    """
    exclude_array = [0] * length
    for idx in indices:
        if 0 <= idx < length:
            exclude_array[idx] = 1
    return exclude_array



def start_driver(headless: bool = False, use_persistent_profile: bool = True):
    """Start Firefox WebDriver with persistent profile."""
    options = Options()

    if headless:
        options.add_argument('--headless')

    if use_persistent_profile:
        profile_dir = Path.home() / '.selenium_profiles' / 'planta_firefox'
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument('-profile')
        options.add_argument(str(profile_dir))

    driver = webdriver.Firefox(options=options)
    return driver



def get_target_hours_per_day(driver) -> Dict[str, float]:
    """Extract target hours from <div class='load att-YYYYMMDD'>."""
    target_hours = {}
    load_divs = driver.find_elements(By.CSS_SELECTOR, 'div.load[class*="att-"]')

    import re
    for div in load_divs:
        class_attr = div.get_attribute('class')
        match = re.search(r'att-(\d{8})', class_attr)

        if match:
            date_str = match.group(1)
            date_formatted = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            text = div.text.strip().replace(',', '.')
            hours_match = re.findall(r'(\d+\.?\d*)', text)
            if hours_match:
                target_hours[date_formatted] = float(hours_match[0])

    return target_hours



def get_hours_per_day(driver) -> Dict[str, List[Tuple[str, float]]]:
    """Extract existing hours grouped by date."""
    all_fields = driver.find_elements(By.CSS_SELECTOR, 'input.load-input')
    hours_by_date = {}

    for field in all_fields:
        field_id = field.get_attribute('id')
        if not field_id or len(field_id) <= 10:
            continue

        date = field_id[-10:]
        value = driver.execute_script("return arguments[0].value;", field)
        hours = float(value) if value and str(value).strip() else 0.0

        if date not in hours_by_date:
            hours_by_date[date] = []
        hours_by_date[date].append((field_id, hours))

    return hours_by_date



def filter_dates_by_weekdays(dates: List[str], weekdays: List[int]) -> List[str]:
    """Filter dates by weekday."""
    if not weekdays:
        return dates

    return [d for d in dates if datetime.strptime(d, '%Y-%m-%d').weekday() in weekdays]



def set_week(
    driver, 
    url: str,
    strategy: str = 'random',
    weekdays: Optional[List[int]] = None,
    skip_login_prompt: bool = False,
    delay: float = DEFAULT_DELAY,
    close_delay: float = DEFAULT_CLOSE_DELAY,
    reference_file: str = DEFAULT_REFERENCE_FILE,
    exclude_indices: List[int] = None
):
    """Fill hours for the week (optimized version with reference file support).

    Args:
        driver: Selenium WebDriver instance
        url: PLANTA URL
        strategy: Distribution strategy ('random', 'equal', 'copy_reference')
        weekdays: List of weekdays to process (0=Mon, 6=Sun)
        skip_login_prompt: Skip manual login prompt
        delay: Delay between field updates
        close_delay: Delay before closing browser
        reference_file: Path to CSV file containing reference values for the week
        exclude_indices: List of task indices to exclude (e.g., [0, 2, 5])
    """
    if exclude_indices is None:
        exclude_indices = []

    try:
        # Load reference file if it exists
        reference_week = {}
        if reference_file and Path(reference_file).exists():
            try:
                reference_week = load_reference_file(reference_file)
                print(f"📁 Loaded reference file: {reference_file}")
                print(f"   Available reference days: {list(reference_week.keys())}")
            except Exception as e:
                print(f"⚠️  Warning: Could not load reference file: {e}")
                print("   Continuing without reference data...")

        if exclude_indices:
            print(f"🚫 Exclude indices: {exclude_indices}")

        driver.get(url)

        if not skip_login_prompt:
            input("⏸️  Press ENTER after you've logged in...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.load-input'))
        )

        print("\n📊 Extracting data...")
        hours_data = get_hours_per_day(driver)
        target_hours_map = get_target_hours_per_day(driver)

        # Show summary
        print(f"\n🎯 Target hours:")
        for date, hours in sorted(target_hours_map.items()):
            if hours > 0:
                weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
                print(f"   {date} ({weekday}): {hours:.2f}h")

        sorted_dates = sorted(hours_data.keys())

        if weekdays is not None:
            sorted_dates = filter_dates_by_weekdays(sorted_dates, weekdays)

        working_dates = [d for d in sorted_dates if target_hours_map.get(d, 0.0) > 0]

        print(f"\n⚙️  Processing {len(working_dates)} working days with strategy: {strategy.upper()}\n")

        # Process each day
        for idx, date in enumerate(working_dates, 1):
            day_target = target_hours_map.get(date, 8.0)
            weekday_idx = datetime.strptime(date, '%Y-%m-%d').weekday()
            weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%a')

            entries = hours_data[date]
            current_values = [hours for _, hours in entries]
            current_sum = sum(current_values)
            num_tasks = len(current_values)

            # Convert exclude indices to binary array
            exclude_array = indices_to_exclude_array(exclude_indices, num_tasks)

            # Get reference for this weekday if available
            reference_day = reference_week.get(weekday_idx, None)

            if reference_day:
                print(f"📅 {date} ({weekday}) - Target: {day_target:.2f}h, Current: {current_sum:.2f}h [Using reference]")
            else:
                print(f"📅 {date} ({weekday}) - Target: {day_target:.2f}h, Current: {current_sum:.2f}h")

            if exclude_indices:
                excluded_tasks = [i for i, e in enumerate(exclude_array) if e == 1]
                print(f"   Excluding tasks at indices: {excluded_tasks}")

            # Calculate new values
            new_values = fill_day(
                override_mode=True,
                strategy=strategy,
                exclude_values=exclude_array,  # Binary array: [1,0,0,1,1,0]
                total_hours=day_target,
                current_values=current_values,
                retries=3,
                precision=2,
                reference_day=reference_day
            )
            print(f"   Calculated distribution: {new_values} (sum: {sum(new_values):.2f}h)")

            # Apply changes
            changes = 0
            for i, (field_id, old_hours) in enumerate(entries):
                new_hour = new_values[i]

                if abs(new_hour - old_hours) > 0.01:
                    field = driver.find_element(By.ID, field_id)

                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys(str(new_hour))
                        driver.execute_script("arguments[0].blur();", field)
                        changes += 1
                        time.sleep(delay)

            print(f"   ✅ {changes} changes applied\n")

        print("✅ ALL DAYS PROCESSED!")
        print(f"\n⏳ Waiting {close_delay} seconds before closing browser...")
        print("   (You can verify the values in the browser during this time)")

        # Countdown display
        for remaining in range(int(close_delay), 0, -1):
            print(f"   Closing in {remaining} seconds...", end='\r')
            time.sleep(1)

        print("\n\n🔒 Closing browser now...")

    except Exception as e:
        raise Exception(f"Setting week failed: {str(e)}")



def reset_week(
    driver, 
    url: str, 
    weekdays: Optional[List[int]] = None, 
    delay: float = DEFAULT_DELAY,
    close_delay: float = DEFAULT_CLOSE_DELAY
):
    """Reset all hours to 0."""
    try:
        driver.get(url)
        input("⏸️  Press ENTER after you've logged in...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.load-input'))
        )

        hours_data = get_hours_per_day(driver)
        sorted_dates = sorted(hours_data.keys())

        if weekdays is not None:
            sorted_dates = filter_dates_by_weekdays(sorted_dates, weekdays)

        print(f"\n🔄 Resetting {len(sorted_dates)} days...\n")

        for date in sorted_dates:
            entries = hours_data[date]
            for field_id, _ in entries:
                field = driver.find_element(By.ID, field_id)
                if field.is_displayed() and field.is_enabled():
                    field.clear()
                    field.send_keys('0')
                    driver.execute_script("arguments[0].blur();", field)
                    time.sleep(delay)
            print(f"   ✅ {date} reset")

        print("\n✅ All days reset!")
        print(f"\n⏳ Waiting {close_delay} seconds before closing browser...")
        print("   (You can verify the reset in the browser during this time)")

        # Countdown display
        for remaining in range(int(close_delay), 0, -1):
            print(f"   Closing in {remaining} seconds...", end='\r')
            time.sleep(1)

        print("\n\n🔒 Closing browser now...")

    except Exception as e:
        raise Exception(f"Resetting week failed: {str(e)}")



def end_driver(driver):
    """Close the browser."""
    driver.quit()



def print_man_page():
    """Print detailed man page."""
    man_page = f"""
NAME
    planta-filler - Automatic timesheet filling for PLANTA



SYNOPSIS
    python3 planta_filler.py --url URL [OPTIONS]



DESCRIPTION
    Automates filling timesheets in PLANTA by distributing working hours
    across tasks according to configurable strategies. Reads target hours
    from the 'Anwesend' column and fills input fields automatically.

    Supports reference files to maintain consistent hour distributions
    across weeks. Allows exclusion of specific task indices from automatic
    filling.

    Configuration is loaded from config.py file.



OPTIONS
    --url URL (REQUIRED)
        PLANTA URL to access
        This parameter is mandatory and must be provided.
        Example: --url https://pze.rz.bankenit.de/



    --strategy STRATEGY
        Hour distribution strategy. One of:
          random         - Random distribution with variance (realistic)
          equal          - Equal distribution across all tasks
          copy_reference - Copy distribution pattern from reference file
        Default: {DEFAULT_STRATEGY} (from config.py)



    --weekdays WEEKDAYS
        Comma-separated list of weekdays to process
        Format: 0,1,2,3,4
        Weekday codes:
          0 = Monday
          1 = Tuesday
          2 = Wednesday
          3 = Thursday
          4 = Friday
          5 = Saturday
          6 = Sunday
        Default: {','.join(map(str, DEFAULT_WEEKDAYS))} (from config.py)



    --exclude INDICES
        Comma-separated list of task indices to exclude from filling
        Format: 0,2,5 (0-based indexing)

        Tasks at these indices will be skipped during hour distribution.
        The script converts this to a binary array [1,0,1,0,0,1,0,0] where
        1 indicates exclusion at that index.

        Use this to preserve manually entered hours for specific tasks
        or to exclude tasks that should always remain at 0.

        Example: --exclude 0,3,7
                 Creates exclude array with 1s at positions 0, 3, and 7

        Default: [] (no exclusions, from config.py)



    --reference-file FILE
        Path to CSV file containing reference hour distributions
        CSV format:
          - First row: headers (Mo, Di, Mi, Do, Fr)
          - First column: row numbers (1-11)
          - Columns 1-5: Monday to Friday hour values
          - Empty cells are treated as 0

        Default: {DEFAULT_REFERENCE_FILE} (from config.py)



    --reset
        Reset all hours to 0 instead of filling
        Default: false (fill mode)



    --persistent
        Use persistent Firefox profile to save login between sessions
        Profile location: ~/.selenium_profiles/planta_firefox/
        Default: {DEFAULT_USE_PERSISTENT_PROFILE} (from config.py)



    --headless
        Run browser in headless mode (no visible window)
        Default: {DEFAULT_HEADLESS} (from config.py)



    --delay SECONDS
        Delay between field updates in seconds
        Default: {DEFAULT_DELAY} (from config.py)



    --close-delay SECONDS
        Delay before closing browser (time to verify changes)
        Default: {DEFAULT_CLOSE_DELAY} (from config.py)



    --help, -h
        Show help message and exit



    --man
        Show this manual page



CONFIGURATION FILE
    The script loads default values from config.py:

    DEFAULT_STRATEGY = '{DEFAULT_STRATEGY}'
    DEFAULT_WEEKDAYS = {DEFAULT_WEEKDAYS}
    DEFAULT_DELAY = {DEFAULT_DELAY}
    DEFAULT_CLOSE_DELAY = {DEFAULT_CLOSE_DELAY}
    DEFAULT_USE_PERSISTENT_PROFILE = {DEFAULT_USE_PERSISTENT_PROFILE}
    DEFAULT_HEADLESS = {DEFAULT_HEADLESS}
    DEFAULT_REFERENCE_FILE = '{DEFAULT_REFERENCE_FILE}'
    DEFAULT_EXCLUDE_VALUES = {DEFAULT_EXCLUDE_VALUES}

    Edit config.py to change default behavior.
    If config.py is missing, fallback defaults are used.



EXCLUDE VALUES - BINARY ARRAY FORMAT
    The fill_day() function expects a binary array where:
      - 1 = exclude this index
      - 0 = include this index

    The --exclude parameter takes indices and converts them:

    Input:   --exclude 0,2,5
    Array:   [1, 0, 1, 0, 0, 1, 0, 0, ...]
    Meaning: Exclude tasks at positions 0, 2, and 5

    Example with 8 tasks:
      --exclude 0,3,7  →  [1,0,0,1,0,0,0,1]

    This array is passed directly to fill_day() as exclude_values.



EXAMPLES
    Basic usage (URL is required):
        python3 planta_filler.py --url https://pze.rz.bankenit.de/



    Exclude specific task indices:
        python3 planta_filler.py --url <URL> --exclude 0,2,5
        # Creates binary array: [1,0,1,0,0,1,0,...]



    Exclude and use reference:
        python3 planta_filler.py --url <URL> --exclude 0,3 --reference-file my_hours.csv



    Fill with equal distribution:
        python3 planta_filler.py --url <URL> --strategy equal



    Fill only Mon, Wed, Fri with exclusions:
        python3 planta_filler.py --url <URL> --weekdays 0,2,4 --exclude 1,4



    Reset current week to zero:
        python3 planta_filler.py --url <URL> --reset



    Complex example:
        python3 planta_filler.py \\
            --url https://pze.rz.bankenit.de/ \\
            --strategy copy_reference \\
            --reference-file week_template.csv \\
            --exclude 0,3,7 \\
            --weekdays 0,1,2,3,4 \\
            --delay 0.3 \\
            --close-delay 30



HOW IT WORKS
    1. Loads configuration from config.py (or uses fallbacks)
    2. Validates that --url parameter is provided (mandatory)
    3. Opens Firefox and navigates to PLANTA URL
    4. Loads reference file (if specified and exists)
    5. Parses exclude indices from --exclude parameter
    6. Waits for manual login (unless persistent profile is used)
    7. Reads target hours from <div class="load att-YYYYMMDD">
    8. Reads current values from input fields
    9. For each day:
       - Gets reference values for that weekday from CSV
       - Converts exclude indices to binary array [1,0,1,0,...]
       - Calculates new distribution using strategy + reference + exclusions
       - Passes binary exclude array to fill_day()
       - Updates only non-excluded fields in browser
    10. Waits for specified close-delay time
    11. Closes browser automatically



FILES
    config.py
        Configuration file with default values



    ~/.selenium_profiles/planta_firefox/
        Firefox profile directory (when using --persistent)



    default_reference.csv
        Default reference file (if exists in current directory)



    calculations.py
        Module containing fill_day() distribution algorithm



REQUIREMENTS
    - Python 3.7+
    - selenium
    - Firefox browser
    - geckodriver (Firefox WebDriver)
    - config.py (optional, fallback defaults used if missing)



EXIT STATUS
    0   Success
    1   Error occurred (missing URL, invalid parameters, etc.)



TROUBLESHOOTING
    "error: the following arguments are required: --url"
        → You must provide the --url parameter



    "Warning: config.py not found"
        → Create config.py or fallback defaults will be used
        → Not critical, script will continue



    Excluded indices not working:
        → Verify fill_day() expects binary array format
        → Check conversion: indices → [1,0,1,0,...] array
        → Ensure indices are within valid range (0 to num_tasks-1)



AUTHOR
    Written for automated PLANTA timesheet filling.



COPYRIGHT
    MIT License



SEE ALSO
    selenium documentation: https://selenium-python.readthedocs.io/
    geckodriver: https://github.com/mozilla/geckodriver
    config.py: Configuration file for default values



"""

    print(man_page)
    sys.exit(0)



def main():
    """Main entry point with CLI arguments."""

    # Check for --man flag before argparse (to show full manual)
    if '--man' in sys.argv:
        print_man_page()

    parser = argparse.ArgumentParser(
        description='PLANTA Timesheet Automation - Automatic timesheet filling (config from config.py)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Basic usage (URL is required)
  python3 planta_filler.py --url https://pze.rz.bankenit.de/



  # Exclude specific task indices (converted to binary array)
  python3 planta_filler.py --url <URL> --exclude 0,2,5
  # This creates: [1,0,1,0,0,1,0,...] array for fill_day()



  # Combine exclusions with reference file
  python3 planta_filler.py --url <URL> --exclude 0,3 --reference-file my_hours.csv



  # Fill only Mon, Wed, Fri with exclusions
  python3 planta_filler.py --url <URL> --weekdays 0,2,4 --exclude 1,4

  # Reset to zero
  python3 planta_filler.py --url <URL> --reset

  # Show full manual
  python3 planta_filler.py --man



Current defaults (from config.py):
  Strategy:       {DEFAULT_STRATEGY}
  Weekdays:       {','.join(map(str, DEFAULT_WEEKDAYS))} (Mon-Fri)
  Reference file: {DEFAULT_REFERENCE_FILE}
  Exclude:        {DEFAULT_EXCLUDE_VALUES}
  Delay:          {DEFAULT_DELAY}s
  Close delay:    {DEFAULT_CLOSE_DELAY}s
  Persistent:     {DEFAULT_USE_PERSISTENT_PROFILE}
  Headless:       {DEFAULT_HEADLESS}



Note: --url parameter is REQUIRED
Weekday codes: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
Exclude format: Indices are converted to binary array [1,0,1,0,...] for fill_day()
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='PLANTA URL to access (REQUIRED)'
    )

    parser.add_argument(
        '--strategy',
        type=str,
        choices=['random', 'equal', 'copy_reference'],
        default=DEFAULT_STRATEGY,
        help=f'Distribution strategy (default: {DEFAULT_STRATEGY})'
    )

    parser.add_argument(
        '--weekdays',
        type=str,
        default=','.join(map(str, DEFAULT_WEEKDAYS)),
        help=f"Comma-separated weekdays (default: {','.join(map(str, DEFAULT_WEEKDAYS))})"
    )

    parser.add_argument(
        '--exclude',
        type=str,
        default='',
        help='Comma-separated task indices to exclude (0-based, converted to binary array)'
    )

    parser.add_argument(
        '--reference-file',
        type=str,
        default=DEFAULT_REFERENCE_FILE,
        help=f'CSV file with reference hour distributions (default: {DEFAULT_REFERENCE_FILE})'
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

    args = parser.parse_args()

    # Parse weekdays
    if args.weekdays:
        weekdays = [int(d.strip()) for d in args.weekdays.split(',')]
    else:
        weekdays = None

    # Parse exclude indices
    exclude_indices = []
    if args.exclude:
        exclude_indices = [int(idx.strip()) for idx in args.exclude.split(',')]

    print("="*70)
    print("PLANTA TIMESHEET AUTOMATION")
    print("="*70)
    print(f"Config:      Loaded from config.py")
    print(f"URL:         {args.url}")
    print(f"Action:      {'RESET' if args.reset else 'FILL'}")
    if not args.reset:
        print(f"Strategy:    {args.strategy.upper()}")
        print(f"Reference:   {args.reference_file if args.reference_file else 'None'}")
        if exclude_indices:
            print(f"Exclude:     {exclude_indices} (indices)")
            # Show what the binary array will look like (preview for first 15 positions)
            preview_length = max(15, max(exclude_indices) + 1) if exclude_indices else 15
            preview_array = indices_to_exclude_array(exclude_indices, preview_length)
            print(f"             Binary: {preview_array[:15]}{'...' if preview_length > 15 else ''}")
    if weekdays:
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        selected = ', '.join(weekday_names[d] for d in weekdays)
        print(f"Weekdays:    {selected}")
    print(f"Delay:       {args.delay}s")
    print(f"Close delay: {args.close_delay}s")
    print("="*70 + "\n")

    # Start driver
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
                close_delay=args.close_delay,
                reference_file=args.reference_file,
                exclude_indices=exclude_indices
            )
    finally:
        end_driver(driver)



if __name__ == '__main__':
    main()