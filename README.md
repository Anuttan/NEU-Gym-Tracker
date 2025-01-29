# NEU Gym Tracker

Automated system to track and analyze occupancy levels at Northeastern University's recreational facilities. Data is collected hourly during operating hours and stored directly in this repository.

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Anuttan/neu-gym-tracker/scrape.yml?label=Scraping%20Job)
![Dataset Updated](https://img.shields.io/badge/dataset-updated%20hourly-brightgreen)

## Features

- Real-time tracking of all NEU recreation facilities:
  - Marino Center (all floors)
  - SquashBusters
- Collects key metrics:
  - Current occupancy count
  - Occupancy percentage
  - Facility status
  - Last update timestamp
- Automated hourly collection during operating hours
- Data stored directly in repository as CSV


## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/Anuttan/neu-gym-tracker.git
   cd neu-gym-tracker
   ```

2. Create necessary directories:
   ```bash
   mkdir -p .github/workflows
   ```

3. Copy required files:
   - `scraper.py` → Root directory
   - `scrape.yml` → `.github/workflows/`

4. Push to GitHub:
   ```bash
   git add .
   git commit -m "Initial setup"
   git push
   ```
   The GitHub Action will start automatically according to the defined schedule.

## Data Format

The collected data is stored in `data/gym_occupancy.csv` with the following columns:

| Column              | Description                           |
|--------------------|----------------------------------|
| `timestamp`        | Time of data collection          |
| `facility`        | Name of the facility            |
| `count`           | Number of people present        |
| `occupancy_percentage` | Percentage of capacity      |
| `status`          | Facility status (Open/Closed)   |
| `last_updated`    | Last recorded update            |

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── scrape.yml     # GitHub Actions workflow
├── data/
│   └── gym_occupancy.csv  # Collected data
├── scraper.py             # Main scraping script
└── README.md
```

## Local Development

Install required dependencies:
```bash
pip install selenium webdriver_manager gitpython pdfplumber pyppeteer
```

Run the scraper locally:
```bash
python scraper.py
```

## Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b new-feature
   ```
3. Make your changes.
4. Push your changes:
   ```bash
   git push origin new-feature
   ```
5. Submit a Pull Request.

## Acknowledgments

- Built for the Northeastern University community
- Data sourced from [NEU Recreation](https://recreation.northeastern.edu/)

## Questions or Issues?

Open an issue in this repository if you have any questions or encounter problems.

---
Made with ❤️ for Huskies

