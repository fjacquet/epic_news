import json
from typing import Any

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, PrivateAttr

from epic_news.models.rss_models import RssFeeds
from epic_news.tools.scraper_factory import get_scraper


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
    # Private attribute to hold the selected scraper tool
    _scraper: Any = PrivateAttr(default_factory=get_scraper)

    # Compatibility alias for tests and external overrides
    @property
    def scrape_ninja_tool(self) -> Any:
        return self._scraper

    @scrape_ninja_tool.setter
    def scrape_ninja_tool(self, value: Any) -> None:
        self._scraper = value

    def _run(self, rss_feeds: list) -> str:
        """
        Scrapes the content for each article in the provided list of feeds.

        Args:
            rss_feeds: A list of feed dictionaries, where each dict conforms to FeedWithArticles.

        Returns:
            A JSON string representation of the updated RssFeeds object
        """
        try:
            # The input from the agent is a list of dicts. We validate it into our Pydantic model.
            feeds_obj = RssFeeds(rss_feeds=rss_feeds)
        except Exception as e:
            logger.error(f"Failed to create RssFeeds object from input: {e}")
            return json.dumps({"error": f"Invalid input format for rss_feeds: {e}"})

        # Process each feed and article
        for feed in feeds_obj.rss_feeds:
            logger.info(f"Processing feed: {feed.feed_url}")
            for article in feed.articles:
                url = article.link
                if not url:
                    logger.warning(f"No URL found for article: {article.title}")
                    continue

                try:
                    # Use the selected scraper to scrape the content
                    logger.info(f"Scraping content from: {url}")
                    scraped_data = self._scraper._run(url=str(url))
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

        return feeds_obj.model_dump_json()
