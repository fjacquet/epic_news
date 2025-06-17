from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReportingToolInput(BaseModel):
    """Input for the ReportingTool."""
    report_title: str = Field(..., description="The title for the HTML report.")
    report_body: str = Field(..., description="The body content of the report, in HTML format.")
    output_file_path: str = Field(..., description="The file path where the HTML report should be saved.")

class ReportingTool(BaseTool):
    name: str = "Professional Report Generator"
    description: str = "Generates a professional HTML report from a title and body content using a standardized template."
    args_schema: Type[BaseModel] = ReportingToolInput

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
            current_dir = Path(__file__).parent
            template_path = current_dir.parent / 'templates' / 'professional_report_template.html'
            
            # Create output directory if it doesn't exist
            output_path = Path(output_file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            report_html = template_content.replace('{{ report_title }}', report_title)
            report_html = report_html.replace('{{ generation_date }}', generation_date)
            report_html = report_html.replace('{{ report_body }}', report_body)

            # Save the report to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_html)

            return f" Professional HTML report successfully generated and saved to {output_path}. The report includes proper styling, formatting, and structure."

        except FileNotFoundError:
            return f" Error: Template file not found. The template 'professional_report_template.html' was not found at the expected location."
        except Exception as e:
            return f" An unexpected error occurred while generating the report: {str(e)}"
