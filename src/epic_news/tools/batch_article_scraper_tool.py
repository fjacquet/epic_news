import json
import logging

from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.rss_models import Article, FeedWithArticles, RssFeeds
from src.epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

# Set up logging
logger = logging.getLogger(__name__)


class BatchArticleScraperTool(BaseTool):
    """
    A tool to scrape a batch of articles from RSS feeds.
    """

    name: str = "Batch Article Scraper"
    description: str = (
        "Accepts a RssFeeds object with a list of RSS feeds, iterates through each article, "
        "scrapes its content using ScrapeNinjaTool, and returns the updated RssFeeds object."
    )
    args_schema: type[BaseModel] = RssFeeds
    scrape_ninja_tool: ScrapeNinjaTool = ScrapeNinjaTool()

    def _run(self, input_data=None, **kwargs) -> str:
        # Use input_data if provided, otherwise extract from kwargs
        rss_feeds = input_data if input_data is not None else kwargs.get("rss_feeds", kwargs)
        """
        Scrapes the content for each article in the provided RssFeeds object.

        Args:
            rss_feeds: Can be a RssFeeds Pydantic model, a dictionary, or a JSON string

        Returns:
            A JSON string representation of the updated RssFeeds object
        """
        # Convert input to RssFeeds object if it's not already
        feeds_obj = self._ensure_rss_feeds_object(rss_feeds)

        # Process each feed and article
        for feed in feeds_obj.rss_feeds:
            logger.info(f"Processing feed: {feed.feed_url}")
            for article in feed.articles:
                url = article.link
                if not url:
                    logger.warning(f"No URL found for article: {article.title}")
                    continue

                try:
                    # Use the ScrapeNinjaTool to scrape the content
                    logger.info(f"Scraping content from: {url}")
                    scraped_data = self.scrape_ninja_tool._run(url=str(url))
                    scraped_json = json.loads(scraped_data)

                    # Extract content, handling potential errors
                    if "error" in scraped_json:
                        logger.error(f"Error scraping {url}: {scraped_json['error']}")
                        article.content = None
                    else:
                        article.content = scraped_json.get("content", scraped_data)
                        logger.info(f"Successfully scraped content for: {article.title}")

                except Exception as e:
                    logger.exception(f"An unexpected error occurred while scraping {url}: {e}")

        # Convert back to JSON string
        try:
            # Try the newer Pydantic v2 method first
            if hasattr(feeds_obj, "model_dump_json"):
                return feeds_obj.model_dump_json()
            # Fall back to the older method for Pydantic v1
            return feeds_obj.json()
        except Exception as e:
            logger.error(f"Error serializing RssFeeds object: {e}")
            # Last resort fallback
            return json.dumps(
                {
                    "feeds": [
                        {"feed_url": feed.feed_url, "articles": [article.dict() for article in feed.articles]}
                        for feed in feeds_obj.feeds
                    ]
                }
            )

    def _ensure_rss_feeds_object(self, input_data: RssFeeds | dict | str) -> RssFeeds:
        """
        Ensures that the input is converted to a RssFeeds object.

        Args:
            input_data: Can be a RssFeeds Pydantic model, a dictionary, or a JSON string

        Returns:
            A RssFeeds object
        """
        if isinstance(input_data, RssFeeds):
            return input_data

        # If it's a string, try to parse as JSON
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse input as JSON: {e}")
                raise ValueError(f"Invalid JSON input: {e}")

        # If it's a dict, convert to RssFeeds
        if isinstance(input_data, dict):
            try:
                # Try the newer Pydantic v2 method first
                if hasattr(RssFeeds, "model_validate"):
                    return RssFeeds.model_validate(input_data)
                # Fall back to the older method for Pydantic v1
                return RssFeeds.parse_obj(input_data)
            except Exception as e:
                logger.error(f"Failed to convert dict to RssFeeds: {e}")
                raise ValueError(f"Invalid RssFeeds format: {e}")

        raise TypeError(f"Expected RssFeeds, dict, or JSON string, got {type(input_data)}")


def test_batch_article_scraper():
    """
    Test function for BatchArticleScraperTool with sample data.
    """
    # Create test data
    feed1 = FeedWithArticles(
        feed_url="https://example.com/feed1.xml",
        articles=[
            Article(
                title="Test Article 1", link="https://example.com/article1", published="2024-06-01T12:00:00Z"
            )
        ],
    )

    feeds = RssFeeds(feeds=[feed1])

    # Create and test the tool
    tool = BatchArticleScraperTool()
    print("Testing BatchArticleScraperTool with sample data...")
    try:
        result = tool._run(feeds)
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    test_batch_article_scraper()
