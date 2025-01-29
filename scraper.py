import os
from datetime import datetime, time as dtime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import csv
import git

def is_facility_open(facility_name, current_time):
    """
    Check if a facility should be open based on its schedule
    """
    current_day = current_time.strftime('%A')
    current_hour = current_time.time()
    
    schedules = {
        'regular': {
            'Monday': (dtime(5, 30), dtime(23, 59)),
            'Tuesday': (dtime(5, 30), dtime(23, 59)),
            'Wednesday': (dtime(5, 30), dtime(23, 59)),
            'Thursday': (dtime(5, 30), dtime(23, 59)),
            'Friday': (dtime(5, 30), dtime(21, 0)),
            'Saturday': (dtime(8, 0), dtime(21, 0)),
            'Sunday': (dtime(8, 0), dtime(23, 59))
        },
        'alternative': {
            'Monday': (dtime(6, 0), dtime(23, 59)),
            'Tuesday': (dtime(6, 0), dtime(23, 59)),
            'Wednesday': (dtime(6, 0), dtime(23, 59)),
            'Thursday': (dtime(6, 0), dtime(23, 59)),
            'Friday': (dtime(6, 0), dtime(21, 0)),
            'Saturday': (dtime(8, 0), dtime(21, 0)),
            'Sunday': (dtime(10, 0), dtime(23, 59))
        }
    }
    
    schedule = schedules['alternative'] if 'SquashBusters' in facility_name else schedules['regular']
    
    if current_day in schedule:
        open_time, close_time = schedule[current_day]
        return open_time <= current_hour <= close_time
    
    return False

def setup_selenium():
    """
    Set up headless Chrome browser for Selenium
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def parse_facility_data(text_content):
    """
    Parse the facility counts from the text content
    """
    facilities = []
    lines = text_content.split('\n')
    current_facility = {}
    
    for line in lines:
        if '%' in line:
            if current_facility:
                facilities.append(current_facility)
            current_facility = {'occupancy_percentage': int(line.strip('%'))}
        
        count_match = re.search(r'Last Count: (\d+)', line)
        if count_match:
            current_facility['count'] = int(count_match.group(1))
        
        if '(Open)' in line or '(Closed)' in line:
            name_parts = line.split('(')
            current_facility['name'] = name_parts[0].strip()
            current_facility['status'] = '('+name_parts[1]
            
        if 'Updated:' in line:
            timestamp_str = line.split('Updated:')[1].strip()
            current_facility['last_updated'] = timestamp_str
    
    if current_facility:
        facilities.append(current_facility)
    
    return facilities

def scrape_gym_occupancy(url):
    """
    Scrape gym occupancy data using Selenium
    """
    driver = setup_selenium()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "content")))
        time.sleep(5)
        page_content = driver.find_element(By.TAG_NAME, "body").text
        return parse_facility_data(page_content)
    except Exception as e:
        print(f"Error scraping data: {e}")
        return None
    finally:
        driver.quit()

def update_csv(facilities_data, filename='data/gym_occupancy.csv'):
    """
    Update the CSV file with new data
    """
    current_time = datetime.now()
    
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'facility', 'count', 'occupancy_percentage', 
                           'status', 'last_updated'])
    
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        for facility in facilities_data:
            if is_facility_open(facility['name'], current_time):
                writer.writerow([
                    timestamp,
                    facility['name'],
                    facility['count'],
                    facility['occupancy_percentage'],
                    facility['status'],
                    facility['last_updated']
                ])

def commit_changes():
    """
    Commit and push changes to the repository
    """
    try:
        repo = git.Repo('.')
        repo.index.add(['data/gym_occupancy.csv'])
        repo.index.commit(f"Update gym occupancy data - {datetime.now()}")
    except Exception as e:
        print(f"Error committing changes: {e}")

def main():
    try:
        url = "https://recreation.northeastern.edu/"
        facilities_data = scrape_gym_occupancy(url)
        if facilities_data:
            update_csv(facilities_data)
            commit_changes()
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
