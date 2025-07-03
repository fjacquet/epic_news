"""Tests for Saint HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.saint_data import SaintData
from epic_news.utils.html.saint_html_factory import saint_to_html
from epic_news.utils.html.template_renderers.saint_renderer import SaintRenderer


@pytest.fixture
def sample_saint_data():
    """Provide a sample SaintData object for testing."""
    return SaintData(
        saint_name="Saint Test",
        feast_date="January 1",
        biography="A saint for testing purposes.",
        significance="Ensures code quality.",
        miracles="No miracles recorded.",
        swiss_connection="None",
        prayer_reflection="A prayer for good tests.",
    )


def test_saint_to_html(sample_saint_data, tmp_path):
    """Test that saint_to_html creates a valid HTML file."""
    html_file = tmp_path / "saint_report.html"
    html_content = saint_to_html(sample_saint_data, html_file=str(html_file))

    assert html_file.exists()
    assert "Saint Test" in html_content
    assert "Patron of Tests" in html_content
    assert "A saint for testing purposes." in html_content


def test_saint_renderer(sample_saint_data):
    """Test the SaintRenderer directly."""
    renderer = SaintRenderer()
    html = renderer.render(sample_saint_data.to_template_data())
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find("h2").text == "✨ Saint Test"
    assert "Patron of Tests" in soup.find("p", class_="saint-title").text
    assert "A saint for testing purposes." in soup.find("div", class_="saint-biography").text
    assert "testing, quality assurance" in soup.find("div", class_="feast-details").text
