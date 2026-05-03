"""Tests for rss_weekly_converter — HTML → RssWeeklyReport conversion."""

from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.utils.rss_weekly_converter import (
    html_to_rss_weekly_json,
    html_to_rss_weekly_model,
    json_to_rss_weekly_model,
)

SAMPLE_HTML = """
<html>
  <body>
    <h1>Résumé Hebdomadaire</h1>
    <section class="executive-summary">
      <p>Top stories this week.</p>
    </section>
    <div class="feed-digest">
      <h3>🌐 Example Feed</h3>
      <a href="https://example.com/feed.xml">feed link</a>
      <article class="article-summary">
        <h4><a href="https://example.com/post-1">Post One</a></h4>
        <p class="published-date">📅 2026-05-01</p>
        <div class="summary"><p>First post body.</p></div>
      </article>
      <article class="article-summary">
        <h4>Post Two (no link)</h4>
        <p class="published-date">2026-05-02</p>
        <div class="summary"><p>Second post body.</p></div>
      </article>
    </div>
  </body>
</html>
"""


def test_html_to_rss_weekly_json_extracts_feed_and_articles():
    result = html_to_rss_weekly_json(SAMPLE_HTML)

    assert result["title"] == "Résumé Hebdomadaire"
    assert result["summary"] == "Top stories this week."
    assert result["total_feeds"] == 1
    assert result["total_articles"] == 2

    feed = result["feeds"][0]
    assert feed["feed_name"] == "Example Feed"
    assert feed["feed_url"] == "https://example.com/feed.xml"
    assert feed["total_articles"] == 2

    first, second = feed["articles"]
    assert first["title"] == "Post One"
    assert first["link"] == "https://example.com/post-1"
    assert first["published"] == "2026-05-01"
    assert first["summary"] == "First post body."
    assert second["title"] == "Post Two (no link)"
    assert second["link"] == ""
    assert second["published"] == "2026-05-02"


def test_html_to_rss_weekly_json_handles_empty_html():
    result = html_to_rss_weekly_json("<html><body></body></html>")
    assert result["total_feeds"] == 0
    assert result["total_articles"] == 0
    assert result["feeds"] == []


def test_json_to_rss_weekly_model_round_trip():
    json_data = html_to_rss_weekly_json(SAMPLE_HTML)
    model = json_to_rss_weekly_model(json_data)
    assert isinstance(model, RssWeeklyReport)
    assert model.title == "Résumé Hebdomadaire"


def test_html_to_rss_weekly_model_end_to_end():
    model = html_to_rss_weekly_model(SAMPLE_HTML)
    assert isinstance(model, RssWeeklyReport)
    assert model.title == "Résumé Hebdomadaire"
