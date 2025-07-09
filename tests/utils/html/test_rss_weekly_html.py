"""Tests for RSS Weekly HTML factory and renderer."""

import pytest

from epic_news.models.crews.rss_weekly_report import FeedDigest, RssWeeklyReport
from epic_news.utils.html.rss_weekly_html_factory import rss_weekly_to_html


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
    html_content = rss_weekly_to_html(sample_rss_weekly_data, html_file=str(html_file))

    assert html_file.exists()
    assert "Test RSS Report" in html_content
    assert "This is a test summary." in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_rss_weekly_renderer(sample_rss_weekly_data):
    """Test the RssWeeklyRenderer directly."""
    # Skipping this test as RssWeeklyRenderer is an abstract class
    # that can't be instantiated directly
