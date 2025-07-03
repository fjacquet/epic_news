"""Tests for rss_weekly_converter."""

import pytest

from epic_news.models.rss_weekly_models import RssWeeklyReport
from epic_news.utils.rss_weekly_converter import (
    html_to_rss_weekly_json,
    html_to_rss_weekly_model,
    json_to_rss_weekly_model,
)


@pytest.fixture
def sample_html_content():
    """Provide sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test RSS Report</title>
    </head>
    <body>
        <h1>Test RSS Report</h1>
        <section class="executive-summary">
            <p>This is a test summary.</p>
        </section>
        <div class="feed-digest">
            <h3>🌐 Feed 1</h3>
            <a href="http://feed1.com/rss"></a>
            <article class="article-summary">
                <h4><a href="http://feed1.com/article1">Article 1</a></h4>
                <p class="published-date">📅 2025-01-01</p>
                <div class="summary"><p>Summary of article 1.</p></div>
            </article>
        </div>
        <div class="feed-digest">
            <h3>🌐 Feed 2</h3>
            <a href="http://feed2.com/rss"></a>
            <article class="article-summary">
                <h4><a href="http://feed2.com/article2">Article 2</a></h4>
                <p class="published-date">📅 2025-01-02</p>
                <div class="summary"><p>Summary of article 2.</p></div>
            </article>
        </div>
    </body>
    </html>
    """


def test_html_to_rss_weekly_json(sample_html_content):
    """Test converting HTML to RSS weekly JSON."""
    json_data = html_to_rss_weekly_json(sample_html_content)
    assert json_data["title"] == "Test RSS Report"
    assert json_data["summary"] == "This is a test summary."
    assert len(json_data["feeds"]) == 2
    assert json_data["feeds"][0]["feed_name"] == "Feed 1"
    assert len(json_data["feeds"][0]["articles"]) == 1
    assert json_data["feeds"][0]["articles"][0]["title"] == "Article 1"


def test_json_to_rss_weekly_model(sample_html_content):
    """Test converting JSON to RssWeeklyReport model."""
    json_data = html_to_rss_weekly_json(sample_html_content)
    model = json_to_rss_weekly_model(json_data)
    assert isinstance(model, RssWeeklyReport)
    assert model.title == "Test RSS Report"
    assert len(model.feeds) == 2


def test_html_to_rss_weekly_model(sample_html_content):
    """Test converting HTML directly to RssWeeklyReport model."""
    model = html_to_rss_weekly_model(sample_html_content)
    assert isinstance(model, RssWeeklyReport)
    assert model.title == "Test RSS Report"
    assert len(model.feeds) == 2
    assert model.feeds[0].articles[0].summary == "Summary of article 1."


def test_html_to_rss_weekly_json_error():
    """Test error handling for invalid HTML."""
    json_data = html_to_rss_weekly_json("invalid html")
    assert "Erreur de Conversion" in json_data["title"]
    assert "error" in json_data
