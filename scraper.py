import asyncio
import os
import csv
from datetime import datetime
from playwright.async_api import async_playwright

CSV_PATH = "data/facility_data.csv"

async def scrape_recreation(url):
    """
    Fetches occupancy data from the given URL and extracts relevant facility details.
    Returns a list of dictionaries containing location details.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        facilities = await page.query_selector_all("div[style='text-align:center;']")
        data_list = []
        
        for facility in facilities:
            lines = await facility.inner_text()
            lines = [line.strip() for line in lines.split("\n") if line.strip()]
            
            if len(lines) >= 4 and any(loc in lines[0] for loc in [
                "SquashBusters - 4th Floor",
                "Marino Center - Studio A",
                "Marino Center - Studio B",
                "Marino Center - 2nd Floor",
                "Marino Center - Gymnasium",
                "Marino Center - 3rd Floor Weight Room",
                "Marino Center - 3rd Floor Select & Cardio"]):
                name = lines[0]
                status = lines[1]
                last_count = lines[2].split(": ")[-1]
                updated = lines[3].split(": ")[-1]
                
                data_list.append({
                    "location": name,
                    "last_count": last_count,
                    "status": status,
                    "is_closed": "Closed" in status,
                    "updated": updated
                })
        
        await browser.close()
    return data_list

async def append_to_csv(results, csv_path=CSV_PATH):
    """
    Appends occupancy data to a CSV file, adding a new row for each location
    with the current UTC timestamp. If the file does not exist, it creates a header.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    timestamp_utc = datetime.utcnow().isoformat()
    
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow([
                "timestamp_utc",
                "location",
                "last_count",
                "status",
                "is_closed",
                "updated"
            ])
        
        for row in results:
            writer.writerow([
                timestamp_utc,
                row.get("location", ""),
                row.get("last_count", ""),
                row.get("status", ""),
                row.get("is_closed", ""),
                row.get("updated", "")
            ])

async def main():
    """
    Main function that fetches data and saves it to CSV.
    """
    url = "https://www.connect2mycloud.com/Widgets/Data/locationCount?type=circle&key=2a2be0d8-df10-4a48-bedd-b3bc0cd628e7&loc_status=false"
    scraped_data = await scrape_recreation(url)
    if scraped_data:
        await append_to_csv(scraped_data)

if __name__ == "__main__":
    asyncio.run(main())