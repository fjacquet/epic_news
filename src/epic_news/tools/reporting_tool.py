from datetime import datetime
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReportingToolInput(BaseModel):
    """Input for the ReportingTool."""

    report_title: str = Field(..., description="The title for the HTML report.")
    report_body: str = Field(..., description="The body content of the report, in HTML format.")
    output_file_path: str = Field(..., description="The file path where the HTML report should be saved.")


class ReportingTool(BaseTool):
    name: str = "Professional Report Generator"
    description: str = (
        "Generates a professional HTML report from a title and body content using a standardized template."
    )
    args_schema: type[BaseModel] = ReportingToolInput

    def _run(self, report_title: str, report_body: str, output_file_path: str) -> str:
        """
        Generates a professional HTML report from a template and saves it to a file.

        This function reads a standard HTML template, populates it with a title,
        generation date, and the main report body content, saves it to a file,
        and returns a success message.

        Args:
            report_title: The title of the report.
            report_body: The main content of the report in HTML format.
            output_file_path: The file path where the HTML report should be saved.

        Returns:
            A success message indicating the report was generated and saved.
        """
        try:
            # Locate the template file
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            template_path = project_root / "templates" / "professional_report_template.html"

            if not template_path.exists():
                return f"❌ Error: Template file not found at {template_path}"

            # Read template content
            template_content = template_path.read_text(encoding="utf-8")

            # Simple string replacement (no Jinja2)
            report_html = template_content.replace("{{ report_title }}", report_title)
            report_html = report_html.replace("{{ generation_date }}", datetime.now().strftime("%Y-%m-%d"))
            report_html = report_html.replace("{{ report_body }}", report_body)

            # Create output directory and save file
            output_path = Path(output_file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_html, encoding="utf-8")

            return f"✅ Professional HTML report successfully generated and saved to {output_path}"

        except Exception as e:
            return f"❌ Error generating report: {str(e)}"
