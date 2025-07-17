"""
Factory function for converting DeepResearchReport to HTML using the universal template system.
"""

from __future__ import annotations

from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.utils.html.template_manager import TemplateManager


def deep_research_to_html(deep_research_report: DeepResearchReport, html_file: str | None = None) -> str:
    """
    Convert a DeepResearchReport instance to a complete HTML document using the universal template system.

    Args:
        deep_research_report (DeepResearchReport): The deep research report model to render.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    template_manager = TemplateManager()
    html = template_manager.render_report("DEEPRESEARCH", deep_research_report.model_dump())
    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
