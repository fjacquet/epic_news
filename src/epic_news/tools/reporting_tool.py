from datetime import datetime
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from jinja2 import Environment, FileSystemLoader
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
            # Correctly locate the project root and then the templates directory
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            template_dir = project_root / 'templates'
            template_path = template_dir / 'report_template.html'

            if not template_path.exists():
                return f" Error: Template file not found. Tried to open: {template_path}"

            # Set up Jinja2 environment
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('report_template.html')

            # Create output directory if it doesn't exist
            output_path = Path(output_file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare context for the template
            context = {
                "title": report_title,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sections": [{"heading": "Summary", "content": report_body}],
                "images": [],
                "citations": []
            }

            # Render the template
            report_html = template.render(context)

            # Save the report to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_html)

            return f" Professional HTML report successfully generated and saved to {output_path}. The report includes proper styling, formatting, and structure."

        except Exception as e:
            return f" An unexpected error occurred while generating the report: {str(e)}"
        except Exception as e:
            return f" An unexpected error occurred while generating the report: {str(e)}"
