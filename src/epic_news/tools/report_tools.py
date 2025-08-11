"""Factory for report-generation related tools.

This exposes:
    - RenderReportTool (standardized HTML rendering)
    - HtmlToPdfTool    (existing conversion utility)
"""

from __future__ import annotations

from epic_news.tools.render_report_tool import RenderReportTool

# HtmlToPdfTool already exists in the same package
try:
    from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
except ImportError:  # pragma: no cover
    # Fallback if dependencies for WeasyPrint are missing; still expose render tool.
    HtmlToPdfTool = None  # type: ignore


def get_report_tools() -> list:
    """Return list of report-related tools available in this environment."""
    tools: list = [RenderReportTool()]
    if HtmlToPdfTool is not None:
        tools.append(HtmlToPdfTool())
    return tools
