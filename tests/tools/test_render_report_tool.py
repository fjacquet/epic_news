import os
from pathlib import Path

import pytest

from epic_news.models.report_models import (
    RenderReportToolSchema,
    ReportImage,
    ReportSection,
)
from epic_news.tools.render_report_tool import RenderReportTool

# Define the correct template directory for testing
TEMPLATE_DIR = Path("/Users/fjacquet/Projects/crews/epic_news/templates")


class TestRenderReportTool:
    """Tests for the RenderReportTool class."""

    @pytest.fixture(autouse=True)
    def mock_html_validation(self, monkeypatch):
        """Automatically mock HTML validation for all tests in this class."""
        # Define a mock validation function that always passes
        def mock_validate_html(html, raise_on_error=True):
            return True

        # Apply the mock to all tests
        monkeypatch.setattr("epic_news.utils.validate_html.validate_html", mock_validate_html)

    def test_render_report_tool_init(self, tmp_path):
        """Test RenderReportTool initialization with default and custom template paths."""
        # Initialize with the correct template directory
        tool = RenderReportTool(template_dir=TEMPLATE_DIR)
        assert tool._template_dir.exists(), "Template directory does not exist"
        assert tool._template_dir.is_dir(), "Template directory is not a directory"

        # Custom initialization with valid template directory
        custom_template_dir = tmp_path / "templates"
        os.makedirs(custom_template_dir, exist_ok=True)

        # Copy a template to the custom directory for testing
        with open(tool._template_dir / "report_template.html", "r") as src_file:
            template_content = src_file.read()

        with open(custom_template_dir / "report_template.html", "w") as dst_file:
            dst_file.write(template_content)

        custom_tool = RenderReportTool(template_dir=custom_template_dir)
        assert custom_tool._template_dir == custom_template_dir
        assert custom_tool._template_dir.exists()

    def test_render_report_tool_invalid_directory(self):
        """Test RenderReportTool initialization with invalid template directory."""
        with pytest.raises(FileNotFoundError):
            RenderReportTool(template_dir="/nonexistent/path")

    def test_render_basic_report(self):
        """Test rendering a basic report with required fields."""
        tool = RenderReportTool(template_dir=TEMPLATE_DIR)

        title = "Test Report"
        sections = [
            {"heading": "Introduction", "content": "<p>This is an introduction.</p>"},
            {"heading": "Conclusion", "content": "<p>This is a conclusion.</p>"}
        ]

        html_output = tool.run(title=title, sections=sections)

        # Basic validation
        assert title in html_output, "Title not included in HTML output"
        assert "Introduction" in html_output, "Section heading not in HTML output"
        assert "<p>This is an introduction.</p>" in html_output, "Section content not in HTML output"
        assert "<!DOCTYPE html>" in html_output, "Doctype missing from HTML output"
        assert "<meta name=\"viewport\"" in html_output, "Viewport meta tag missing from HTML"

    def test_render_with_images_and_citations(self):
        """Test rendering a report with images and citations."""
        tool = RenderReportTool(template_dir=TEMPLATE_DIR)

        title = "Report with Images and Citations"
        sections = [{"heading": "Content", "content": "<p>Some content here.</p>"}]
        images = [
            {"src": "https://example.com/image.jpg", "alt": "Example image", "caption": "Figure 1"}
        ]
        citations = [
            "Smith, J. (2022). Example citation.",
            "<a href='https://example.com'>Example link</a>"
        ]

        html_output = tool.run(
            title=title,
            sections=sections,
            images=images,
            citations=citations
        )

        assert "https://example.com/image.jpg" in html_output, "Image source not in HTML"
        assert "Example image" in html_output, "Image alt text not in HTML"
        assert "Figure 1" in html_output, "Image caption not in HTML"
        assert "Smith, J. (2022)" in html_output, "Citation not in HTML"
        # Check for the escaped version of the HTML tag (this is correct behavior to prevent XSS)
        assert "&lt;a href=&#39;https://example.com&#39;&gt;" in html_output, "Citation link not in HTML"

    def test_positional_args_handling(self):
        """Test handling of positional arguments."""
        tool = RenderReportTool(template_dir=TEMPLATE_DIR)

        title = "Positional Args Test"
        sections = [{"heading": "Section", "content": "<p>Content</p>"}]
        images = [{"src": "https://example.com/img.jpg", "alt": "Alt text"}]
        citations = ["Citation 1"]

        # Call with positional arguments
        html_output = tool.run(title, sections, images, citations)

        assert title in html_output, "Title not included when using positional args"
        assert "Section" in html_output, "Section heading not included when using positional args"
        assert "https://example.com/img.jpg" in html_output, "Image not included when using positional args"
        assert "Citation 1" in html_output, "Citation not included when using positional args"

    def test_pydantic_schema_validation(self):
        """Test that the Pydantic schema models work correctly."""
        # Test ReportSection
        section = ReportSection(heading="Test Heading", content="<p>Test content</p>")
        assert section.heading == "Test Heading"
        assert section.content == "<p>Test content</p>"

        # Test ReportImage
        image = ReportImage(src="https://example.com/test.jpg", alt="Test alt")
        assert image.src == "https://example.com/test.jpg"
        assert image.alt == "Test alt"
        assert image.caption is None  # Optional field

        # Test with caption
        image_with_caption = ReportImage(
            src="https://example.com/test2.jpg",
            alt="Test alt 2",
            caption="Test caption"
        )
        assert image_with_caption.caption == "Test caption"

        # Test RenderReportToolSchema
        schema = RenderReportToolSchema(
            title="Test Schema",
            sections=[section],
            images=[image, image_with_caption],
            citations=["Citation 1", "Citation 2"]
        )
        assert schema.title == "Test Schema"
        assert len(schema.sections) == 1
        assert len(schema.images) == 2
        assert len(schema.citations) == 2

    def test_html_validation(self, monkeypatch):
        """Test that HTML validation is called correctly."""
        tool = RenderReportTool(template_dir=TEMPLATE_DIR)

        # Mock the validate_html function
        validation_called = False

        def mock_validate_html(html):
            nonlocal validation_called
            validation_called = True
            assert "<!DOCTYPE html>" in html
            assert "<html" in html
            return True

        # Use monkeypatch to replace the real validator with our mock
        monkeypatch.setattr("epic_news.utils.validate_html.validate_html", mock_validate_html)

        # Render a report - this should call our mock validator
        tool.run(
            title="Validation Test",
            sections=[{"heading": "Test", "content": "<p>Content</p>"}]
        )

        assert validation_called, "HTML validation was not called during rendering"

    def test_async_rendering(self):
        """Test the async version of the tool."""
        import asyncio

        tool = RenderReportTool(template_dir=TEMPLATE_DIR)
        title = "Async Test"
        sections = [{"heading": "Async Section", "content": "<p>Async content</p>"}]

        # Run the async method in an event loop
        async def run_async_test():
            return await tool._arun(title=title, sections=sections)

        html_output = asyncio.run(run_async_test())

        assert title in html_output, "Title not included in async HTML output"
        assert "Async Section" in html_output, "Section heading not in async HTML output"
