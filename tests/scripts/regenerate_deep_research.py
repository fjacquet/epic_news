#!/usr/bin/env python3
"""
Temporary script to regenerate deep research HTML from JSON data.
"""

import json

from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.utils.html.deep_research_html_factory import deep_research_to_html

# Load JSON data
with open("output/deep_research/report.json", encoding="utf-8") as f:
    data = json.load(f)

# Parse JSON to DeepResearchReport model
report_model = DeepResearchReport.model_validate(data)

# Generate HTML
html = deep_research_to_html(report_model, html_file="output/deep_research/regenerated_report.html")
print("✅ Deep research report HTML regenerated successfully")
