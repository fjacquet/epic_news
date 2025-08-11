"""Tests for Company News HTML factory and renderer."""

import pytest

from epic_news.models.crews.company_news_report import (
    ArticleItem,
    CompanyNewsReport,
)
from epic_news.utils.html.template_manager import TemplateManager


@pytest.fixture
def sample_company_news_data():
    """Provide a sample CompanyNewsReport object for testing."""
    return CompanyNewsReport(
        summary="This is a test summary.",
        sections=[
            {
                "titre": "Test Section",
                "contenu": [
                    ArticleItem(
                        article="Test Article",
                        date="2025-01-01",
                        source="Test Source",
                        citation="Test Citation",
                    )
                ],
            }
        ],
        notes="Test notes.",
    )


def test_company_news_to_html(sample_company_news_data, tmp_path):
    """Test that TemplateManager renders COMPANY_NEWS and we can write it to a file."""
    html_file = tmp_path / "company_news_report.html"
    tm = TemplateManager()
    html_content = tm.render_report("COMPANY_NEWS", sample_company_news_data.model_dump())
    html_file.write_text(html_content, encoding="utf-8")

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Test Section" in html_content
    assert "Test Article" in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_company_news_renderer(sample_company_news_data):
    """Test the CompanyNewsRenderer directly."""
    # Skipping this test as CompanyNewsRenderer is an abstract class
    # that can't be instantiated directly
