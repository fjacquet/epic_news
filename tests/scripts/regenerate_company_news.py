"""
Temporary script to regenerate company news HTML from JSON data.
"""

import json

from src.epic_news.utils.html.company_news_html_factory import company_news_to_html

# Load JSON data
with open("output/holiday/itinerary.json", encoding="utf-8") as f:
    data = json.load(f)

# Generate HTML
html = company_news_to_html(data, html_file="output/holiday/regenerated_itinerary.html")
print("✅ Holiday itinerary HTML regenerated successfully")
