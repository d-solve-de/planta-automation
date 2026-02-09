from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import argparse
import sys
import re
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from calculations import fill_day
from config import (
    DEFAULT_URL, DEFAULT_STRATEGY, DEFAULT_WEEKDAYS, DEFAULT_DELAY,
    DEFAULT_CLOSE_DELAY, DEFAULT_USE_PERSISTENT_PROFILE, DEFAULT_HEADLESS,
    VALID_STRATEGIES, VALID_WEEKDAYS, MAX_DELAY, MIN_DELAY
)
from validation import validate_all_inputs, ValidationError
from week_handler import parse_week_spec, format_week_display


def load_selectors(config_path: Path = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).parent / 'planta_selectors.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

SELECTORS = load_selectors()


def start_driver(headless: bool = False, use_persistent_profile: bool = True):
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
    target_hours = {}
    load_divs = driver.find_elements(By.CSS_SELECTOR, SELECTORS['selectors']['target_hours_div'])
    
    for div in load_divs:
        class_attr = div.get_attribute('class')
        match = re.search(SELECTORS['patterns']['date_attr_regex'], class_attr)
        
        if match:
            date_str = match.group(1)
            date_formatted = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            text = div.text.strip().replace(',', '.')
            hours_match = re.findall(r'(\d+\.?\d*)', text)
            if hours_match:
                target_hours[date_formatted] = float(hours_match[0])
    
    return target_hours



def get_hours_per_day(driver) -> Dict[str, List[Tuple[str, float]]]:
    all_fields = driver.find_elements(By.CSS_SELECTOR, SELECTORS['selectors']['hours_input'])
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
    close_delay: float = DEFAULT_CLOSE_DELAY
):
    try:
        driver.get(url)
        
        if not skip_login_prompt:
            input("⏸️  Press ENTER after you've logged in...")
        
        WebDriverWait(driver, SELECTORS['timeouts']['presence_seconds']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['selectors']['hours_input']))
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
            weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
            
            entries = hours_data[date]
            current_values = [hours for _, hours in entries]
            current_sum = sum(current_values)
            
            print(f"📅 {date} ({weekday}) - Target: {day_target:.2f}h, Current: {current_sum:.2f}h")
            
            # Calculate new values
            new_values = fill_day(
                override_mode=True,
                strategy=strategy,
                exclude_values=[],
                total_hours=day_target,
                current_values=current_values,
                retries=3,
                precision=2
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
    try:
        driver.get(url)
        input("⏸️  Press ENTER after you've logged in...")
        
        WebDriverWait(driver, SELECTORS['timeouts']['presence_seconds']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['selectors']['hours_input']))
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
    driver.quit()



def print_man_page():
    man_page_path = Path(__file__).parent / 'man_page.txt'
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
  python planta_filler.py

  # Fill with equal distribution
  python planta_filler.py --strategy equal

  # Fill only Mon, Wed, Fri
  python planta_filler.py --weekdays 0,2,4
  
  # Reset to zero
  python planta_filler.py --reset
  
  # Use persistent profile (saves login)
  python planta_filler.py --persistent

  # Wait 10 seconds before closing
  python planta_filler.py --close-delay 10

  # Show full manual
  python planta_filler.py --man

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
                close_delay=args.close_delay
            )
    finally:
        end_driver(driver)



if __name__ == '__main__':
    main()
