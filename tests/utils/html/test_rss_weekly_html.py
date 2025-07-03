"""Tests for RSS Weekly HTML factory and renderer."""

import pytest
from bs4 import BeautifulSoup

from epic_news.models.rss_weekly_models import FeedDigest, RssWeeklyReport
from epic_news.utils.html.rss_weekly_html_factory import rss_weekly_to_html
from epic_news.utils.html.template_renderers.rss_weekly_renderer import (
    RssWeeklyRenderer,
)


@pytest.fixture
def sample_rss_weekly_data():
    """Provide a sample RssWeeklyReport object for testing."""
    return RssWeeklyReport(
        title="Test RSS Report",
        summary="This is a test summary.",
        feeds=[FeedDigest(feed_url="http://test.com/rss", articles=[])],
    )


def test_rss_weekly_to_html(sample_rss_weekly_data, tmp_path):
    """Test that rss_weekly_to_html creates a valid HTML file."""
    html_file = tmp_path / "rss_weekly_report.html"
    html_content = rss_weekly_to_html(
        sample_rss_weekly_data, html_file=str(html_file)
    )

    assert html_file.exists()
    assert "Test RSS Report" in html_content
    assert "This is a test summary." in html_content


def test_rss_weekly_renderer(sample_rss_weekly_data):
    """Test the RssWeeklyRenderer directly."""
    renderer = RssWeeklyRenderer()
    html = renderer.render(sample_rss_weekly_data.model_dump())
    soup = BeautifulSoup(html, "html.parser")

    assert "Test RSS Report" in soup.find("h1", class_="rss-title").text
    assert "This is a test summary." in soup.find("div", class_="rss-summary").text
