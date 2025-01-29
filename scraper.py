import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os
from datetime import datetime

PARENT_URL = "https://recreation.northeastern.edu"
CSV_PATH = "data/gym_occupancy.csv"


def get_iframe_url(parent_url):
    """
    Fetches the parent page and attempts to find the iframe
    pointing to widget (or whichever domain).
    Returns the absolute URL of that iframe, or None if not found.
    """
    resp = requests.get(parent_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Example: look for any <iframe> whose src contains widget
    iframe = soup.find('iframe', src=lambda x: x and "connect2mycloud.com" in x)
    if not iframe:
        return None

    iframe_src = iframe['src']
    # Make sure it's an absolute URL
    absolute_url = urljoin(parent_url, iframe_src)
    return absolute_url


def scrape_widget(iframe_url):
    """
    Scrapes the HTML from the widget iframe URL
    and extracts each location's occupancy info.
    Returns a list of dicts with the data.
    """
    resp = requests.get(iframe_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Each location is inside <div class="col-md-3 col-sm-6">
    blocks = soup.select('div.col-md-3.col-sm-6')

    results = []
    for block in blocks:
        # The circleChart div has data attributes like data-percent, data-lastcount, data-isclosed
        circle_div = block.select_one('div.circleChart')
        if not circle_div:
            continue

        data_percent = circle_div.get('data-percent', '0')
        data_lastcount = circle_div.get('data-lastcount', '0')
        data_isclosed = circle_div.get('data-isclosed', 'false')

        # The text block (centered div) typically has location name, status, last count, etc.
        text_div = block.select_one('div[style="text-align:center;"]')
        if not text_div:
            continue

        # Extract text lines
        lines = list(text_div.stripped_strings)
        # Example lines:
        # [
        #   "Marino Center - Studio A",
        #   "(Open)",
        #   "Last Count: 8",
        #   "Updated: 01/29/2025 09:26 AM"
        # ]

        if len(lines) < 4:
            continue

        location = lines[0]
        status_str = lines[1]  # e.g., "(Open)"
        status_clean = status_str.strip("()")  # remove parentheses

        last_count_str = lines[2].replace("Last Count: ", "")
        updated_str = lines[3].replace("Updated: ", "")

        # Convert numeric fields
        try:
            percent_val = float(data_percent)
        except ValueError:
            percent_val = None

        # last_count might be integer or float
        try:
            last_count_val = int(last_count_str)
        except ValueError:
            try:
                last_count_val = float(last_count_str)
            except ValueError:
                last_count_val = None

        is_closed = (data_isclosed.lower() == 'true')

        row = {
            "location": location,
            "status": status_clean,       # e.g., "Open" or "Closed"
            "is_closed": is_closed,       
            "percent": percent_val,       # e.g., 45.0
            "last_count": last_count_val, # e.g., 27
            "updated": updated_str        # "01/29/2025 09:01 AM"
        }
        results.append(row)

    return results


def append_to_csv(results, csv_path=CSV_PATH):
    """
    Appends the scraped location results to a CSV file (csv_path),
    one row per location, with a timestamp for each scrape.
    """
    # Ensure the data/ directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    file_exists = os.path.isfile(csv_path)
    timestamp_utc = datetime.utcnow().isoformat()

    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header if CSV does not exist yet
            writer.writerow([
                "timestamp_utc",
                "location",
                "percent",
                "last_count",
                "status",
                "is_closed",
                "updated"
            ])
        
        for row in results:
            writer.writerow([
                timestamp_utc,
                row.get("location", ""),
                row.get("percent", ""),
                row.get("last_count", ""),
                row.get("status", ""),
                row.get("is_closed", ""),
                row.get("updated", "")
            ])


def main():
    # 1. Find the widget iframe URL from the parent site
    iframe_url = get_iframe_url(PARENT_URL)
    if not iframe_url:
        print("WARNING: Could not find the widget iframe on the parent page.")
        return

    results = scrape_widget(iframe_url)
    append_to_csv(results, CSV_PATH)

    print(f"Appended {len(results)} rows to {CSV_PATH}.")


if __name__ == "__main__":
    main()
