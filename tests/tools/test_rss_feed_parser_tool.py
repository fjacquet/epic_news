import json
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from epic_news.tools.rss_feed_parser_tool import RssFeedParserTool


@pytest.fixture
def tool():
    """Fixture to provide an RssFeedParserTool instance."""
    return RssFeedParserTool()


@freeze_time("2024-01-08")
def test_rss_feed_parser_success(tool, mocker):
    """Test successful parsing and filtering of a recent RSS feed entry."""
    # Mock feedparser to return a feed with one recent entry and one old entry
    mock_feedparser = mocker.patch("epic_news.tools.rss_feed_parser_tool.feedparser")
    mock_feed = mocker.MagicMock()
    mock_feed.bozo = 0
    mock_feed.status = 200

    now = datetime.now()
    recent_entry_time = now - timedelta(days=3)
    old_entry_time = now - timedelta(days=10)

    def mock_get(key, default=None):
        if key == "title":
            return "Recent Article"
        if key == "link":
            return "http://fake-rss.com/recent"
        if key == "published":
            return "Mon, 05 Jan 2024 00:00:00 GMT"
        return default

    recent_entry = mocker.MagicMock(published_parsed=recent_entry_time.timetuple())
    recent_entry.get.side_effect = mock_get

    old_entry = mocker.MagicMock(published_parsed=old_entry_time.timetuple())

    mock_feed.entries = [recent_entry, old_entry]
    mock_feedparser.parse.return_value = mock_feed

    result = tool._run(feed_url="http://fake-rss.com/feed")

    # The tool should return only the recent entry as a JSON string
    expected_output = [
        {
            "title": "Recent Article",
            "link": "http://fake-rss.com/recent",
            "published": "Mon, 05 Jan 2024 00:00:00 GMT",
        }
    ]
    assert json.loads(result) == expected_output
    mock_feedparser.parse.assert_called_once_with("http://fake-rss.com/feed")


def test_rss_feed_parser_error(tool, mocker):
    """Test that the tool gracefully handles a parsing error."""
    mock_feedparser = mocker.patch("epic_news.tools.rss_feed_parser_tool.feedparser")
    mock_feedparser.parse.side_effect = Exception("Network Error")

    result = tool._run(feed_url="http://invalid-url.com/feed")

    assert "Error parsing RSS feed: Network Error" in result
