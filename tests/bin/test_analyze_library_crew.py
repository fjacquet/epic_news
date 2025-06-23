import logging
from pathlib import Path

import pytest

from epic_news.bin.analyze_library_crew import (
    analyze_dashboard_directories,
    analyze_file_paths,
    analyze_html_file,
    analyze_templates_directory,
)


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Create a mock project root directory."""
    (tmp_path / "output" / "library").mkdir(parents=True)
    (tmp_path / "output" / "dashboard_data").mkdir(parents=True)
    (tmp_path / "output" / "dashboards").mkdir(parents=True)
    (tmp_path / "templates").mkdir(parents=True)
    return tmp_path


def test_analyze_html_file_valid(caplog, mock_project_root):
    """Test analysis of a valid HTML file."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Art of War</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body class="epic-news-report">
        <div class="report-container">
            <header class="report-header"><h1>Sun Tzu's Art of War</h1></header>
            <section class="report-section"><h2>Chapter 1</h2><p>Details...</p></section>
            <section class="report-section"><h3>Subsection</h3><p>More details...</p></section>
        </div>
    </body>
    </html>
    """
    html_path = mock_project_root / "output" / "library" / "book_summary.html"
    html_path.write_text(html_content, encoding="utf-8")

    with caplog.at_level(logging.INFO):
        analyze_html_file(str(html_path))

    assert "Template usage looks good: 100.0%" in caplog.text
    assert "Word count: 12" in caplog.text
    assert "Number of headings: 3" in caplog.text
    assert "Content does not appear to be about 'Art of War' by Sun Tzu" not in caplog.text


def test_analyze_html_file_with_issues(caplog, mock_project_root):
    """Test analysis of an HTML file with multiple issues."""
    html_content = """<html><body><h1>A Topic</h1><p>Some text.</p></body></html>"""
    html_path = mock_project_root / "output" / "library" / "book_summary.html"
    html_path.write_text(html_content, encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        analyze_html_file(str(html_path))

    assert "Missing DOCTYPE declaration" in caplog.text
    assert "Missing <head> element" in caplog.text
    assert "No styling found" in caplog.text
    assert "Content does not appear to be about 'Art of War' by Sun Tzu" in caplog.text
    assert "Few sections found, structure may be minimal (1 headings)" in caplog.text
    assert "Low template usage indicator: 0.0%" in caplog.text


def test_analyze_html_file_not_found(caplog):
    """Test analysis when HTML file does not exist."""
    with caplog.at_level(logging.ERROR):
        analyze_html_file("non_existent_file.html")
    assert "HTML file not found: non_existent_file.html" in caplog.text


def test_analyze_file_paths_correct(caplog, monkeypatch, mock_project_root):
    """Test file path analysis when paths are correct."""
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", mock_project_root)
    (mock_project_root / "output" / "library" / "book.pdf").touch()

    with caplog.at_level(logging.INFO):
        analyze_file_paths()

    assert "Found incorrect nested path" not in caplog.text
    assert "Files in correct output directory: ['book.pdf']" in caplog.text


def test_analyze_file_paths_incorrect(caplog, monkeypatch, mock_project_root):
    """Test file path analysis when an incorrect nested path exists."""
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", mock_project_root)
    incorrect_path = (
        mock_project_root / "Users" / "fjacquet" / "Projects" / "crews" / "epic_news" / "output" / "library"
    )
    incorrect_path.mkdir(parents=True)
    (incorrect_path / "book_summary.pdf").touch()

    with caplog.at_level(logging.WARNING):
        analyze_file_paths()

    assert f"Found incorrect nested path: {incorrect_path}" in caplog.text
    assert "PDF file exists in the incorrect location" in caplog.text


def test_analyze_templates_directory_valid(caplog, monkeypatch, mock_project_root):
    """Test template directory analysis when the template exists."""
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", mock_project_root)
    (mock_project_root / "templates" / "report_template.html").touch()

    with caplog.at_level(logging.INFO):
        analyze_templates_directory()

    assert "Templates available: ['report_template.html']" in caplog.text
    assert "Report template exists" in caplog.text


def test_analyze_templates_directory_missing(caplog, monkeypatch, mock_project_root):
    """Test template directory analysis when the template is missing."""
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", mock_project_root)

    with caplog.at_level(logging.WARNING):
        analyze_templates_directory()

    assert "Report template not found" in caplog.text


def test_analyze_dashboard_directories_valid(caplog, monkeypatch, mock_project_root):
    """Test dashboard directory analysis when directories exist."""
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", mock_project_root)
    (mock_project_root / "output" / "dashboard_data" / "data.json").touch()
    (mock_project_root / "output" / "dashboards" / "dashboard.html").touch()

    with caplog.at_level(logging.INFO):
        analyze_dashboard_directories()

    assert "Dashboard data files: ['data.json']" in caplog.text
    assert "Dashboard files: ['dashboard.html']" in caplog.text


def test_analyze_dashboard_directories_missing(caplog, monkeypatch, tmp_path):
    """Test dashboard directory analysis when directories are missing."""
    # Use a clean tmp_path without the full mock structure
    monkeypatch.setattr("epic_news.bin.analyze_library_crew.project_root", tmp_path)

    with caplog.at_level(logging.WARNING):
        analyze_dashboard_directories()

    assert f"Dashboard data directory doesn't exist: {tmp_path / 'output/dashboard_data'}" in caplog.text
    assert f"Dashboards directory doesn't exist: {tmp_path / 'output/dashboards'}" in caplog.text
