"""Pydantic models for RSS tools."""

from pydantic import BaseModel


class Article(BaseModel):
    """Represents a single article extracted from an RSS feed."""

    title: str
    link: str
    published: str
    summary: str | None = None
    content: str | None = None


class FeedWithArticles(BaseModel):
    """Represents a single RSS feed and its list of articles."""

    feed_url: str
    articles: list[Article]


class RssFeeds(BaseModel):
    """A list of RSS feeds, each with its recent articles."""

    rss_feeds: list[FeedWithArticles]
