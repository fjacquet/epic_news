#!/usr/bin/env python3
"""
Test script for meeting preparation HTML rendering.
This script loads the fixed JSON file and renders it to HTML using the improved renderer.
"""

import json

from epic_news.utils.html.meeting_prep_html_factory import meeting_prep_to_html

# Load the fixed JSON data
json_file = "output/meeting/meeting_preparation_fixed.json"
with open(json_file) as f:
    data = json.load(f)

# Render to a new HTML file
output_file = "output/meeting/meeting_preparation_new.html"
html = meeting_prep_to_html(data, html_file=output_file)

print(f"Successfully rendered HTML to {output_file}")
