"""
Factory function to convert a HolidayPlannerReport (or compatible dict) to HTML using TemplateManager.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.
"""

import os

from src.epic_news.models.holiday_planner_models import HolidayPlannerReport
from src.epic_news.utils.debug_utils import parse_crewai_output
from src.epic_news.utils.directory_utils import ensure_output_directory
from src.epic_news.utils.html.template_manager import TemplateManager


def holiday_planner_to_html(holiday_report, html_file=None):
    """
    Convert a HolidayPlannerReport to HTML using TemplateManager.

    Args:
        holiday_report: HolidayPlannerReport model, dict, or CrewOutput
        html_file: Optional path to write HTML file

    Returns:
        str: Generated HTML content
    """
    # Parse and validate the input data
    if hasattr(holiday_report, 'raw'):
        # CrewOutput object
        parsed_data = parse_crewai_output(holiday_report, HolidayPlannerReport)
    elif isinstance(holiday_report, dict):
        # Dictionary input
        parsed_data = HolidayPlannerReport.model_validate(holiday_report)
    elif isinstance(holiday_report, HolidayPlannerReport):
        # Already a Pydantic model
        parsed_data = holiday_report
    else:
        raise ValueError(f"Unsupported holiday_report type: {type(holiday_report)}")

    # Generate HTML using TemplateManager
    template_manager = TemplateManager()
    html_content = template_manager.render_report(
        selected_crew="HOLIDAY_PLANNER",
        content_data=parsed_data.to_template_data()
    )

    # Write to file if requested
    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    return html_content
