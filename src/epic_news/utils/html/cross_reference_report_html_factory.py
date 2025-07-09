"""
This module provides a function to generate an HTML report from a CrossReferenceReport object.
"""

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.utils.html.template_manager import TemplateManager


def cross_reference_report_to_html(report: CrossReferenceReport, html_file: str) -> str:
    """
    Generates an HTML report from a CrossReferenceReport object.

    Args:
        report (CrossReferenceReport): The cross-reference report to be rendered.
        html_file (str): The path to the output HTML file.

    Returns:
        str: The generated HTML content.
    """
    template_manager = TemplateManager()
    html_content = template_manager.render_report(
        "CROSS_REFERENCE_REPORT",
        report.model_dump(),
    )
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_content
