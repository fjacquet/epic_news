"""
Temporary script to regenerate the cross-reference report HTML from JSON data.
"""

import json

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.utils.html.cross_reference_report_html_factory import cross_reference_report_to_html

# Load JSON data
with open("output/osint/global_report.json", encoding="utf-8") as f:
    data = json.load(f)

# The root of the JSON is the report itself
report_model = CrossReferenceReport.model_validate(data)

# Generate HTML
html = cross_reference_report_to_html(report_model, html_file="output/osint/cross_reference_report.html")
print("✅ Cross-reference report HTML regenerated successfully")
