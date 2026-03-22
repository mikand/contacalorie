# contacalorie
A simple web app to compute and report the bill subdivision for a specific condo heating system

## Setup

1. Install dependencies: `pip install -r requirements.txt`

2. Populate the database: Run `python -c "from calorie import populate_from_sheets; populate_from_sheets()"` to import data from the Google Spreadsheet.

3. Run the app: `python website.py`

The app now uses SQLAlchemy with SQLite instead of Google Sheets.
