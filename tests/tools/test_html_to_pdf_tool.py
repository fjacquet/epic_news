import os

import pytest

from epic_news.tools import html_to_pdf_tool
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool, is_allowed_resource_url
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


@pytest.fixture
def output_root(tmp_path, monkeypatch):
    """Point the tool's allowed output/ root at a temp directory."""
    root = tmp_path / "output"
    root.mkdir()
    monkeypatch.setattr(html_to_pdf_tool, "_output_root", lambda: root.resolve())
    return root


@pytest.fixture
def mock_weasyprint_available(mocker, output_root):
    """Mock WeasyPrint as available for tests that need path validation."""
    mocker.patch("epic_news.tools.html_to_pdf_tool.WEASYPRINT_AVAILABLE", True)
    mock_html_class = mocker.MagicMock()
    mock_html_instance = mocker.MagicMock()
    mock_html_class.return_value = mock_html_instance

    # Make write_pdf create the output file
    def create_pdf(output_path):
        with open(output_path, "wb") as f:
            f.write(b"%PDF-1.4 mock pdf content")

    mock_html_instance.write_pdf.side_effect = create_pdf
    mocker.patch("epic_news.tools.html_to_pdf_tool.HTML", mock_html_class)
    mocker.patch("epic_news.tools.html_to_pdf_tool.OutputOnlyURLFetcher", mocker.MagicMock())
    return mock_html_class


class TestHtmlToPdfTool:
    def test_successful_conversion(self, output_root, mock_weasyprint_available):
        """Test successful conversion of an HTML file to PDF."""
        tool = HtmlToPdfTool()
        html_file_path = str(output_root / "test_input.html")
        pdf_file_path = str(output_root / "test_output.pdf")

        create_dummy_html(html_file_path)

        result = tool.run(html_file_path=html_file_path, output_pdf_path=pdf_file_path)

        assert "Successfully converted" in result, f"Conversion failed or message incorrect: {result}"
        assert os.path.exists(pdf_file_path), "PDF file was not created."
        assert str(pdf_file_path) in result, "Output PDF path not mentioned in success message."
        assert "url_fetcher" in mock_weasyprint_available.call_args.kwargs

    def test_input_html_not_found(self, output_root, mock_weasyprint_available):
        """Test handling when the input HTML file does not exist."""
        tool = HtmlToPdfTool()
        non_existent_html_file = str(output_root / "non_existent.html")
        pdf_file_path = str(output_root / "output.pdf")

        result = tool.run(html_file_path=non_existent_html_file, output_pdf_path=pdf_file_path)

        assert "Error: HTML input file not found" in result, f"Incorrect error message: {result}"
        assert not os.path.exists(pdf_file_path), "PDF file should not be created if input is missing."

    def test_non_absolute_html_path(self, output_root, mock_weasyprint_available):
        """Test that the tool returns an error for a non-absolute HTML file path."""
        tool = HtmlToPdfTool()
        # Create a dummy html file in tmp_path to ensure the error is about the path type, not file existence
        dummy_absolute_html_path = str(output_root / "input.html")
        create_dummy_html(dummy_absolute_html_path)

        relative_html_path = "input.html"  # This is a relative path
        absolute_pdf_path = str(output_root / "output.pdf")

        # The tool should check for absolute paths irrespective of CWD
        result = tool.run(html_file_path=relative_html_path, output_pdf_path=absolute_pdf_path)
        assert f"Error: HTML file path '{relative_html_path}' must be an absolute path." in result, (
            f"Incorrect error for relative HTML path: {result}"
        )

    def test_non_absolute_pdf_path(self, output_root, mock_weasyprint_available):
        """Test that the tool returns an error for a non-absolute PDF output path."""
        tool = HtmlToPdfTool()
        absolute_html_path = str(output_root / "input.html")
        create_dummy_html(absolute_html_path)

        relative_pdf_path = "output.pdf"  # This is a relative path

        result = tool.run(html_file_path=absolute_html_path, output_pdf_path=relative_pdf_path)
        assert f"Error: Output PDF path '{relative_pdf_path}' must be an absolute path." in result, (
            f"Incorrect error for relative PDF path: {result}"
        )

    def test_output_directory_creation(self, output_root, mock_weasyprint_available):
        """Test that the tool creates the output directory if it doesn't exist."""
        tool = HtmlToPdfTool()
        html_file_path = str(output_root / "input.html")
        create_dummy_html(html_file_path)

        # Define an output path where the directory doesn't exist yet
        output_dir = output_root / "new_output_dir_for_pdf"
        pdf_file_path = str(output_dir / "output.pdf")

        assert not os.path.exists(output_dir), "Output directory should not exist before tool run."

        result = tool.run(html_file_path=html_file_path, output_pdf_path=pdf_file_path)

        assert "Successfully converted" in result, f"Conversion failed: {result}"
        assert os.path.exists(output_dir), "Output directory was not created."
        assert os.path.exists(pdf_file_path), "PDF file was not created in the new directory."

    def test_html_outside_output_dir_is_rejected(self, tmp_path, output_root, mock_weasyprint_available):
        tool = HtmlToPdfTool()
        outside_html = str(tmp_path / "secret.html")
        create_dummy_html(outside_html)

        result = tool.run(html_file_path=outside_html, output_pdf_path=str(output_root / "out.pdf"))

        assert result.startswith("Error:")
        assert "output" in result
        mock_weasyprint_available.assert_not_called()

    def test_pdf_outside_output_dir_is_rejected(self, tmp_path, output_root, mock_weasyprint_available):
        tool = HtmlToPdfTool()
        html_file_path = str(output_root / "input.html")
        create_dummy_html(html_file_path)

        result = tool.run(html_file_path=html_file_path, output_pdf_path=str(tmp_path / "elsewhere.pdf"))

        assert result.startswith("Error:")
        assert not (tmp_path / "elsewhere.pdf").exists()
        mock_weasyprint_available.assert_not_called()

    def test_traversal_out_of_output_dir_is_rejected(self, output_root, mock_weasyprint_available):
        tool = HtmlToPdfTool()
        html_file_path = str(output_root / "input.html")
        create_dummy_html(html_file_path)

        result = tool.run(
            html_file_path=html_file_path, output_pdf_path=str(output_root / ".." / "escaped.pdf")
        )

        assert result.startswith("Error:")
        mock_weasyprint_available.assert_not_called()


class TestResourceUrlPolicy:
    def test_data_url_allowed(self, output_root):
        assert is_allowed_resource_url("data:image/png;base64,AAAA", output_root)

    def test_file_url_inside_output_allowed(self, output_root):
        assert is_allowed_resource_url((output_root / "img.png").as_uri(), output_root)

    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "http://169.254.169.254/latest/meta-data/",
            "https://example.com/style.css",
            "ftp://example.com/x",
        ],
    )
    def test_other_urls_blocked(self, output_root, url):
        assert not is_allowed_resource_url(url, output_root)

    def test_file_url_traversal_blocked(self, output_root):
        assert not is_allowed_resource_url((output_root).as_uri() + "/../secret.txt", output_root)


@pytest.mark.skipif(not html_to_pdf_tool.WEASYPRINT_AVAILABLE, reason="WeasyPrint system libraries missing")
class TestOutputOnlyURLFetcher:
    def test_blocks_file_outside_output(self, output_root):
        fetcher = html_to_pdf_tool.OutputOnlyURLFetcher(output_root)
        with pytest.raises(ValueError):
            fetcher.fetch("file:///etc/hosts")

    def test_blocks_http(self, output_root):
        fetcher = html_to_pdf_tool.OutputOnlyURLFetcher(output_root)
        with pytest.raises(ValueError):
            fetcher.fetch("http://127.0.0.1:1/")

    def test_reads_file_inside_output(self, output_root):
        (output_root / "ok.css").write_text("body{}", encoding="utf-8")
        fetcher = html_to_pdf_tool.OutputOnlyURLFetcher(output_root)
        response = fetcher.fetch((output_root / "ok.css").as_uri())
        try:
            assert response.read() == b"body{}"
        finally:
            response.close()
