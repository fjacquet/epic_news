import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json

from src.epic_news.utils.data_normalization import normalize_structured_data_report
from src.epic_news.utils.html.sales_prospecting_html_factory import sales_prospecting_report_to_html

input_json_path = Path("output/sales_prospecting/report.json")
output_html_path = Path("output/sales_prospecting/regenerated_report.html")

if not input_json_path.exists():
    print(f"❌ Error: Input JSON file not found at {input_json_path}")
    print("Please run the SALES_PROSPECTING crew first to generate the data.")
    print("Command: crewai flow kickoff")
    exit(1)

with open(input_json_path, encoding="utf-8") as f:
    data = json.load(f)

# Apply normalization to ensure proper enum values
if "sales_metrics" in data:
    data["sales_metrics"] = normalize_structured_data_report(data["sales_metrics"])

html = sales_prospecting_report_to_html(data, html_file=str(output_html_path))
print("✅ Sales prospecting report HTML regenerated successfully")
print(f"Output saved to: {output_html_path}")
