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
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from .calculations import fill_day
from .config import (
    DEFAULT_DELAY, DEFAULT_CLOSE_DELAY, SELECTORS
)


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
        
        for idx, date in enumerate(working_dates, 1):
            day_target = target_hours_map.get(date, 8.0)
            weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
            
            entries = hours_data[date]
            current_values = [hours for _, hours in entries]
            current_sum = sum(current_values)
            
            print(f"📅 {date} ({weekday}) - Target: {day_target:.2f}h, Current: {current_sum:.2f}h")
            
            new_values = fill_day(
                override_mode=True,
                strategy=strategy,
                exclude_values=[],
                total_hours=day_target,
                current_values=current_values,
                retries=3,
                precision=2,
                post_randomization=False
            )
            print(f"   Calculated distribution: {new_values} (sum: {sum(new_values):.2f}h)")
            
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
        
        for remaining in range(int(close_delay), 0, -1):
            print(f"   Closing in {remaining} seconds...", end='\r')
            time.sleep(1)
        
        print("\n\n🔒 Closing browser now...")
        
    except Exception as e:
        raise Exception(f"Resetting week failed: {str(e)}")
