import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
from crewai.tools import BaseTool
from dateutil import parser
from newspaper import Article as NewspaperArticle
from pydantic import BaseModel, Field

from epic_news.models.rss_models import Article, FeedWithArticles, RssFeeds
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

# Set up logging
logger = logging.getLogger(__name__)


class UnifiedRssToolInput(BaseModel):
    """Input schema for UnifiedRssTool."""
    opml_file_path: str = Field(
        ...,
        description="The absolute path to the OPML file containing RSS feed sources."
    )
    days_to_look_back: int = Field(
        7,
        description="Number of days to look back for articles (default: 7)."
    )
    output_file_path: str = Field(
        ...,
        description="The absolute path where the JSON output should be saved."
    )


class UnifiedRssTool(BaseTool):
    """
    A comprehensive tool that handles the entire RSS pipeline:
    1. Parse OPML file to extract RSS feed sources
    2. Fetch articles from each source
    3. Filter articles by date (last N days)
    4. Scrape content for each article
    5. Save results to a JSON file in RssFeeds format
    """
    name: str = "Unified RSS Tool"
    description: str = (
        "Processes an OPML file to extract RSS feeds, fetches recent articles, "
        "scrapes their content, and saves the results to a JSON file. "
        "The tool handles the entire pipeline from OPML parsing to content scraping."
    )
    args_schema: type[BaseModel] = UnifiedRssToolInput
    scrape_ninja_tool: ScrapeNinjaTool = ScrapeNinjaTool()

    def _run(
        self,
        opml_file_path: str,
        days_to_look_back: int = 7,
        output_file_path: str = None,
        invalid_sources_file_path: str = None
    ) -> str:
        # Set up logger
        logger = logging.getLogger(__name__)
        """
        Execute the entire RSS processing pipeline.
        
        Args:
            opml_file_path: Path to the OPML file containing RSS feed sources
            days_to_look_back: Number of days to look back for articles
            output_file_path: Path where the JSON output should be saved
            invalid_sources_file_path: Path where the invalid sources JSON output should be saved
            
        Returns:
            A string message indicating the result of the operation
        """
        try:
            # Track invalid sources
            invalid_sources = set()

            # Parse OPML file to get feed URLs
            feed_urls = self._parse_opml_file(opml_file_path)
            logger.info(f"Found {len(feed_urls)} feeds in OPML file")

            # Calculate cutoff date for filtering articles
            cutoff_date = datetime.now() - timedelta(days=days_to_look_back)

            # Process each feed to get articles
            all_feeds = []
            for feed_url in feed_urls:
                feed_articles = self._fetch_and_filter_articles(feed_url, cutoff_date, invalid_sources)
                if feed_articles:
                    all_feeds.append(FeedWithArticles(
                        feed_url=feed_url,
                        articles=feed_articles
                    ))
                else:
                    # Track feeds with no valid articles
                    invalid_sources.add(feed_url)

            if not all_feeds:
                return "No articles found within the specified date range."

            # Scrape content for each article
            for feed in all_feeds:
                for article in feed.articles:
                    try:
                        logger.info(f"Scraping content for: {article.link}")
                        article.content = self._scrape_article_content(article.link)
                    except Exception as e:
                        logger.error(f"Error scraping content for {article.link}: {str(e)}")

            # Save results to a JSON file
            rss_feeds = RssFeeds(feeds=all_feeds)

            if output_file_path:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

                # Write results to JSON file
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    json.dump(rss_feeds.model_dump(), f, ensure_ascii=False, indent=2)

                logger.info(f"Results saved to {output_file_path}")

            # Write invalid sources to a separate file
            if invalid_sources:
                invalid_sources_data = {
                    "invalid_sources": list(invalid_sources),
                    "timestamp": datetime.now().isoformat(),
                    "total_invalid": len(invalid_sources)
                }
                with open(invalid_sources_file_path, 'w', encoding='utf-8') as f:
                    json.dump(invalid_sources_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Found {len(invalid_sources)} invalid sources. Saved to {invalid_sources_file_path}")

            logger.info(f"Successfully processed {len(all_feeds)} feeds with {sum(len(feed.articles) for feed in all_feeds)} articles. Results saved to {output_file_path}")
            return f"Successfully processed {len(all_feeds)} feeds with {sum(len(feed.articles) for feed in all_feeds)} articles. Results saved to {output_file_path}"
        except Exception as e:
            error_msg = f"Error in UnifiedRssTool: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _parse_opml_file(self, opml_file_path: str) -> list[str]:
        """
        Parse the OPML file and extract all RSS feed URLs.
        
        Args:
            opml_file_path: Path to the OPML file
            
        Returns:
            A list of RSS feed URLs
        """
        try:
            tree = ET.parse(opml_file_path)
            root = tree.getroot()
            urls = []

            for outline in root.findall('.//outline[@xmlUrl]'):
                url = outline.get('xmlUrl')
                if url:
                    urls.append(url)

            return urls
        except ET.ParseError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error parsing XML file: {e}")
            raise
        except FileNotFoundError:
            logger = logging.getLogger(__name__)
            logger.error(f"File not found: {opml_file_path}")
            raise

    def _fetch_and_filter_articles(
        self,
        feed_url: str,
        cutoff_date: datetime,
        invalid_sources: set[str]
    ) -> list[Article]:
        """Fetch articles from a feed URL and filter by date."""
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Fetching and parsing feed: {feed_url}")
            feed = feedparser.parse(feed_url)

            # Check for HTTP error status
            if hasattr(feed, 'status'):
                try:
                    if int(feed.status) >= 400:
                        logger.error(f"HTTP error {feed.status} for feed: {feed_url}")
                        invalid_sources.add(feed_url)
                        return []
                except (TypeError, ValueError):
                    # Handle case where status is not comparable with integers
                    logger.warning(f"Invalid status value for feed: {feed_url}")

            # Check for bozo exception (feed parsing error)
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.error(f"Feed parsing error for {feed_url}: {getattr(feed, 'bozo_exception', 'Unknown error')}")
                invalid_sources.add(feed_url)
                return []

            if not feed.entries:
                logger.warning(f"No entries found for feed: {feed_url}")
                # Not marking as invalid - empty feed is not necessarily invalid
                return []

            logger.info(f"Found {len(feed.entries)} entries in feed: {feed_url}")

            articles = []
            skipped_count = 0
            no_date_count = 0

            for entry in feed.entries:
                # Extract publication date
                pub_date = None
                date_source = None

                # Try multiple date fields that might be available
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        # Handle both real tuples and mock objects
                        if hasattr(entry.published_parsed, '__getitem__'):
                            pub_date = datetime(*entry.published_parsed[:6])
                            date_source = 'published_parsed'
                    except (TypeError, ValueError):
                        pass

                if not pub_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        # Handle both real tuples and mock objects
                        if hasattr(entry.updated_parsed, '__getitem__'):
                            pub_date = datetime(*entry.updated_parsed[:6])
                            date_source = 'updated_parsed'
                    except (TypeError, ValueError):
                        pass

                # As a last resort, try to parse from string fields
                if not pub_date and hasattr(entry, 'published') and entry.published:
                    try:
                        pub_date = parser.parse(entry.published)
                        date_source = 'published string'
                    except (TypeError, ValueError):
                        pass

                if not pub_date and hasattr(entry, 'updated') and entry.updated:
                    try:
                        pub_date = parser.parse(entry.updated)
                        date_source = 'updated string'
                    except (TypeError, ValueError):
                        pass

                # Skip if no date
                if not pub_date:
                    no_date_count += 1
                    continue

                # Skip if article is older than cutoff
                if pub_date < cutoff_date:
                    skipped_count += 1
                    continue

                # Create Article object
                article = Article(
                    title=entry.title,
                    link=entry.link,
                    published=pub_date.isoformat(),
                    content=None  # Will be populated later
                )
                articles.append(article)

            if not articles:
                logger.warning(f"No recent articles found for feed: {feed_url} (skipped {skipped_count} old articles, {no_date_count} with no date)")
                # No longer marking feeds as invalid if they have no recent articles
            else:
                logger.info(f"Found {len(articles)} recent articles for feed: {feed_url} using {date_source} (skipped {skipped_count} old articles, {no_date_count} with no date)")

            return articles

        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {str(e)}")
            # Mark as invalid for any error during feed processing
            invalid_sources.add(feed_url)
            return []

    def _scrape_article_content(self, url: str) -> str | None:
        """
        Scrape the content of an article using either Newspaper3k or ScrapeNinjaTool.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            The article content as a string, or None if scraping failed
        """
        # First try with Newspaper3k (faster and doesn't require API key)
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()

            if article.text and len(article.text.strip()) > 100:  # Ensure we got meaningful content
                return article.text
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Newspaper3k failed for {url}: {str(e)}")

        # Fall back to ScrapeNinjaTool if Newspaper3k fails
        try:
            content = self.scrape_ninja_tool._run(url)
            if isinstance(content, dict) and 'content' in content:
                return content['content']
            return content
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"ScrapeNinjaTool failed for {url}: {str(e)}")
            return None


def get_default_paths():
    """Get default paths for OPML input and JSON output."""
    # Set default output paths if not provided
    project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))))
    output_dir = project_root / "output" / "rss_weekly"
    os.makedirs(output_dir, exist_ok=True)

    opml_path = str(project_root / "data" / "feedly.opml")
    output_file_path = str(output_dir / "content.json")
    invalid_sources_file_path = str(output_dir / "invalid_sources.json")

    return opml_path, output_file_path, invalid_sources_file_path


def main():
    """Command-line interface for UnifiedRssTool."""
    import argparse

    # Get default paths
    default_opml_path, default_output_path, default_invalid_sources_path = get_default_paths()

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Unified RSS Tool')
    parser.add_argument('--opml', type=str, default=default_opml_path,
                        help='Path to OPML file')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to look back')
    parser.add_argument('--output', type=str, default=default_output_path,
                        help='Output file path')
    parser.add_argument('--invalid-sources', type=str, default=default_invalid_sources_path,
                        help='Invalid sources output file path')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Set log level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the tool
    tool = UnifiedRssTool()
    result = tool._run(
        opml_file_path=args.opml,
        days_to_look_back=args.days,
        output_file_path=args.output,
        invalid_sources_file_path=args.invalid_sources
    )

    logger.info(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
