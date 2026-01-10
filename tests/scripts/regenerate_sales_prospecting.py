import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json

from epic_news.utils.data_normalization import normalize_structured_data_report
from epic_news.utils.html.template_manager import TemplateManager

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

tm = TemplateManager()
html = tm.render_report("SALES_PROSPECTING", data)
with open(output_html_path, "w", encoding="utf-8") as out:
    out.write(html)
print("✅ Sales prospecting report HTML regenerated successfully")
print(f"Output saved to: {output_html_path}")
