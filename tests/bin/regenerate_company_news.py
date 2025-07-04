"""
Temporary script to regenerate company news HTML from JSON data.
"""

import json

from src.epic_news.utils.html.company_news_html_factory import company_news_to_html

# Load JSON data
with open("output/company_news/report.json", encoding="utf-8") as f:
    data = json.load(f)

# Generate HTML
html = company_news_to_html(data, html_file="output/company_news/report.html")
print("✅ HTML report regenerated successfully")
