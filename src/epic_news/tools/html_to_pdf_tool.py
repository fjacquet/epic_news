import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Try to import WeasyPrint, but make it optional
try:
    from weasyprint import HTML
    from weasyprint.urls import URLFetcher

    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    HTML = None
    URLFetcher = object
    _weasyprint_error = str(e)


def _output_root() -> Path:
    """The only directory the tool may read HTML/resources from or write PDFs to.

    Same root as ``render_and_write_html``: ``output/`` under the working directory.
    """
    return Path("output").resolve()


def _is_inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root)


def is_allowed_resource_url(url: str, root: Path) -> bool:
    """Allow only data: URLs and file: URLs that resolve inside ``root``."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme == "data":
        return True
    if scheme == "file" and parts.netloc in ("", "localhost"):
        return _is_inside(Path(url2pathname(parts.path)), root)
    return False


class OutputOnlyURLFetcher(URLFetcher):
    """WeasyPrint fetcher that blocks network access and files outside output/."""

    def __init__(self, root: Path, **kwargs):
        super().__init__(allowed_protocols={"data", "file"}, allow_redirects=False, **kwargs)
        self._root = root

    def fetch(self, url, headers=None):
        if not is_allowed_resource_url(url, self._root):
            raise ValueError(f"Blocked resource URL: {url}")
        return super().fetch(url, headers)


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
    html_file_path: str | None = None
    output_pdf_path: str | None = None

    def _run(
        self,
        html_file_path: str,
        output_pdf_path: str,
    ) -> str:
        # Check if WeasyPrint is available
        if not WEASYPRINT_AVAILABLE:
            return (
                "Error: WeasyPrint library is not available. "
                f"Original error: {_weasyprint_error}. "
                "Please install system dependencies: brew install glib pango cairo"
            )

        self.html_file_path = html_file_path
        self.output_pdf_path = output_pdf_path
        try:
            if not os.path.isabs(html_file_path):
                return f"Error: HTML file path '{html_file_path}' must be an absolute path."
            if not os.path.isabs(output_pdf_path):
                return f"Error: Output PDF path '{output_pdf_path}' must be an absolute path."

            root = _output_root()
            if not _is_inside(Path(html_file_path), root):
                return (
                    f"Error: HTML file path '{html_file_path}' must be inside the project output directory."
                )
            if not _is_inside(Path(output_pdf_path), root):
                return (
                    f"Error: Output PDF path '{output_pdf_path}' must be inside the project output directory."
                )

            if not os.path.exists(html_file_path):
                return f"Error: HTML input file not found at '{html_file_path}'."

            # Ensure the output directory exists before writing the PDF
            output_dir = os.path.dirname(output_pdf_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            HTML(filename=html_file_path, url_fetcher=OutputOnlyURLFetcher(root)).write_pdf(output_pdf_path)

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
