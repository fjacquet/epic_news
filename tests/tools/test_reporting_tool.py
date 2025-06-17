import os
import pytest
from pathlib import Path
from freezegun import freeze_time
from epic_news.tools.reporting_tool import ReportingTool

class TestReportingTool:
    
    def setup_method(self):
        """Set up the test environment before each test."""
        self.tool = ReportingTool()
        self.template_path = Path(__file__).parent.parent.parent / 'src' / 'epic_news' / 'templates' / 'professional_report_template.html'
        self.test_output_path = "test_output/test_report.html"

    def test_successful_report_generation(self):
        """Test that the tool generates a report successfully and saves it to the specified path."""
        report_title = "Test Report"
        report_body = "<p>This is the body of the test report.</p>"
        
        with freeze_time("2024-01-01 12:00:00"):
            result = self.tool._run(
                report_title=report_title, 
                report_body=report_body,
                output_file_path=self.test_output_path
            )

        # Check that the tool returns a success message
        assert " Professional HTML report successfully generated" in result
        assert self.test_output_path in result
        
        # Check that the file was actually created and contains expected content
        output_path = Path(self.test_output_path)
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "<h1><span class=\"emoji\">📰</span> Test Report</h1>" in content
        assert "<p>This is the body of the test report.</p>" in content
        assert "<em>Date of generation: 2024-01-01 12:00:00</em>" in content
        assert "{{ report_title }}" not in content
        assert "{{ report_body }}" not in content
        assert "{{ generation_date }}" not in content
        
        # Clean up
        output_path.unlink(missing_ok=True)
        output_path.parent.rmdir() if output_path.parent.exists() and not any(output_path.parent.iterdir()) else None

    def test_template_not_found_error(self):
        """Test that the tool returns an error when the template file is not found."""
        # Temporarily rename the template file to simulate it being missing
        original_path = self.template_path
        renamed_path = self.template_path.with_name("professional_report_template.html.bak")
        os.rename(original_path, renamed_path)

        try:
            report_title = "Test Report"
            report_body = "<p>This should fail.</p>"
            result = self.tool._run(
                report_title=report_title, 
                report_body=report_body,
                output_file_path=self.test_output_path
            )
            assert "Error: Template file not found" in result
        finally:
            # Rename the file back to its original name
            os.rename(renamed_path, original_path)

    def test_report_content_integrity(self):
        """Test that the HTML structure and key elements are present in the generated file."""
        report_title = "Content Integrity Check"
        report_body = "<ul><li>Item 1</li><li>Item 2</li></ul>"

        result = self.tool._run(
            report_title=report_title, 
            report_body=report_body,
            output_file_path=self.test_output_path
        )

        # Check that the tool returns a success message
        assert " Professional HTML report successfully generated" in result
        assert self.test_output_path in result
        
        # Check that the file was actually created and contains expected content
        output_path = Path(self.test_output_path)
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "<!DOCTYPE html>" in content
        assert "<html lang=\"en\">" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "<div class=\"container\">" in content
        assert "<div class=\"footer\">" in content
        assert "<ul><li>Item 1</li><li>Item 2</li></ul>" in content
        
        # Clean up
        output_path.unlink(missing_ok=True)
        output_path.parent.rmdir() if output_path.parent.exists() and not any(output_path.parent.iterdir()) else None
