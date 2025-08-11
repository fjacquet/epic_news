"""Tests for RSS Weekly HTML factory and renderer."""

import pytest

from epic_news.models.crews.rss_weekly_report import FeedDigest, RssWeeklyReport
from epic_news.utils.html.template_manager import TemplateManager


@pytest.fixture
def sample_rss_weekly_data():
    """Provide a sample RssWeeklyReport object for testing."""
    return RssWeeklyReport(
        title="Test RSS Report",
        summary="This is a test summary.",
        feeds=[FeedDigest(feed_url="http://test.com/rss", articles=[])],
    )


def test_rss_weekly_to_html(sample_rss_weekly_data, tmp_path):
    """Test that TemplateManager renders RSS_WEEKLY and we can write it to a file."""
    html_file = tmp_path / "rss_weekly_report.html"
    tm = TemplateManager()
    html_content = tm.render_report("RSS_WEEKLY", sample_rss_weekly_data)
    html_file.write_text(html_content, encoding="utf-8")

    assert html_file.exists()
    assert "Test RSS Report" in html_content
    assert "This is a test summary." in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_rss_weekly_renderer(sample_rss_weekly_data):
    """Test the RssWeeklyRenderer directly."""
    # Skipping this test as RssWeeklyRenderer is an abstract class
    # that can't be instantiated directly
