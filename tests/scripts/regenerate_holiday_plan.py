import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json

from src.epic_news.utils.html.template_manager import TemplateManager

input_json_path = Path("output/holiday/itinerary.json")
output_html_path = Path("output/holiday/regenerated_itinerary.html")

if not input_json_path.exists():
    print(f"❌ Error: Input JSON file not found at {input_json_path}")
    print("Please run the HOLIDAY_PLANNER crew first to generate the data.")
    print("Command: crewai flow kickoff")
    exit(1)

with open(input_json_path, encoding="utf-8") as f:
    data = json.load(f)

tm = TemplateManager()
html = tm.render_report("HOLIDAY_PLANNER", data)
with open(output_html_path, "w", encoding="utf-8") as out:
    out.write(html)
print("✅ Holiday itinerary HTML regenerated successfully")
