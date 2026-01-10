"""
Temporary script to regenerate company news HTML from JSON data.
"""

import json

from epic_news.utils.html.template_manager import TemplateManager

# Load JSON data
with open("output/holiday/itinerary.json", encoding="utf-8") as f:
    data = json.load(f)

# Generate HTML via TemplateManager
tm = TemplateManager()
output_path = "output/holiday/regenerated_itinerary.html"
html = tm.render_report("COMPANY_NEWS", data)
with open(output_path, "w", encoding="utf-8") as out:
    out.write(html)
print("✅ Holiday itinerary HTML regenerated successfully")
