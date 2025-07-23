"""
Temporary script to regenerate book summary HTML from JSON data.
"""

from epic_news.utils.html.book_summary_html_factory import (
    book_summary_from_json,
    book_summary_to_html,
)

# Define the path to the JSON data
# Note: You may need to update this path to your actual JSON output file.
json_file_path = "output/library/book_summary.json"

# Load the book summary from the JSON file into a Pydantic model
book_summary_model = book_summary_from_json(json_file_path)

# Generate HTML from the Pydantic model
html = book_summary_to_html(book_summary_model, html_file="output/library/regenerated_book_summary.html")
print("✅ Book summary HTML regenerated successfully")
