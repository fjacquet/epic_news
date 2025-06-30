"""
Factory function for converting FinancialReport to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.financial_report import FinancialReport
from epic_news.utils.html.template_manager import TemplateManager


def findaily_to_html(financial_report: FinancialReport, html_file: str | None = None) -> str:
    """
    Convert a FinancialReport instance to a complete HTML document using the universal template system.

    Args:
        financial_report (FinancialReport): The financial report model to render.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    template_manager = TemplateManager()
    html = template_manager.render_report("FINDAILY", financial_report.model_dump())
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
