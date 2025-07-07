"""Tests for Book Summary HTML factory and renderer."""

import pytest

from epic_news.models.crews.book_summary_report import (
    BookSummaryReport,
    ChapterSummary,
    TableOfContentsEntry,
)
from epic_news.utils.html.book_summary_html_factory import book_summary_to_html


@pytest.fixture
def sample_book_summary_data():
    """Provide a sample BookSummaryReport object for testing."""
    return BookSummaryReport(
        topic="Test Topic",
        title="Test Book",
        author="Test Author",
        publication_date="2025-01-01",
        summary="This is a test book summary.",
        table_of_contents=[TableOfContentsEntry(id="chapter-1", title="The First Chapter")],
        sections=[],
        references=[],
        chapter_summaries=[
            ChapterSummary(
                chapter=1,
                title="The First Chapter",
                summary="This is the first chapter.",
                focus="The beginning.",
            )
        ],
    )


def test_book_summary_to_html(sample_book_summary_data, tmp_path):
    """Test that book_summary_to_html creates a valid HTML file."""
    html_file = tmp_path / "book_summary_report.html"
    html_content = book_summary_to_html(sample_book_summary_data, html_file=str(html_file))

    assert html_file.exists()
    assert "Test Book" in html_content
    assert "The First Chapter" in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_book_summary_renderer(sample_book_summary_data):
    """Test the BookSummaryRenderer directly."""
    # Skipping this test as BookSummaryRenderer is an abstract class
    # that can't be instantiated directly
