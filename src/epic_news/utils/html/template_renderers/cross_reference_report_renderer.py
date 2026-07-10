"""
This module contains the renderer for the Cross-Reference Report.
"""

from html import escape
from typing import Any

from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer, _get_markdown_parser


class CrossReferenceReportRenderer(BaseRenderer):
    """Renderer for the Cross-Reference Report."""

    def __init__(self):
        """Initializes the renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict, **kwargs) -> str:
        """
        Renders the cross-reference report into a comprehensive HTML format.
        """
        if not isinstance(data, dict):
            return "<p>Invalid data format for Cross-Reference Report.</p>"

        report_target = data.get("target", "N/A")
        executive_summary = data.get("executive_summary", "No summary provided.")
        detailed_findings = data.get("detailed_findings", {})
        confidence = data.get("confidence_assessment", "N/A")
        gaps = data.get("information_gaps", [])

        html = f"<h1>Cross-Reference Intelligence Report: {self._prose(report_target)}</h1>"
        html += f"<h2>Executive Summary</h2><p>{self._prose(executive_summary)}</p>"

        html += "<h2>Detailed Findings</h2>"
        html += self._render_dict(detailed_findings)

        html += f"<h2>Confidence Assessment</h2><p>{self._prose(confidence)}</p>"

        html += "<h2>Information Gaps</h2>"
        if gaps:
            html += "<ul>"
            for gap in gaps:
                html += f"<li>{self._prose(gap)}</li>"
            html += "</ul>"
        else:
            html += "<p>No information gaps identified.</p>"

        return html

    @staticmethod
    def _prose(value: Any) -> str:
        """Render an agent-authored value as safe inline HTML.

        Strings are parsed as inline Markdown (bold, links, code); non-strings are
        stringified and escaped. The Markdown parser is configured with ``html=False``,
        so any literal HTML in the source text is escaped, not injected.
        """
        if isinstance(value, str):
            return str(_get_markdown_parser().renderInline(value))
        return escape(str(value))

    def _render_dict(self, data: dict) -> str:
        """Renders a dictionary into an HTML list."""
        html = "<ul>"
        for key, value in data.items():
            safe_key = escape(str(key).replace("_", " ").title())
            html += f"<li><strong>{safe_key}:</strong>"
            if isinstance(value, dict):
                html += self._render_dict(value)
            elif isinstance(value, list):
                html += self._render_list(value)
            else:
                html += f" {self._prose(value)}"
            html += "</li>"
        html += "</ul>"
        return html

    def _render_list(self, data: list) -> str:
        """Renders a list into an HTML list."""
        html = "<ul>"
        for item in data:
            html += "<li>"
            if isinstance(item, dict):
                html += self._render_dict(item)
            elif isinstance(item, list):
                html += self._render_list(item)
            else:
                html += self._prose(item)
            html += "</li>"
        html += "</ul>"
        return html
