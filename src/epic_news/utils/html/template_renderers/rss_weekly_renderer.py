"""
RSS Weekly Renderer

Renders weekly RSS feed content to structured HTML using BeautifulSoup.
Handles article lists, source information, and category organization.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class RssWeeklyRenderer(BaseRenderer):
    """Renders RSS weekly content with structured formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """
        Render RSS weekly data to HTML.

        Args:
            data: Dictionary containing RSS weekly data

        Returns:
            HTML string for RSS weekly content
        """
        # Create main container
        soup = self.create_soup("div")
        container = soup.find("div")
        container.attrs["class"] = ["rss-weekly-container"]  # type: ignore[union-attr]

        # Add header
        self._add_header(soup, container, data)

        # Add summary if available
        self._add_summary(soup, container, data)

        # Add articles by category
        self._add_articles_by_category(soup, container, data)

        # Add all articles if not organized by category
        if not data.get("categories"):
            self._add_articles(soup, container, data)

        # Add sources section if available
        self._add_sources(soup, container, data)


        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add RSS weekly header with title."""
        header = soup.new_tag("header")
        header.attrs["class"] = ["rss-header"]  # type: ignore[assignment]

        # Title
        title = data.get("title", "RSS Weekly")
        title_tag = soup.new_tag("h1")
        title_tag.attrs["class"] = ["rss-title"]  # type: ignore[assignment]
        title_tag.string = f"📰 {title}"
        header.append(title_tag)

        # Date if available
        date = data.get("date")
        if date:
            date_tag = soup.new_tag("p")
            date_tag.attrs["class"] = ["rss-date"]  # type: ignore[assignment]
            date_tag.string = date
            header.append(date_tag)

        container.append(header)

    def _add_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add summary section if available."""
        summary = data.get("summary", "")
        if not summary:
            return

        summary_div = soup.new_tag("div")
        summary_div.attrs["class"] = ["rss-summary"]  # type: ignore[assignment]

        summary_title = soup.new_tag("h2")
        summary_title.string = "📋 Résumé de la semaine"
        summary_div.append(summary_title)

        summary_p = soup.new_tag("p")
        summary_p.string = summary
        summary_div.append(summary_p)

        container.append(summary_div)

    def _add_articles_by_category(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add articles organized by category."""
        categories = data.get("categories", {})
        if not categories:
            return

        for category_name, articles in categories.items():
            category_section = soup.new_tag("section")
            category_section.attrs["class"] = ["rss-category"]  # type: ignore[assignment]

            # Category title
            category_title = soup.new_tag("h2")
            category_title.attrs["class"] = ["category-title"]  # type: ignore[assignment]
            category_title.string = category_name
            category_section.append(category_title)

            # Articles list
            articles_div = soup.new_tag("div")
            articles_div.attrs["class"] = ["category-articles"]  # type: ignore[assignment]

            for article in articles:
                article_card = self._create_article_card(soup, article)
                articles_div.append(article_card)

            category_section.append(articles_div)
            container.append(category_section)

    def _add_articles(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add all articles without category organization."""
        articles = data.get("articles", [])
        if not articles:
            return

        articles_section = soup.new_tag("section")
        articles_section.attrs["class"] = ["rss-articles"]  # type: ignore[assignment]

        articles_title = soup.new_tag("h2")
        articles_title.string = "📑 Articles"
        articles_section.append(articles_title)

        articles_grid = soup.new_tag("div")
        articles_grid.attrs["class"] = ["articles-grid"]  # type: ignore[assignment]

        for article in articles:
            article_card = self._create_article_card(soup, article)
            articles_grid.append(article_card)

        articles_section.append(articles_grid)
        container.append(articles_section)

    def _create_article_card(self, soup: BeautifulSoup, article: dict[str, Any]) -> Any:
        """Create an article card."""
        article_div = soup.new_tag("div")
        article_div.attrs["class"] = ["article-card"]  # type: ignore[assignment]

        # Article title with link if URL is available
        title = article.get("title", "")
        url = article.get("url", "")

        title_tag = soup.new_tag("h3")
        title_tag.attrs["class"] = ["article-title"]  # type: ignore[assignment]
        if url:
            link_tag = soup.new_tag("a", href=url)
            link_tag["target"] = "_blank"
            link_tag["rel"] = "noopener noreferrer"
            link_tag.string = title
            title_tag.append(link_tag)
        else:
            title_tag.string = title

        article_div.append(title_tag)

        # Source and date
        meta_div = soup.new_tag("div")
        meta_div.attrs["class"] = ["article-meta"]  # type: ignore[assignment]

        source = article.get("source", "")
        if source:
            source_span = soup.new_tag("span")
            source_span.attrs["class"] = ["article-source"]  # type: ignore[assignment]
            source_span.string = f"Source: {source}"
            meta_div.append(source_span)

        date = article.get("date", "")
        if date:
            if source:
                meta_div.append(soup.new_string(" | "))

            date_span = soup.new_tag("span")
            date_span.attrs["class"] = ["article-date"]  # type: ignore[assignment]
            date_span.string = date
            meta_div.append(date_span)

        if meta_div.contents:
            article_div.append(meta_div)

        # Description
        description = article.get("description", "")
        if description:
            desc_p = soup.new_tag("p")
            desc_p.attrs["class"] = ["article-description"]  # type: ignore[assignment]
            desc_p.string = description
            article_div.append(desc_p)

        # Article summary or content
        summary = article.get("summary", "")
        if summary:
            summary_div = soup.new_tag("div")
            summary_div.attrs["class"] = ["article-summary"]  # type: ignore[assignment]
            summary_p = soup.new_tag("p")
            summary_p.string = summary
            summary_div.append(summary_p)
            article_div.append(summary_div)

        return article_div

    def _add_sources(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add sources section if available."""
        sources = data.get("sources", [])
        if not sources:
            return

        sources_section = soup.new_tag("section")
        sources_section.attrs["class"] = ["rss-sources"]  # type: ignore[assignment]

        sources_title = soup.new_tag("h2")
        sources_title.string = "📚 Sources"
        sources_section.append(sources_title)

        sources_list = soup.new_tag("ul")
        sources_list.attrs["class"] = ["sources-list"]  # type: ignore[assignment]

        for source in sources:
            source_name = source.get("name", "")
            source_url = source.get("url", "")

            if source_name:
                source_item = soup.new_tag("li")
                if source_url:
                    link_tag = soup.new_tag("a", href=source_url)
                    link_tag["target"] = "_blank"
                    link_tag["rel"] = "noopener noreferrer"
                    link_tag.string = source_name
                    source_item.append(link_tag)
                else:
                    source_item.string = source_name

                sources_list.append(source_item)

        sources_section.append(sources_list)
        container.append(sources_section)
