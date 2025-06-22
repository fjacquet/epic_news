import json
from datetime import datetime, timedelta
from typing import Type

import feedparser
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.rss_models import RssFeedParserToolInput


class RssFeedParserTool(BaseTool):
    name: str = "rss_feed_parser"
    description: str = (
        "A tool for parsing an RSS feed and returning recent entries. "
        "It requires the RSS feed URL."
    )
    args_schema: Type[BaseModel] = RssFeedParserToolInput

    def _run(self, feed_url: str) -> str:
        """Run the RSS feed parser tool with robust error handling."""
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"[WARN] Feed at {feed_url} is not well-formed. Reason: {feed.get('bozo_exception', 'Unknown')}")

            if hasattr(feed, 'status') and feed.status >= 400:
                print(f"[ERROR] Feed at {feed_url} returned HTTP status {feed.status}")
                return f"Error: Failed to fetch RSS feed, status code {feed.status}"

            seven_days_ago = datetime.now() - timedelta(days=7)

            recent_entries = []
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_time = datetime(*entry.published_parsed[:6])
                        if published_time >= seven_days_ago:
                            recent_entries.append({
                                "title": entry.get("title", "No Title"),
                                "link": entry.get("link", ""),
                                "published": entry.get("published", "")
                            })
                    except (ValueError, TypeError):
                        print(f"[WARN] Could not parse date for an entry in {feed_url}. Entry title: {entry.get('title', 'N/A')}")
                        continue
                else:
                    print(f"[INFO] Skipping entry with no publication date in {feed_url}. Entry title: {entry.get('title', 'N/A')}")

            return json.dumps(recent_entries, default=str)
        except Exception as e:
            print(f"[ERROR] Failed to process feed {feed_url}. Reason: {e}")
            return f"Error parsing RSS feed: {e}"
