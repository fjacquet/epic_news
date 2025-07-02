"""
Factory function to convert a MeetingPrepReport (or compatible dict) to HTML.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.

Uses the modular renderer pattern with MeetingPrepRenderer for better maintainability."""

import os

from epic_news.models.meeting_prep_report import MeetingPrepReport
from epic_news.utils.debug_utils import parse_crewai_output
from epic_news.utils.html.template_manager import TemplateManager


def meeting_prep_to_html(meeting_prep_report, html_file=None):
    """
    Converts a validated MeetingPrepReport (Pydantic model or dict) to HTML using MeetingPrepRenderer.
    If html_file is provided, writes the HTML to disk.

    Args:
        meeting_prep_report: A MeetingPrepReport model, dict, or CrewOutput containing meeting preparation data
        html_file: Optional path to write the HTML output to

    Returns:
        The HTML string
    """
    # Parse CrewAI output if needed (CrewOutput, dict, or model)
    if hasattr(meeting_prep_report, "raw"):
        # CrewOutput: parse raw JSON
        content_data = parse_crewai_output(meeting_prep_report, MeetingPrepReport)
    elif hasattr(meeting_prep_report, "model_dump"):
        # Pydantic model
        content_data = meeting_prep_report.to_template_data()
    elif isinstance(meeting_prep_report, dict):
        # If it's already a dict, use it directly
        content_data = meeting_prep_report
    else:
        raise ValueError("Unsupported meeting_prep_report type for HTML rendering")

    # Use TemplateManager for rendering with the universal template
    template_manager = TemplateManager()
    html = template_manager.render_report("MEETING_PREP", content_data)

    # Write to file if requested
    if html_file:
        os.makedirs(os.path.dirname(html_file), exist_ok=True)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

    return html
