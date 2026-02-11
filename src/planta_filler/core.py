# =============================================================================
# core.py - Selenium Browser Control and PLANTA Interaction
# =============================================================================
# This module contains the core Selenium-based automation logic for interacting
# with the PLANTA timesheet system. It handles browser lifecycle, page navigation,
# data extraction, and field updates.
#
# Main functions:
# - start_driver(): Initialize Firefox WebDriver with optional persistent profile
# - end_driver(): Close the browser
# - set_week(): Fill hours for a week using specified strategy
# - reset_week(): Reset all hours to zero
# - get_hours_per_day(): Extract current hours from PLANTA DOM
# - get_target_hours_per_day(): Extract target hours (Anwesend) from DOM
# - filter_dates_by_weekdays(): Filter dates by weekday selection
# =============================================================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from .calculations import fill_day
from .config import (
    DEFAULT_DELAY, DEFAULT_CLOSE_DELAY, SELECTORS
)
from .week_handler import parse_week_spec, get_monday_of_week
from .reference_handler import load_reference_for_weekday, ensure_reference_file
from .config import DEFAULT_REFERENCE_FILE


def _assert_planta_pulse_title(driver):
    """Verify the page title contains 'PLANTA Pulse'. Raise with helpful message if not."""
    try:
        title = getattr(driver, 'title', '') or ''
    except Exception:
        title = ''
    if 'planta pulse' not in title.lower():
        raise Exception("URL invalid or try with VPN turned on (page title does not contain 'PLANTA Pulse')")


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


def end_driver(driver):
    driver.quit()


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


def navigate_weeks(driver, weeks: int, step_delay: float = 0.0):
    """Navigate by full weeks using week navigation arrows.
    Positive weeks -> go back in time (left). Negative -> forward (right).
    Each click moves exactly one week.
    """
    if weeks == 0:
        return
    selector = SELECTORS['navigation']['week_back'] if weeks > 0 else SELECTORS['navigation']['week_forward']
    clicks = abs(weeks)
    for _ in range(clicks):
        el = driver.find_element(By.CSS_SELECTOR, selector)
        try:
            el.click()
        except Exception:
            parent = driver.find_element(By.CSS_SELECTOR, selector + ":not(i)")
            parent.click()
        if step_delay:
            time.sleep(step_delay)

        # Optional: verify the week actually changed by reading the date picker input
        try:
            dp_input = driver.find_element(By.CSS_SELECTOR, SELECTORS['navigation']['week_picker_input'])
            _ = dp_input.get_attribute('value')
        except Exception:
            pass


def _process_visible_week(driver, strategy: str, weekdays: Optional[List[int]], delay: float, post_randomization: float, reference_day: Optional[list]=None, reference_file: Optional[str]=None):
    print("\n📊 Extracting data...")
    hours_data = get_hours_per_day(driver)
    target_hours_map = get_target_hours_per_day(driver)

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
    if strategy == 'copy_reference':
        # Announce which file will be used to load reference values
        print(f"   Reference file: {reference_file or 'DEFAULT'}")

    for idx, date in enumerate(working_dates, 1):
        # Determine slots and weekday index for potential reference loading
        entries = hours_data[date]
        current_values = [hours for _, hours in entries]
        num_slots = len(current_values)
        weekday_index = datetime.strptime(date, '%Y-%m-%d').weekday()

        # Load per-day reference vector
        local_reference_day = reference_day if (reference_day is not None and len(reference_day) == num_slots) else None
        ref_fallback = False
        fallback_reason = None
        if strategy == 'copy_reference' and local_reference_day is None:
            filepath = reference_file or DEFAULT_REFERENCE_FILE
            try:
                # Only auto-adapt dimensions for the default packaged file
                if Path(filepath).resolve() == Path(DEFAULT_REFERENCE_FILE).resolve():
                    ensure_reference_file(filepath, num_slots)
                loaded = load_reference_for_weekday(filepath, weekday_index, num_slots)
                local_reference_day = loaded
            except Exception as e:
                ref_fallback = True
                fallback_reason = str(e)
                local_reference_day = [1.0] * num_slots

        if strategy == 'copy_reference':
            if ref_fallback:
                print(f"   No reference day used for {date} ({fallback_reason}); falling back to equal")
            elif local_reference_day is not None:
                preview = ", ".join(str(x) for x in local_reference_day[:5])
                if len(local_reference_day) > 5:
                    preview += ", ..."
                print(f"   Using reference day for {date} ({len(local_reference_day)} slots): [{preview}]")

        day_target = target_hours_map.get(date, 8.0)
        weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%a')

        current_sum = sum(current_values)

        print(f"📅 {date} ({weekday}) - Target: {day_target:.2f}h, Current: {current_sum:.2f}h")

        # Build exclude mask for this day based on CLI indices (0-based) and slots count
        ex_mask = []
        # Read exclude indices attached by set_week, if any
        exclude_indices = getattr(_process_visible_week, 'exclude_indices', None)
        if exclude_indices is not None:
            ex_mask = [1 if i in exclude_indices else 0 for i in range(num_slots)]

        new_values = fill_day(
            override_mode=True,
            strategy=strategy,
            exclude_values=ex_mask,
            total_hours=day_target,
            current_values=current_values,
            retries=3,
            precision=2,
            reference_day=(local_reference_day if strategy == 'copy_reference' else []),
            post_randomization=post_randomization
        )
        print(f"   Calculated distribution: {new_values} (sum: {sum(new_values):.2f}h)")

        # Print old vs new values
        diffs = []
        for old, new in zip(current_values, new_values):
            diffs.append(f"{old} -> {new}")
        print("   Changes (old -> new): " + "; ".join(diffs))

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


def set_week(
    driver, 
    url: str,
    strategy: str = 'random',
    weekdays: Optional[List[int]] = None,
    skip_login_prompt: bool = False,
    delay: float = DEFAULT_DELAY,
    close_delay: float = DEFAULT_CLOSE_DELAY,
    post_randomization: float = 0.0,
    week_specs: Optional[List[str]] = None,
    reference_day: Optional[list] = None,
    reference_file: Optional[str] = None,
    exclude_indices: Optional[list[int]] = None,
):
    try:
        driver.get(url)
        
        # Verify the site looks like PLANTA Pulse
        _assert_planta_pulse_title(driver)
        
        if not skip_login_prompt:
            input("⏸️  Press ENTER after you've logged in...")
        
        WebDriverWait(driver, SELECTORS['timeouts']['presence_seconds']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['selectors']['hours_input']))
        )
        
        # Determine requested week offsets (relative to current week)
        if week_specs is None:
            requested = ["0"]
        else:
            requested = week_specs

        # Compute integer week offsets from today for all specs
        today = datetime.now()
        current_year, current_week = today.isocalendar()[0], today.isocalendar()[1]
        current_monday = get_monday_of_week(current_year, current_week)

        def week_offset(spec: str) -> int:
            ty, tw = parse_week_spec(spec)
            target_monday = get_monday_of_week(ty, tw)
            return int((target_monday - current_monday).days // 7)

        # Preserve the order given by the user (no sorting)
        offsets = [week_offset(s) for s in requested]

        # Process each requested week, navigating between them
        current_offset = 0
        for off in offsets:
            step = current_offset - off  # positive -> navigate back in time
            if step != 0:
                navigate_weeks(driver, step, step_delay=0.0)
                current_offset = off

            # Attach exclude_indices to function local scope for _process_visible_week via attribute
            try:
                _process_visible_week.exclude_indices = exclude_indices
            except Exception:
                pass
            _process_visible_week(
                driver,
                strategy=strategy,
                weekdays=weekdays,
                delay=delay,
                post_randomization=post_randomization,
                reference_day=reference_day,
                reference_file=reference_file,
            )

        print("✅ ALL DAYS PROCESSED!")
        print(f"\n⏳ Waiting {close_delay} seconds before closing browser...")
        print("   (You can verify the values in the browser during this time)")
        
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
    close_delay: float = DEFAULT_CLOSE_DELAY,
    skip_login_prompt: bool = False,
    week_specs: Optional[List[str]] = None,
    exclude_indices: Optional[list[int]] = None,
):
    try:
        driver.get(url)
        
        # Verify the site looks like PLANTA Pulse
        _assert_planta_pulse_title(driver)
        
        if not skip_login_prompt:
            input("⏸️  Press ENTER after you've logged in...")
        
        WebDriverWait(driver, SELECTORS['timeouts']['presence_seconds']).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS['selectors']['hours_input']))
        )

        # Determine requested week offsets (relative to current week)
        if week_specs is None:
            requested = ["0"]
        else:
            requested = week_specs

        today = datetime.now()
        current_year, current_week = today.isocalendar()[0], today.isocalendar()[1]
        current_monday = get_monday_of_week(current_year, current_week)

        def week_offset(spec: str) -> int:
            ty, tw = parse_week_spec(spec)
            target_monday = get_monday_of_week(ty, tw)
            return int((target_monday - current_monday).days // 7)

        offsets = [week_offset(s) for s in requested]

        # Process each requested week, navigating between them
        current_offset = 0
        for off in offsets:
            step = current_offset - off  # positive -> navigate back in time
            if step != 0:
                navigate_weeks(driver, step, step_delay=0.0)
                current_offset = off

            hours_data = get_hours_per_day(driver)
            sorted_dates = sorted(hours_data.keys())

            if weekdays is not None:
                sorted_dates = filter_dates_by_weekdays(sorted_dates, weekdays)

            print(f"\n🔄 Resetting {len(sorted_dates)} days in specified week...\n")

            for date in sorted_dates:
                entries = hours_data[date]
                num_slots = len(entries)
                # Build exclude mask for this day
                ex_mask = []
                if exclude_indices is not None:
                    ex_mask = [1 if i in exclude_indices else 0 for i in range(num_slots)]

                for idx, (field_id, _) in enumerate(entries):
                    # Skip excluded indices
                    if ex_mask and ex_mask[idx] == 1:
                        continue
                    field = driver.find_element(By.ID, field_id)
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys('0')
                        driver.execute_script("arguments[0].blur();", field)
                        time.sleep(delay)
                print(f"   ✅ {date} reset")

        print("\n✅ All specified weeks reset!")
        print(f"\n⏳ Waiting {close_delay} seconds before closing browser...")
        print("   (You can verify the reset in the browser during this time)")
        
        for remaining in range(int(close_delay), 0, -1):
            print(f"   Closing in {remaining} seconds...", end='\r')
            time.sleep(1)
        
        print("\n\n🔒 Closing browser now...")
        
    except Exception as e:
        raise Exception(f"Resetting week failed: {str(e)}")
