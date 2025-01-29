import os
import re
import csv
import asyncio
import pdfplumber
from datetime import datetime
from pyppeteer import launch

URL = "https://recreation.northeastern.edu/"
PDF_PATH = "gym_occupancy.pdf"
CSV_PATH = "data/gym_occupancy.csv"

# Step 1: Generate PDF
async def save_webpage_as_pdf(url, output_pdf):
    """
    Uses Pyppeteer (Headless Chrome) to save a webpage as a PDF.
    """
    print("Launching headless Chrome to save webpage as PDF...")

    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.goto(url, {"waitUntil": "networkidle2"})  # Ensure full page load

    await page.pdf({"path": output_pdf, "format": "A4"})

    await browser.close()
    print(f"Webpage saved as PDF: {output_pdf}")

def generate_pdf(url, output_pdf):
    asyncio.get_event_loop().run_until_complete(save_webpage_as_pdf(url, output_pdf))

# Step 2: Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from the PDF.
    """
    text_content = ""

    print("Extracting text from PDF...")
    if not os.path.exists(pdf_path):
        print(f"PDF file {pdf_path} not found!")
        return ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    return text_content

# Step 3: Parse Extracted Text
def parse_extracted_text(text_content):
    """
    Parses extracted text to retrieve gym occupancy data.
    """
    facilities = []
    lines = text_content.split('\n')
    current_facility = {}

    print("Parsing extracted text...")

    for i in range(len(lines)):
        line = lines[i].strip()
        
        if re.match(r'^\d+%$', line):  # Matches percentage (e.g., "30%")
            if current_facility:
                facilities.append(current_facility)
                print(f"Captured facility: {current_facility}")
            current_facility = {'occupancy_percentage': int(line.strip('%'))}

        elif 'Last Count:' in line:  # Matches "Last Count: 18"
            count_match = re.search(r'Last Count: (\d+)', line)
            if count_match:
                current_facility['count'] = int(count_match.group(1))

        elif '(Open)' in line or '(Closed)' in line:  # Matches facility name + status
            current_facility['name'] = lines[i-1].strip()  # Facility name is the line above
            current_facility['status'] = line.strip()

        elif 'Updated:' in line:  # Matches "Updated: 01/28/2025 11:31 PM"
            timestamp_match = re.search(r'Updated:\s*(.*)', line)
            if timestamp_match:
                current_facility['last_updated'] = timestamp_match.group(1).strip()

    if current_facility:
        facilities.append(current_facility)
        print(f"Captured facility: {current_facility}")

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

# Step 5: Run the Full Scraper
def main():
    try:
        print("Starting Gym Occupancy Scraper...")

        # Step 1: Generate PDF
        generate_pdf(URL, PDF_PATH)

        # Ensure PDF exists before proceeding
        if not os.path.exists(PDF_PATH):
            print("PDF was not created. Exiting.")
            return

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

        print("Scraper execution completed successfully.")

    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()