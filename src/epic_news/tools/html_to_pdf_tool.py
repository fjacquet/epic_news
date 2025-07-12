import os
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from weasyprint import HTML


class HtmlToPdfToolSchema(BaseModel):
    """Input schema for HtmlToPdfTool."""

    html_file_path: str = Field(
        ..., description="The absolute path to the input HTML file that needs to be converted."
    )
    output_pdf_path: str = Field(
        ..., description="The absolute path where the generated PDF file will be saved."
    )


class HtmlToPdfTool(BaseTool):
    name: str = "HTML to PDF Converter"
    description: str = (
        "Converts a given HTML file to a PDF document using the WeasyPrint library. "
        "It returns the absolute path to the generated PDF file upon successful conversion, "
        "or an error message if the conversion fails or an issue occurs."
    )
    args_schema: type[BaseModel] = HtmlToPdfToolSchema
    html_file_path: Optional[str] = None
    output_pdf_path: Optional[str] = None

    def _run(
        self,
        html_file_path: str,
        output_pdf_path: str,
    ) -> str:
        self.html_file_path = html_file_path
        self.output_pdf_path = output_pdf_path
        try:
            if not os.path.isabs(html_file_path):
                return f"Error: HTML file path '{html_file_path}' must be an absolute path."
            if not os.path.isabs(output_pdf_path):
                return f"Error: Output PDF path '{output_pdf_path}' must be an absolute path."

            if not os.path.exists(html_file_path):
                return f"Error: HTML input file not found at '{html_file_path}'."

            # Ensure the output directory exists before writing the PDF
            output_dir = os.path.dirname(output_pdf_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            HTML(filename=html_file_path).write_pdf(output_pdf_path)

            if os.path.exists(output_pdf_path):
                return (
                    f"Successfully converted '{html_file_path}' to PDF. Output saved at '{output_pdf_path}'."
                )
            # This case should ideally not be reached if write_pdf doesn't error, but it's a safeguard.
            return f"Error: PDF generation failed for '{html_file_path}'. Output file not found at '{output_pdf_path}'."

        except FileNotFoundError:
            # This specific exception might be redundant due to the initial check, but good for safety.
            return f"Error: HTML input file not found at '{html_file_path}'."
        except Exception as e:
            # Catch any other exceptions during the WeasyPrint conversion process.
            return f"An error occurred during PDF conversion: {str(e)}"
