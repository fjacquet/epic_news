"""
Factory function for converting SaintData to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.saint_data import SaintData
from epic_news.utils.html.template_manager import TemplateManager


def saint_to_html(saint_data: SaintData, html_file: str | None = None) -> str:
    """
    Convert a SaintData instance to a complete HTML document using the universal template system.

    Args:
        saint_data (SaintData): The saint data model to render.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    # Prepare content_data as expected by TemplateManager
    content_data = saint_data.to_template_data()
    template_manager = TemplateManager()
    html = template_manager.render_report("SAINT", content_data)
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
