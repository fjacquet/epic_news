"""
RSS Feed Tool for reliable news source ingestion.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, ClassVar
from urllib.parse import urljoin, urlparse

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from epic_news.tools._json_utils import ensure_json_str
from epic_news.utils.http import http_get
from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


class RSSFeedInput(BaseModel):
    """Input schema for RSS Feed Tool."""

    region: str = Field(..., description="Region to get news for (suisse_romande, france, europe, world)")
    max_articles: int | None = Field(10, description="Maximum number of articles to retrieve")
    hours_back: int | None = Field(24, description="How many hours back to look for articles")


class RSSFeedTool(BaseTool):
    """
    RSS Feed tool for reliable news source ingestion.
    Fetches news directly from trusted RSS feeds for better link reliability.
    """

    name: str = "rss_feed_tool"
    description: str = (
        "Fetch news directly from trusted RSS feeds for reliable, verified sources. "
        "Provides working links from established news organizations. "
        "Supports regional filtering and recent article selection."
    )
    args_schema: type[BaseModel] = RSSFeedInput

    # Curated RSS feeds by region (tested and working URLs)
    RSS_SOURCES: ClassVar[dict[str, list[dict[str, str]]]] = {
        "suisse_romande": [
            {
                "name": "Le Temps - Tous articles",
                "url": "https://www.letemps.ch/articles.rss",
                "language": "fr",
            },
            {"name": "Le Temps - Suisse", "url": "https://www.letemps.ch/suisse.rss", "language": "fr"},
            {"name": "Le Temps - Monde", "url": "https://www.letemps.ch/monde.rss", "language": "fr"},
            {"name": "Le Temps - Économie", "url": "https://www.letemps.ch/economie.rss", "language": "fr"},
        ],
        "france": [
            {"name": "Le Monde - À la Une", "url": "https://www.lemonde.fr/rss/une.xml", "language": "fr"},
            {
                "name": "Le Monde - International",
                "url": "https://www.lemonde.fr/international/rss_full.xml",
                "language": "fr",
            },
            {
                "name": "Le Monde - Politique",
                "url": "https://www.lemonde.fr/politique/rss_full.xml",
                "language": "fr",
            },
            {
                "name": "Le Monde - Économie",
                "url": "https://www.lemonde.fr/economie/rss_full.xml",
                "language": "fr",
            },
            {
                "name": "Le Figaro - À la Une",
                "url": "https://www.lefigaro.fr/rss/figaro_actualites.xml",
                "language": "fr",
            },
            {
                "name": "Le Figaro - Flash Actu",
                "url": "https://www.lefigaro.fr/rss/figaro_flash-actu.xml",
                "language": "fr",
            },
            {
                "name": "Libération",
                "url": "https://www.liberation.fr/arc/outboundfeeds/rss-all/collection/accueil-une/?outputType=xml",
                "language": "fr",
            },
            {
                "name": "Les Échos",
                "url": "https://services.lesechos.fr/rss/les-echos-general.xml",
                "language": "fr",
            },
            {"name": "France 24", "url": "https://www.france24.com/fr/rss", "language": "fr"},
            {"name": "Le Point", "url": "https://www.lepoint.fr/rss.xml", "language": "fr"},
            {"name": "L'Obs", "url": "https://www.nouvelobs.com/rss", "language": "fr"},
            {
                "name": "Courrier International",
                "url": "https://www.courrierinternational.com/feed/all/rss.xml",
                "language": "fr",
            },
            {"name": "France Inter", "url": "https://www.radiofrance.fr/franceinter/rss", "language": "fr"},
            {
                "name": "France Culture",
                "url": "https://www.radiofrance.fr/franceculture/rss",
                "language": "fr",
            },
        ],
        "europe": [
            {
                "name": "BBC Europe",
                "url": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
                "language": "en",
            },
            {
                "name": "Reuters Europe",
                "url": "https://feeds.reuters.com/reuters/UKdomesticNews",
                "language": "en",
            },
            {"name": "Yahoo News", "url": "https://news.yahoo.com/rss/", "language": "en"},
        ],
        "world": [
            {
                "name": "BBC World News",
                "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
                "language": "en",
            },
            {
                "name": "Reuters Top News",
                "url": "https://feeds.reuters.com/reuters/topNews",
                "language": "en",
            },
            {"name": "Yahoo News International", "url": "https://news.yahoo.com/rss/", "language": "en"},
        ],
        "belgique": [{"name": "La Libre Belgique", "url": "https://www.lalibre.be/rss", "language": "fr"}],
        "canada": [{"name": "Radio-Canada", "url": "https://ici.radio-canada.ca/rss", "language": "fr"}],
    }

    def _run(self, region: str, max_articles: int = 10, hours_back: int = 24) -> str:
        """
        Fetch news from RSS feeds for the specified region.

        Args:
            region: Region to get news for
            max_articles: Maximum number of articles to retrieve
            hours_back: How many hours back to look for articles

        Returns:
            JSON string containing RSS feed results
        """
        try:
            # Get RSS sources for the region
            sources = self.RSS_SOURCES.get(region, [])
            if not sources:
                logger.warning(f"No RSS sources configured for region: {region}")
                return ensure_json_str(
                    {
                        "error": f"No RSS sources for region {region}",
                        "region": region,
                        "articles": [],
                        "success": False,
                    }
                )

            all_articles = []
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            for source in sources:
                try:
                    articles = self._fetch_rss_feed(source, cutoff_time)
                    all_articles.extend(articles)
                    logger.info(f"Fetched {len(articles)} articles from {source['name']}")
                except Exception as e:
                    logger.error(f"Error fetching from {source['name']}: {str(e)}")
                    continue

            # Sort by publication date (newest first) and limit
            all_articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
            limited_articles = all_articles[:max_articles]

            logger.info(f"RSS feed fetch completed: {len(limited_articles)} articles from {region}")

            return ensure_json_str(
                {
                    "region": region,
                    "source": "rss_feeds",
                    "articles": limited_articles,
                    "total_fetched": len(all_articles),
                    "total_returned": len(limited_articles),
                    "success": True,
                }
            )

        except Exception as e:
            logger.error(f"Error in RSS feed tool: {str(e)}")
            return ensure_json_str(
                {
                    "error": f"RSS feed fetch failed: {str(e)}",
                    "region": region,
                    "articles": [],
                    "success": False,
                }
            )

    def _fetch_rss_feed(self, source: dict[str, str], cutoff_time: datetime) -> list[dict[str, Any]]:
        """
        Fetch and parse a single RSS feed.

        Args:
            source: RSS source configuration
            cutoff_time: Only include articles newer than this

        Returns:
            List of article dictionaries
        """
        articles = []

        try:
            # Fetch RSS feed with timeout using resilient httpx client
            headers = {"User-Agent": "Mozilla/5.0 (compatible; EpicNews/1.0; RSS Reader)"}
            response = http_get(source["url"], headers=headers, timeout=10.0)

            # Parse XML
            root = ET.fromstring(response.content)

            # Handle different RSS formats
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items:
                try:
                    article = self._parse_rss_item(item, source)

                    # Filter by date if possible
                    if article.get("pub_date"):
                        try:
                            pub_date = datetime.fromisoformat(article["pub_date"].replace("Z", "+00:00"))
                            if pub_date < cutoff_time:
                                continue
                        except (ValueError, TypeError):
                            # If date parsing fails, include the article
                            pass

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parsing RSS item from {source['name']}: {str(e)}")
                    continue

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {source['url']}: {str(e)}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parsing error for {source['url']}: {str(e)}")
            raise

        return articles

    def _parse_rss_item(self, item: ET.Element, source: dict[str, str]) -> dict[str, Any]:
        """
        Parse a single RSS item into a standardized format.

        Args:
            item: XML element representing an RSS item
            source: Source configuration

        Returns:
            Standardized article dictionary
        """

        # Helper function to get text from element
        def get_text(element, tag_name: str, default: str = "") -> str:
            elem = element.find(tag_name) or element.find(f".//{tag_name}")
            if elem is not None and elem.text:
                return str(elem.text).strip()
            return default

        # Extract basic fields
        title = get_text(item, "title")
        link = get_text(item, "link")
        description = get_text(item, "description") or get_text(item, "summary")
        pub_date = get_text(item, "pubDate") or get_text(item, "published")

        # Handle Atom feeds
        if not link:
            link_elem = item.find(".//{http://www.w3.org/2005/Atom}link")
            if link_elem is not None:
                link = link_elem.get("href", "")

        # Clean up description (remove HTML tags)
        if description:
            import re

            description = re.sub(r"<[^>]+>", "", description)
            description = description.replace("&nbsp;", " ").strip()

        # Ensure absolute URL
        if link and not link.startswith("http"):
            base_url = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"
            link = urljoin(base_url, link)

        return {
            "title": title,
            "url": link,
            "description": description,
            "pub_date": pub_date,
            "source": source["name"],
            "language": source.get("language", "unknown"),
            "region": "rss_direct",
        }
