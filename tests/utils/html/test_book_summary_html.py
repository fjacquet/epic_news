"""Tests for Book Summary HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.book_summary_report import BookSummaryReport, ChapterSummary
from epic_news.utils.html.book_summary_html_factory import book_summary_to_html
from epic_news.utils.html.template_renderers.book_summary_renderer import (
    BookSummaryRenderer,
)


@pytest.fixture
def sample_book_summary_data():
    """Provide a sample BookSummaryReport object for testing."""
    return BookSummaryReport(
        topic="Test Topic",
        title="Test Book",
        author="Test Author",
        publication_date="2025-01-01",
        summary="This is a test book summary.",
        chapters=[
            ChapterSummary(
                chapter=1, title="The First Chapter", focus="The beginning."
            )
        ],
        table_of_contents=[],
        sections=[],
        references=[],
        chapter_summaries=[],
    )


def test_book_summary_to_html(sample_book_summary_data, tmp_path):
    """Test that book_summary_to_html creates a valid HTML file."""
    html_file = tmp_path / "book_summary_report.html"
    html_content = book_summary_to_html(
        sample_book_summary_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "Test Book" in html_content
    assert "The First Chapter" in html_content


def test_book_summary_renderer(sample_book_summary_data):
    """Test the BookSummaryRenderer directly."""
    renderer = BookSummaryRenderer()
    html = renderer.render(sample_book_summary_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("h2").text.strip() == "📖 Test Book"
    assert "Test Author" in soup.find("div", class_="book-meta").text
    assert "The First Chapter" in soup.find("div", class_="chapters-section").text
