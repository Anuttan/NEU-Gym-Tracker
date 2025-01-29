import re
import os
import csv
import pdfplumber
from datetime import datetime

CSV_PATH = "data/gym_occupancy.csv"
PDF_PATH = "gym_occupancy.pdf"

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from the PDF.
    """
    text_content = ""

    print("\nExtracting text from PDF...\n")
    if not os.path.exists(pdf_path):
        print(f"PDF file {pdf_path} not found!")
        return ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"

    return text_content

def parse_extracted_text(text_content):
    """
    Parses extracted text to retrieve gym occupancy data.
    """
    facilities = []
    lines = text_content.split('\n')
    current_facility = {}

    print("\nParsing extracted text...\n")

    for i in range(len(lines)):
        line = lines[i].strip()
        
        if re.match(r'^\d+%$', line):  # Matches percentage (e.g., "30%")
            if current_facility:  # Save previous facility before starting a new one
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

    print(f"\nTotal facilities parsed: {len(facilities)}\n")
    return facilities

def update_csv(facilities_data, filename=CSV_PATH):
    """
    Updates the CSV file with new occupancy data.
    """
    current_time = datetime.now()
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Create CSV with headers if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'facility', 'count', 'occupancy_percentage', 'status', 'last_updated'])

    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

    print("\nWriting data to CSV...\n")
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

def main():
    try:
        print("\nStarting Gym Occupancy Scraper...\n")

        # Step 1: Extract text from the PDF
        pdf_text = extract_text_from_pdf(PDF_PATH)

        if not pdf_text.strip():
            print("No text extracted. Exiting.")
            return

        # Step 2: Parse extracted text
        facilities_data = parse_extracted_text(pdf_text)

        if not facilities_data:
            print("No facility data extracted. Exiting.")
            return

        # Step 3: Update CSV
        update_csv(facilities_data)

        print("\nScraper execution completed successfully.\n")

    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
