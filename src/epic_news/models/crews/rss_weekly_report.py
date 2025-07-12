"""Pydantic models for RSS Weekly digest reports."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ArticleSummary(BaseModel):
    """Represents a summarized article from an RSS feed."""

    title: str = Field(..., description="Original article title")
    link: str = Field(..., description="URL to the original article")
    published: str = Field(..., description="Publication date")
    summary: str = Field(..., description="Professional French summary of the article")
    source_feed: str = Field(..., description="Original RSS feed URL")


class FeedDigest(BaseModel):
    """Represents a digest of articles from a single RSS feed."""

    feed_url: str = Field(..., description="RSS feed URL")
    feed_name: Optional[str] = Field(None, description="Human-readable feed name")
    articles: list[ArticleSummary] = Field(
        default_factory=list, description="Summarized articles from this feed"
    )
    total_articles: int = Field(0, description="Total number of articles processed from this feed")


class RssWeeklyReport(BaseModel):
    """Complete RSS weekly digest report."""

    title: str = Field(default="Résumé Hebdomadaire des Flux RSS", description="Report title")
    generation_date: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    feeds: list[FeedDigest] = Field(default_factory=list, description="Digests from all RSS feeds")
    total_feeds: int = Field(0, description="Total number of RSS feeds processed")
    total_articles: int = Field(0, description="Total number of articles across all feeds")
    summary: Optional[str] = Field(None, description="Executive summary of the weekly digest")

    def model_post_init(self, __context) -> None:
        """Calculate totals after model initialization."""
        self.total_feeds = len(self.feeds)
        self.total_articles = sum(feed.total_articles for feed in self.feeds)

        # Update individual feed totals
        for feed in self.feeds:
            feed.total_articles = len(feed.articles)
