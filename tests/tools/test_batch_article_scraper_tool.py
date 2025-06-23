import json
import unittest
from unittest.mock import MagicMock

from src.epic_news.models.rss_models import Article, FeedWithArticles, RssFeeds
from src.epic_news.tools.batch_article_scraper_tool import BatchArticleScraperTool


class TestBatchArticleScraperTool(unittest.TestCase):
    """Test suite for BatchArticleScraperTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = BatchArticleScraperTool()

        # Create sample test data
        self.test_article1 = Article(
            title="Test Article 1", link="https://example.com/article1", published="2024-06-01T12:00:00Z"
        )

        self.test_article2 = Article(
            title="Test Article 2", link="https://example.com/article2", published="2024-06-02T12:00:00Z"
        )

        self.test_feed = FeedWithArticles(
            feed_url="https://example.com/feed.xml", articles=[self.test_article1, self.test_article2]
        )

        self.test_feeds = RssFeeds(feeds=[self.test_feed])

    def test_run_with_pydantic_model(self):
        """Test _run method with a Pydantic model input."""
        # Create a direct mock of the scrape_ninja_tool instance
        self.tool.scrape_ninja_tool = MagicMock()
        self.tool.scrape_ninja_tool._run.return_value = json.dumps({"content": "Test content"})

        # Run the tool with a Pydantic model
        result = self.tool._run(self.test_feeds)

        # Verify the result is a valid JSON string
        result_dict = json.loads(result)
        self.assertIsInstance(result_dict, dict)
        self.assertIn("feeds", result_dict)

        # Verify the ScrapeNinjaTool was called for each article
        self.assertEqual(self.tool.scrape_ninja_tool._run.call_count, 2)

    def test_run_with_dict(self):
        """Test _run method with a dictionary input."""
        # Create a direct mock of the scrape_ninja_tool instance
        self.tool.scrape_ninja_tool = MagicMock()
        self.tool.scrape_ninja_tool._run.return_value = json.dumps({"content": "Test content"})

        # Convert Pydantic model to dict
        if hasattr(self.test_feeds, "model_dump_json"):
            feeds_dict = json.loads(self.test_feeds.model_dump_json())
        else:
            feeds_dict = json.loads(self.test_feeds.json())

        # Run the tool with a dictionary
        result = self.tool._run(feeds_dict)

        # Verify the result is a valid JSON string
        result_dict = json.loads(result)
        self.assertIsInstance(result_dict, dict)
        self.assertIn("feeds", result_dict)

        # Verify the ScrapeNinjaTool was called for each article
        self.assertEqual(self.tool.scrape_ninja_tool._run.call_count, 2)

    def test_run_with_json_string(self):
        """Test _run method with a JSON string input."""
        # Create a direct mock of the scrape_ninja_tool instance
        self.tool.scrape_ninja_tool = MagicMock()
        self.tool.scrape_ninja_tool._run.return_value = json.dumps({"content": "Test content"})

        # Convert Pydantic model to JSON string
        if hasattr(self.test_feeds, "model_dump_json"):
            feeds_json = self.test_feeds.model_dump_json()
        else:
            feeds_json = self.test_feeds.json()

        # Run the tool with a JSON string
        result = self.tool._run(feeds_json)

        # Verify the result is a valid JSON string
        result_dict = json.loads(result)
        self.assertIsInstance(result_dict, dict)
        self.assertIn("feeds", result_dict)

        # Verify the ScrapeNinjaTool was called for each article
        self.assertEqual(self.tool.scrape_ninja_tool._run.call_count, 2)

    def test_error_handling(self):
        """Test error handling in _run method."""
        # Create a direct mock of the scrape_ninja_tool instance
        self.tool.scrape_ninja_tool = MagicMock()
        self.tool.scrape_ninja_tool._run.side_effect = Exception("Test error")

        # Run the tool
        result = self.tool._run(self.test_feeds)

        # Verify the result is a valid JSON string
        result_dict = json.loads(result)
        self.assertIsInstance(result_dict, dict)

        # Verify the content is still None (error case)
        feeds = result_dict.get("feeds", [])
        self.assertTrue(len(feeds) > 0)
        articles = feeds[0].get("articles", [])
        self.assertTrue(len(articles) > 0)
        self.assertIsNone(articles[0].get("content"))

    def test_invalid_input(self):
        """Test handling of invalid input types."""
        with self.assertRaises(TypeError):
            self.tool._run(123)  # Integer is not a valid input type

    def test_invalid_json(self):
        """Test handling of invalid JSON string."""
        with self.assertRaises(ValueError):
            self.tool._run("{invalid json}")


if __name__ == "__main__":
    unittest.main()
