"""
Factory function to convert a SalesProspectingReport (or compatible dict) to HTML using TemplateManager.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.
"""

import os

from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.utils.debug_utils import parse_crewai_output
from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.template_manager import TemplateManager


def normalize_sales_prospecting_report_dict(report_dict):
    """
    Ensures all fields in the SalesProspectingReport are properly formatted for HTML rendering.
    """
    # Convert Pydantic model to dict if needed
    if hasattr(report_dict, "model_dump"):
        report_dict = report_dict.model_dump()
    elif hasattr(report_dict, "dict"):
        report_dict = report_dict.dict()

    # Provide defaults for missing fields to prevent rendering errors
    defaults = {
        "company_overview": "No company overview provided.",
        "key_contacts": [],
        "approach_strategy": "No approach strategy provided.",
        "remaining_information": "No additional information provided.",
    }

    for key, value in defaults.items():
        if key not in report_dict or not report_dict[key]:
            report_dict[key] = value

    return report_dict


def sales_prospecting_report_to_html(sales_prospecting_report, html_file=None):
    """
    Converts a validated SalesProspectingReport (Pydantic model or dict) to HTML using TemplateManager.
    If html_file is provided, writes the HTML to disk.
    Returns the HTML string.

    Args:
        sales_prospecting_report: A SalesProspectingReport Pydantic model, dict, or CrewOutput
        html_file: Optional path to write the HTML output

    Returns:
        The generated HTML as a string
    """
    # Parse CrewAI output if needed (CrewOutput, dict, or model)
    if hasattr(sales_prospecting_report, "raw"):
        # CrewOutput: parse raw JSON
        content_data = parse_crewai_output(sales_prospecting_report, SalesProspectingReport)
    elif hasattr(sales_prospecting_report, "model_dump"):
        # Pydantic model
        content_data = sales_prospecting_report.model_dump()
    elif isinstance(sales_prospecting_report, dict):
        content_data = sales_prospecting_report
    else:
        raise ValueError("Unsupported sales_prospecting_report type for HTML rendering")

    # Normalize for consistent rendering
    content_data = normalize_sales_prospecting_report_dict(content_data)

    template_manager = TemplateManager()
    html = template_manager.render_report("SALESPROSPECTING", content_data)

    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
    return html
