"""
Factory function to convert a NewsDailyReport (or compatible dict) to HTML using TemplateManager.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.
"""

import os

from epic_news.models.news_daily_report import NewsDailyReport
from epic_news.utils.debug_utils import parse_crewai_output
from epic_news.utils.html.template_manager import TemplateManager


def daily_news_to_html(news_daily_report, html_file=None):
    """
    Converts a validated NewsDailyReport (Pydantic model or dict) to HTML using TemplateManager.
    If html_file is provided, writes the HTML to disk.
    Returns the HTML string.
    """
    # Parse CrewAI output if needed (CrewOutput, dict, or model)
    if hasattr(news_daily_report, "raw"):
        # CrewOutput: parse raw JSON
        content_data = parse_crewai_output(news_daily_report, NewsDailyReport)

    elif hasattr(news_daily_report, "model_dump"):
        # Pydantic model
        content_data = news_daily_report.model_dump()
    elif isinstance(news_daily_report, dict):
        content_data = news_daily_report
    else:
        raise ValueError("Unsupported news_daily_report type for HTML rendering")

    template_manager = TemplateManager()
    html = template_manager.render_report("NEWSDAILY", content_data)

    if html_file:
        os.makedirs(os.path.dirname(html_file), exist_ok=True)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
