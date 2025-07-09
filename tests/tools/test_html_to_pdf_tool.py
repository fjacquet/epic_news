import os

from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.utils.directory_utils import ensure_output_directory


# Helper function to create a dummy HTML file for testing
def create_dummy_html(
    filepath, content="<html><body><h1>Test PDF Content</h1><p>This is a test.</p></body></html>"
):
    # Ensure the directory for the dummy HTML file exists
    ensure_output_directory(os.path.dirname(filepath))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


class TestHtmlToPdfTool:
    def test_successful_conversion(self, tmp_path):
        """Test successful conversion of an HTML file to PDF."""
        tool = HtmlToPdfTool()
        html_file_path = str(tmp_path / "test_input.html")
        pdf_file_path = str(tmp_path / "test_output.pdf")

        create_dummy_html(html_file_path)

        result = tool.run(html_file_path=html_file_path, output_pdf_path=pdf_file_path)

        assert "Successfully converted" in result, f"Conversion failed or message incorrect: {result}"
        assert os.path.exists(pdf_file_path), "PDF file was not created."
        assert str(pdf_file_path) in result, "Output PDF path not mentioned in success message."

    def test_input_html_not_found(self, tmp_path):
        """Test handling when the input HTML file does not exist."""
        tool = HtmlToPdfTool()
        non_existent_html_file = str(tmp_path / "non_existent.html")
        pdf_file_path = str(tmp_path / "output.pdf")

        result = tool.run(html_file_path=non_existent_html_file, output_pdf_path=pdf_file_path)

        assert "Error: HTML input file not found" in result, f"Incorrect error message: {result}"
        assert not os.path.exists(pdf_file_path), "PDF file should not be created if input is missing."

    def test_non_absolute_html_path(self, tmp_path):
        """Test that the tool returns an error for a non-absolute HTML file path."""
        tool = HtmlToPdfTool()
        # Create a dummy html file in tmp_path to ensure the error is about the path type, not file existence
        dummy_absolute_html_path = str(tmp_path / "input.html")
        create_dummy_html(dummy_absolute_html_path)

        relative_html_path = "input.html"  # This is a relative path
        absolute_pdf_path = str(tmp_path / "output.pdf")

        # The tool should check for absolute paths irrespective of CWD
        result = tool.run(html_file_path=relative_html_path, output_pdf_path=absolute_pdf_path)
        assert f"Error: HTML file path '{relative_html_path}' must be an absolute path." in result, (
            f"Incorrect error for relative HTML path: {result}"
        )

    def test_non_absolute_pdf_path(self, tmp_path):
        """Test that the tool returns an error for a non-absolute PDF output path."""
        tool = HtmlToPdfTool()
        absolute_html_path = str(tmp_path / "input.html")
        create_dummy_html(absolute_html_path)

        relative_pdf_path = "output.pdf"  # This is a relative path

        result = tool.run(html_file_path=absolute_html_path, output_pdf_path=relative_pdf_path)
        assert f"Error: Output PDF path '{relative_pdf_path}' must be an absolute path." in result, (
            f"Incorrect error for relative PDF path: {result}"
        )

    def test_output_directory_creation(self, tmp_path):
        """Test that the tool creates the output directory if it doesn't exist."""
        tool = HtmlToPdfTool()
        html_file_path = str(tmp_path / "input.html")
        create_dummy_html(html_file_path)

        # Define an output path where the directory doesn't exist yet
        output_dir = tmp_path / "new_output_dir_for_pdf"
        pdf_file_path = str(output_dir / "output.pdf")

        assert not os.path.exists(output_dir), "Output directory should not exist before tool run."

        result = tool.run(html_file_path=html_file_path, output_pdf_path=pdf_file_path)

        assert "Successfully converted" in result, f"Conversion failed: {result}"
        assert os.path.exists(output_dir), "Output directory was not created."
        assert os.path.exists(pdf_file_path), "PDF file was not created in the new directory."
