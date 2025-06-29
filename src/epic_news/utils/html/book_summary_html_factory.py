"""
Factory function for converting BookSummaryReport to HTML using the universal template system.
"""

from __future__ import annotations

import json

from epic_news.models.book_summary_report import BookSummaryReport
from epic_news.utils.html.template_manager import TemplateManager


def book_summary_to_html(book_summary: BookSummaryReport, html_file: str | None = None) -> str:
    """
    Convert a BookSummaryReport instance to a complete HTML document using the universal template system.

    Args:
        book_summary (BookSummaryReport): The book summary model to render.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    # Prepare content_data as expected by TemplateManager
    content_data = book_summary.model_dump()
    template_manager = TemplateManager()
    html = template_manager.render_report("BOOK_SUMMARY", content_data)
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html


def book_summary_from_json(json_path: str) -> BookSummaryReport:
    """
    Load a BookSummaryReport from a JSON file.
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return BookSummaryReport(**data)
