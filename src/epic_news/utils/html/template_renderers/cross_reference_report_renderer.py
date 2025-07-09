"""
This module contains the renderer for the Cross-Reference Report.
"""

from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer


class CrossReferenceReportRenderer(BaseRenderer):
    """Renderer for the Cross-Reference Report."""

    def __init__(self):
        """Initializes the renderer."""
        super().__init__()

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

        html = f"<h1>Cross-Reference Intelligence Report: {report_target}</h1>"
        html += f"<h2>Executive Summary</h2><p>{executive_summary}</p>"

        html += "<h2>Detailed Findings</h2>"
        html += self._render_dict(detailed_findings)

        html += f"<h2>Confidence Assessment</h2><p>{confidence}</p>"

        html += "<h2>Information Gaps</h2>"
        if gaps:
            html += "<ul>"
            for gap in gaps:
                html += f"<li>{gap}</li>"
            html += "</ul>"
        else:
            html += "<p>No information gaps identified.</p>"

        return html

    def _render_dict(self, data: dict) -> str:
        """Renders a dictionary into an HTML list."""
        html = "<ul>"
        for key, value in data.items():
            html += f"<li><strong>{key.replace('_', ' ').title()}:</strong>"
            if isinstance(value, dict):
                html += self._render_dict(value)
            elif isinstance(value, list):
                html += self._render_list(value)
            else:
                html += f" {value}"
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
                html += str(item)
            html += "</li>"
        html += "</ul>"
        return html
