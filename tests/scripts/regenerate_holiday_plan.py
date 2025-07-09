import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json

from src.epic_news.utils.html.holiday_planner_html_factory import holiday_planner_to_html

input_json_path = Path("output/holiday/itinerary.json")
output_html_path = Path("output/holiday/regenerated_itinerary.html")

if not input_json_path.exists():
    print(f"❌ Error: Input JSON file not found at {input_json_path}")
    print("Please run the HOLIDAY_PLANNER crew first to generate the data.")
    print("Command: crewai flow kickoff")
    exit(1)

with open(input_json_path, encoding="utf-8") as f:
    data = json.load(f)

html = holiday_planner_to_html(data, html_file=str(output_html_path))
print("✅ Holiday itinerary HTML regenerated successfully")
