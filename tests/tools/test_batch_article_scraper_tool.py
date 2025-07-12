import json

import pytest

from src.epic_news.models.rss_models import Article, FeedWithArticles, RssFeeds
from src.epic_news.tools.batch_article_scraper_tool import BatchArticleScraperTool


@pytest.fixture
def setup_tool_and_data(mocker):
    """Set up test fixtures."""
    tool = BatchArticleScraperTool()

    # Create sample test data
    test_article1 = Article(
        title="Test Article 1", link="https://example.com/article1", published="2024-06-01T12:00:00Z"
    )

    test_article2 = Article(
        title="Test Article 2", link="https://example.com/article2", published="2024-06-02T12:00:00Z"
    )

    test_feed = FeedWithArticles(
        feed_url="https://example.com/feed.xml", articles=[test_article1, test_article2]
    )

    test_feeds = RssFeeds(rss_feeds=[test_feed])

    # Mock the scrape_ninja_tool
    tool.scrape_ninja_tool = mocker.MagicMock()
    tool.scrape_ninja_tool._run.return_value = json.dumps({"content": "Test content"})

    # Return all test objects
    return {
        "tool": tool,
        "test_article1": test_article1,
        "test_article2": test_article2,
        "test_feed": test_feed,
        "test_feeds": test_feeds,
    }


def test_run_with_valid_input(setup_tool_and_data):
    """Test _run method with a valid list of feed dictionaries."""
    data = setup_tool_and_data
    tool = data["tool"]
    test_feeds = data["test_feeds"]

    # Convert Pydantic model to list of dicts
    feeds_list = json.loads(test_feeds.model_dump_json())["rss_feeds"]

    # Run the tool
    result = tool._run(rss_feeds=feeds_list)

    # Verify the result is a valid JSON string
    result_dict = json.loads(result)
    assert isinstance(result_dict, dict)
    assert "rss_feeds" in result_dict

    # Verify the ScrapeNinjaTool was called for each article
    assert tool.scrape_ninja_tool._run.call_count == 2
    # Verify content is scraped
    scraped_feeds = RssFeeds.model_validate(result_dict)
    assert scraped_feeds.rss_feeds[0].articles[0].content == "Test content"


def test_error_handling(setup_tool_and_data, mocker):
    """Test error handling in _run method."""
    data = setup_tool_and_data
    tool = data["tool"]
    test_feeds = data["test_feeds"]
    # Create a direct mock of the scrape_ninja_tool instance
    tool.scrape_ninja_tool = mocker.MagicMock()
    tool.scrape_ninja_tool._run.side_effect = Exception("Test error")

    # Convert Pydantic model to list of dicts
    feeds_list = json.loads(test_feeds.model_dump_json())["rss_feeds"]

    # Run the tool
    result = tool._run(rss_feeds=feeds_list)

    # Verify the result is a valid JSON string
    result_dict = json.loads(result)
    assert isinstance(result_dict, dict)

    # Verify the content is still None (error case)
    feeds = result_dict.get("rss_feeds", [])
    assert len(feeds) > 0
    articles = feeds[0].get("articles", [])
    assert len(articles) > 0
    assert articles[0].get("content") is None


def test_invalid_input_type(setup_tool_and_data):
    """Test handling of invalid input types."""
    data = setup_tool_and_data
    tool = data["tool"]
    result = tool._run(rss_feeds=123)  # Integer is not a valid input type
    result_dict = json.loads(result)
    assert "error" in result_dict
    assert "Invalid input format for rss_feeds" in result_dict["error"]


def test_invalid_list_format(setup_tool_and_data):
    """Test handling of a list with incorrect format."""
    data = setup_tool_and_data
    tool = data["tool"]
    result = tool._run(rss_feeds=[{"invalid_key": "value"}])
    result_dict = json.loads(result)
    assert "error" in result_dict
    assert "Invalid input format for rss_feeds" in result_dict["error"]

