"""
Factory function to convert a NewsDailyReport (or compatible dict) to HTML using TemplateManager.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.
"""

import os

from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.utils.debug_utils import parse_crewai_output
from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.template_manager import TemplateManager


def normalize_news_daily_report_dict(report_dict):
    """
    Ensures all news section fields are lists of NewsItem-like dicts, converting fallback strings/lists.
    """
    import copy

    # Convert Pydantic model to dict if needed
    if hasattr(report_dict, "model_dump"):
        report_dict = report_dict.model_dump()
    elif hasattr(report_dict, "dict"):
        report_dict = report_dict.dict()

    fields = ["suisse_romande", "suisse", "france", "europe", "world", "wars", "economy"]
    normalized = copy.deepcopy(report_dict)
    for field in fields:
        val = normalized.get(field)
        if val is None:
            normalized[field] = []
        elif isinstance(val, str):
            # Fallback string: create one NewsItem dict with title only if not empty fallback, else empty list
            if val.strip() and not val.lower().startswith("aucune actualité"):
                normalized[field] = [
                    {"titre": val[:100] + "..." if len(val) > 100 else val, "source": "Fallback"}
                ]
            else:
                normalized[field] = []
        elif isinstance(val, list):
            news_items = []
            for item in val:
                if isinstance(item, str):
                    news_items.append(
                        {"titre": item[:100] + "..." if len(item) > 100 else item, "source": "Fallback"}
                    )
                elif isinstance(item, dict):
                    # Accept as-is
                    news_items.append(item)
                else:
                    # Unknown type, skip
                    continue
            normalized[field] = news_items
        # else: already a list of dicts or NewsItem
    return normalized


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

    # Normalize for fallback handling
    content_data = normalize_news_daily_report_dict(content_data)

    template_manager = TemplateManager()
    html = template_manager.render_report("NEWSDAILY", content_data)

    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
