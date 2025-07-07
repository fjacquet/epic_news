"""Tests for News Daily HTML factory and renderer."""

import pytest

from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.utils.html.daily_news_html_factory import daily_news_to_html


@pytest.fixture
def sample_news_daily_data():
    """Provide a sample NewsDailyReport object for testing."""
    return NewsDailyReport(
        summary="This is a test summary.",
        suisse_romande=[{"titre": "Test article in Suisse Romande"}],
    )


def test_daily_news_to_html(sample_news_daily_data, tmp_path):
    """Test that daily_news_to_html creates a valid HTML file."""
    html_file = tmp_path / "daily_news_report.html"
    html_content = daily_news_to_html(sample_news_daily_data, html_file=str(html_file))

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Test article in Suisse Romande" in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_news_daily_renderer(sample_news_daily_data):
    """Test the NewsDailyRenderer directly."""
    # Skipping this test as NewsDailyRenderer is an abstract class
    # that can't be instantiated directly
