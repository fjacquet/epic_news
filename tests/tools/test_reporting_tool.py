from pathlib import Path

from freezegun import freeze_time

from epic_news.tools.reporting_tool import ReportingTool


class TestReportingTool:
    def setup_method(self):
        """Set up the test environment before each test."""
        self.tool = ReportingTool()
        # Correctly locate the project root and then the templates directory
        project_root = Path(__file__).resolve().parent.parent.parent
        self.template_path = project_root / "templates" / "professional_report_template.html"
        self.test_output_path = "test_output/test_report.html"

    def teardown_method(self):
        """Clean up after each test."""
        output_path = Path(self.test_output_path)
        if output_path.exists():
            output_path.unlink()
        if output_path.parent.exists() and not any(output_path.parent.iterdir()):
            output_path.parent.rmdir()

    def test_successful_report_generation(self):
        """Test that the tool generates a report successfully and saves it to the specified path."""
        report_title = "Test Report"
        report_body = "<p>This is the body of the test report.</p>"

        with freeze_time("2024-01-01 12:00:00"):
            result = self.tool._run(
                report_title=report_title,
                report_body=report_body,
                output_file_path=self.test_output_path,
            )

        # Check that the tool returns a success message
        assert "Professional HTML report successfully generated" in result
        assert self.test_output_path in result

        # Check that the file was actually created and contains expected content
        output_path = Path(self.test_output_path)
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert '<h1><span class="emoji">📰</span> Test Report</h1>' in content
        assert "Date of generation: 2024-01-01" in content
        assert "<p>This is the body of the test report.</p>" in content
        assert "{{ title }}" not in content  # Check that placeholders are filled
        assert "{{ date }}" not in content
        assert "{{ section.content }}" not in content

    def test_template_not_found_error(self, mocker):
        """Test that the tool returns an error when the template file is not found."""
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_exists.return_value = False
        result = self.tool._run(
            report_title="Test Report",
            report_body="<p>This should fail.</p>",
            output_file_path=self.test_output_path,
        )
        assert "Error: Template file not found" in result

    def test_report_content_integrity(self):
        """Test that the HTML structure and key elements are present in the generated file."""
        report_title = "Content Integrity Check"
        report_body = "<ul><li>Item 1</li><li>Item 2</li></ul>"

        result = self.tool._run(
            report_title=report_title,
            report_body=report_body,
            output_file_path=self.test_output_path,
        )

        # Check that the tool returns a success message
        assert "Professional HTML report successfully generated" in result

        # Check that the file was actually created and contains expected content
        output_path = Path(self.test_output_path)
        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "<!DOCTYPE html>" in content
        assert '<html lang="en">' in content
        assert "<head>" in content
        assert "<body>" in content
        assert '<div class="footer">' in content
        assert "<ul><li>Item 1</li><li>Item 2</li></ul>" in content

        # Clean up
        output_path.unlink(missing_ok=True)
        output_path.parent.rmdir() if output_path.parent.exists() and not any(
            output_path.parent.iterdir()
        ) else None
