"""
Company News HTML Factory

Renders company news reports to HTML according to project html_rendering_pattern.md.
"""

import os

from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.template_manager import TemplateManager


def company_news_to_html(company_news_report, html_file=None):
    """
    Converts a validated CompanyNewsReport (Pydantic model or dict) to HTML using TemplateManager.
    Follows the HTML rendering pattern in docs/html_rendering_pattern.md.
    Args:
        company_news_report: CompanyNewsReport instance or dict
        html_file: Optional output file path
    Returns:
        str: Rendered HTML
    """
    # Normalize to dict if needed
    if hasattr(company_news_report, "model_dump"):
        content_data = company_news_report.model_dump()
    elif hasattr(company_news_report, "dict"):
        content_data = company_news_report.dict()
    elif isinstance(company_news_report, dict):
        content_data = company_news_report
    else:
        raise ValueError("Unsupported company_news_report type for HTML rendering")

    template_manager = TemplateManager()
    html = template_manager.render_report("COMPANY_NEWS", content_data)

    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
