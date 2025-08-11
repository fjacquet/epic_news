"""Tests for News Daily HTML factory and renderer."""

import pytest

from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.utils.html.template_manager import TemplateManager


@pytest.fixture
def sample_news_daily_data():
    """Provide a sample NewsDailyReport object for testing."""
    return NewsDailyReport(
        summary="This is a test summary.",
        suisse_romande=[{"titre": "Test article in Suisse Romande"}],
    )


def test_daily_news_to_html(sample_news_daily_data, tmp_path):
    """Test that TemplateManager renders NEWSDAILY and we can write it to a file."""
    html_file = tmp_path / "daily_news_report.html"
    tm = TemplateManager()
    html_content = tm.render_report("NEWSDAILY", sample_news_daily_data.model_dump())
    html_file.write_text(html_content, encoding="utf-8")

    assert html_file.exists()
    assert "This is a test summary." in html_content
    assert "Test article in Suisse Romande" in html_content


@pytest.mark.skip(reason="Renderer is abstract class and can't be instantiated directly")
def test_news_daily_renderer(sample_news_daily_data):
    """Test the NewsDailyRenderer directly."""
    # Skipping this test as NewsDailyRenderer is an abstract class
    # that can't be instantiated directly
