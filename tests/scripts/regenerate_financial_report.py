import json
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.epic_news.models.crews.financial_report import FinancialReport
from src.epic_news.utils.html.fin_daily_html_factory import findaily_to_html

def main():
    """Reads a JSON report, converts it to HTML, and saves it."""
    json_path = 'output/findaily/report.json'
    html_path = 'output/findaily/report.html'

    print(f"Reading financial report from {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
        return

    print("Parsing JSON data into FinancialReport model...")
    try:
        financial_report = FinancialReport(**report_data)
    except Exception as e:
        print(f"Error creating FinancialReport model: {e}")
        return

    print(f"Generating HTML report and saving to {html_path}...")
    findaily_to_html(financial_report, html_file=html_path)

    print("✅ HTML report regenerated successfully.")

if __name__ == "__main__":
    main()
