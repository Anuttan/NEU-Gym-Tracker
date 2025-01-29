import os
import time
import re
import csv
import git
import pdfplumber

from datetime import datetime, time as dtime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Constants
URL = "https://recreation.northeastern.edu/"
PDF_PATH = "gym_occupancy.pdf"
CSV_PATH = "data/gym_occupancy.csv"

# Step 1: Save Webpage as PDF
def save_webpage_as_pdf(url, output_pdf):
    """
    Uses Selenium to open the webpage and print it as a PDF.
    """
    print("Launching Selenium to save webpage as PDF...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--kiosk-printing")  # Enable headless printing

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)  # Allow page to load

        driver.execute_script("window.print();")  # Simulate "Print to PDF"
        print(f"Webpage saved as PDF: {output_pdf}")
    
    except Exception as e:
        print(f"Error saving webpage as PDF: {e}")
    
    finally:
        driver.quit()

# Step 2: Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from the PDF.
    """
    text_content = ""
    
    print("Extracting text from PDF...")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"
    
    if text_content.strip():
        print("Successfully extracted text from PDF.")
    else:
        print("No text extracted! The PDF may be empty or improperly formatted.")
    
    return text_content

# Step 3: Parse Extracted Text
def parse_extracted_text(text_content):
    """
    Parses extracted text to retrieve gym occupancy data.
    """
    facilities = []
    lines = text_content.split('\n')

    print("Parsing extracted text...")
    current_facility = {}

    for line in lines:
        line = line.strip()
        print(f"Line: {line}")  # Debug output

        if '%' in line:  # Extract occupancy percentage
            match = re.search(r'(\d+)%', line)
            if match:
                if current_facility and 'name' in current_facility:
                    facilities.append(current_facility)
                    print(f"Parsed facility: {current_facility}")
                current_facility = {'occupancy_percentage': int(match.group(1))}

        count_match = re.search(r'Last Count: (\d+)', line)
        if count_match:
            current_facility['count'] = int(count_match.group(1))

        if '(Open)' in line or '(Closed)' in line:  # Extract facility name and status
            name_match = re.match(r"(.+?)\s*\((Open|Closed)\)", line)
            if name_match:
                current_facility['name'] = name_match.group(1).strip()
                current_facility['status'] = f"({name_match.group(2)})"

        if 'Updated:' in line:  # Extract last updated timestamp
            timestamp_match = re.search(r'Updated:\s*(.*)', line)
            if timestamp_match:
                current_facility['last_updated'] = timestamp_match.group(1).strip()

    if current_facility and 'name' in current_facility:
        facilities.append(current_facility)
        print(f"Parsed facility (final): {current_facility}")

    print(f"Total facilities parsed: {len(facilities)}")
    return facilities

# Step 4: Save Data to CSV
def update_csv(facilities_data, filename=CSV_PATH):
    """
    Updates the CSV file with new occupancy data.
    """
    current_time = datetime.now()
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'facility', 'count', 'occupancy_percentage', 'status', 'last_updated'])

    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

    print("Writing data to CSV...")
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        for facility in facilities_data:
            writer.writerow([
                timestamp,
                facility.get('name', 'Unknown'),
                facility.get('count', 0),
                facility.get('occupancy_percentage', 0),
                facility.get('status', 'Unknown'),
                facility.get('last_updated', 'Unknown')
            ])
    print(f"Data written to CSV: {filename}")

# Step 5: Commit & Push to GitHub
def commit_changes():
    """
    Commits and pushes changes to the GitHub repository.
    """
    try:
        repo = git.Repo('.')
        repo.index.add([CSV_PATH])
        repo.index.commit(f"Update gym occupancy data - {datetime.now()}")
        repo.remote().push()
        print("Changes committed and pushed to GitHub.")
    except Exception as e:
        print(f"Error committing changes: {e}")

# Step 6: Run the Full Scraper
def main():
    try:
        print("Starting the Gym Occupancy Scraper...")
        
        # Step 1: Save webpage as PDF
        save_webpage_as_pdf(URL, PDF_PATH)

        # Step 2: Extract text from the PDF
        pdf_text = extract_text_from_pdf(PDF_PATH)

        if not pdf_text.strip():
            print("No text extracted. Exiting.")
            return

        # Step 3: Parse extracted text
        facilities_data = parse_extracted_text(pdf_text)

        if not facilities_data:
            print("No facility data extracted. Exiting.")
            return

        # Step 4: Update CSV
        update_csv(facilities_data)

        # Step 5: Commit & Push Changes
        commit_changes()

        print("Scraper execution completed successfully!")

    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
