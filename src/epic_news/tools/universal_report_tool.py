"""Universal HTML Report Generation Tool for CrewAI agents.

This tool provides a simple interface for agents to generate standardized HTML reports
using the universal template system, ensuring consistent styling across all crews.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from epic_news.utils.html.templates import render_universal_report


class UniversalReportInput(BaseModel):
    """Input schema for the Universal Report Tool."""

    title: str = Field(
        description="The title of the report (e.g., 'Recette de Tapenade Noire', 'Analyse Financière')"
    )
    content: str = Field(
        description="The HTML content body of the report. Should contain well-structured HTML with headings, paragraphs, lists, etc."
    )


class UniversalReportTool(BaseTool):
    """Tool for generating standardized HTML reports with consistent styling."""

    name: str = "universal_report_generator"
    description: str = (
        "Generate a professional HTML report with standardized styling. "
        "Use this tool to create consistent, well-formatted HTML reports. "
        "The content should be well-structured HTML (headings, paragraphs, lists, etc.)."
    )
    args_schema: type[BaseModel] = UniversalReportInput

    def _run(self, title: str, content: str) -> str:
        """Generate a standardized HTML report.

        Args:
            title: Report title
            content: HTML content body

        Returns:
            Complete HTML document with standardized styling
        """
        try:
            return render_universal_report(title=title, content=content)
        except Exception as e:
            return f"Error generating report: {str(e)}"



