"""Tests for Company News HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.company_news_report import ArticleItem, CompanyNewsReport
from epic_news.utils.html.company_news_html_factory import company_news_to_html
from epic_news.utils.html.template_renderers.company_news_renderer import (
    CompanyNewsRenderer,
)


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
    """Test that company_news_to_html creates a valid HTML file."""
    html_file = tmp_path / "company_news_report.html"
    html_content = company_news_to_html(
        sample_company_news_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Test Section" in html_content
    assert "Test Article" in html_content


def test_company_news_renderer(sample_company_news_data):
    """Test the CompanyNewsRenderer directly."""
    renderer = CompanyNewsRenderer()
    html = renderer.render(sample_company_news_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert "Synthèse stratégique 2025" in soup.find(
        "header", class_="company-news-header"
    ).text
    assert "Test Section" in soup.find("section", class_="company-news-section").text
    assert "Test Article" in soup.find("div", class_="company-news-article").text
