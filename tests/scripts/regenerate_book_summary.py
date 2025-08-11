"""
Temporary script to regenerate book summary HTML from JSON data.
"""

import json

from src.epic_news.models.crews.book_summary_report import BookSummaryReport
from src.epic_news.utils.html.template_manager import TemplateManager

# Define the path to the JSON data
# Note: You may need to update this path to your actual JSON output file.
json_file_path = "output/library/book_summary.json"

# Load and validate into a Pydantic model
with open(json_file_path, encoding="utf-8") as f:
    data = json.load(f)
book_summary_model = BookSummaryReport.model_validate(data)

# Generate HTML via TemplateManager
tm = TemplateManager()
output_path = "output/library/regenerated_book_summary.html"
html = tm.render_report("BOOK_SUMMARY", book_summary_model)
with open(output_path, "w", encoding="utf-8") as out:
    out.write(html)
print("✅ Book summary HTML regenerated successfully")
