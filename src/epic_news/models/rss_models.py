from typing import List, Optional

from pydantic import BaseModel, Field


class RssFeedParserToolInput(BaseModel):
    """Input schema for the RssFeedParserTool."""

    feed_url: str = Field(..., description="The URL of the RSS feed to parse.")


class Article(BaseModel):
    """Represents a single article extracted from an RSS feed."""

    title: str
    link: str
    published: str
    content: Optional[str] = None


class FeedWithArticles(BaseModel):
    """Represents a single RSS feed and its list of articles."""

    feed_url: str
    articles: List[Article]


class RssFeeds(BaseModel):
    """A list of RSS feeds, each with its recent articles."""

    feeds: List[FeedWithArticles]
