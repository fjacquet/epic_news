"""
Temporary script to regenerate the cross-reference report HTML from JSON data.
"""

import json

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.utils.html.template_manager import TemplateManager

# Load JSON data
with open("output/osint/global_report.json", encoding="utf-8") as f:
    data = json.load(f)

# The root of the JSON is the report itself
report_model = CrossReferenceReport.model_validate(data)

# Generate HTML via TemplateManager
tm = TemplateManager()
output_path = "output/osint/cross_reference_report.html"
html = tm.render_report("CROSS_REFERENCE_REPORT", report_model)
with open(output_path, "w", encoding="utf-8") as out:
    out.write(html)
print("✅ Cross-reference report HTML regenerated successfully")
