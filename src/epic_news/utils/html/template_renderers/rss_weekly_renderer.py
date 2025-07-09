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
        container.attrs["class"] = ["rss-weekly-container"]

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

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add RSS weekly header with title."""
        header = soup.new_tag("header")
        header.attrs["class"] = ["rss-header"]

        # Title
        title = data.get("title", "RSS Weekly")
        title_tag = soup.new_tag("h1")
        title_tag.attrs["class"] = ["rss-title"]
        title_tag.string = f"📰 {title}"
        header.append(title_tag)

        # Date if available
        date = data.get("date")
        if date:
            date_tag = soup.new_tag("p")
            date_tag.attrs["class"] = ["rss-date"]
            date_tag.string = date
            header.append(date_tag)

        container.append(header)

    def _add_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add summary section if available."""
        summary = data.get("summary", "")
        if not summary:
            return

        summary_div = soup.new_tag("div")
        summary_div.attrs["class"] = ["rss-summary"]

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
            category_section.attrs["class"] = ["rss-category"]

            # Category title
            category_title = soup.new_tag("h2")
            category_title.attrs["class"] = ["category-title"]
            category_title.string = category_name
            category_section.append(category_title)

            # Articles list
            articles_div = soup.new_tag("div")
            articles_div.attrs["class"] = ["category-articles"]

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
        articles_section.attrs["class"] = ["rss-articles"]

        articles_title = soup.new_tag("h2")
        articles_title.string = "📑 Articles"
        articles_section.append(articles_title)

        articles_grid = soup.new_tag("div")
        articles_grid.attrs["class"] = ["articles-grid"]

        for article in articles:
            article_card = self._create_article_card(soup, article)
            articles_grid.append(article_card)

        articles_section.append(articles_grid)
        container.append(articles_section)

    def _create_article_card(self, soup: BeautifulSoup, article: dict[str, Any]) -> BeautifulSoup:
        """Create an article card."""
        article_div = soup.new_tag("div")
        article_div.attrs["class"] = ["article-card"]

        # Article title with link if URL is available
        title = article.get("title", "")
        url = article.get("url", "")

        title_tag = soup.new_tag("h3")
        title_tag.attrs["class"] = ["article-title"]
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
        meta_div.attrs["class"] = ["article-meta"]

        source = article.get("source", "")
        if source:
            source_span = soup.new_tag("span")
            source_span.attrs["class"] = ["article-source"]
            source_span.string = f"Source: {source}"
            meta_div.append(source_span)

        date = article.get("date", "")
        if date:
            if source:
                meta_div.append(soup.new_string(" | "))

            date_span = soup.new_tag("span")
            date_span.attrs["class"] = ["article-date"]
            date_span.string = date
            meta_div.append(date_span)

        if meta_div.contents:
            article_div.append(meta_div)

        # Description
        description = article.get("description", "")
        if description:
            desc_p = soup.new_tag("p")
            desc_p.attrs["class"] = ["article-description"]
            desc_p.string = description
            article_div.append(desc_p)

        # Article summary or content
        summary = article.get("summary", "")
        if summary:
            summary_div = soup.new_tag("div")
            summary_div.attrs["class"] = ["article-summary"]
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
        sources_section.attrs["class"] = ["rss-sources"]

        sources_title = soup.new_tag("h2")
        sources_title.string = "📚 Sources"
        sources_section.append(sources_title)

        sources_list = soup.new_tag("ul")
        sources_list.attrs["class"] = ["sources-list"]

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

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles to the RSS weekly content."""
        style = soup.new_tag("style")
        style.string = """
        .rss-weekly-container {
            max-width: 900px;
            margin: 0 auto;
            font-family: var(--body-font);
            color: var(--text-color);
        }
        .rss-header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--accent-color);
        }
        .rss-title {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .rss-date {
            color: var(--text-muted);
            margin-top: 0.25rem;
            font-style: italic;
        }
        .rss-summary {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .rss-summary h2 {
            color: var(--heading-color);
            margin-top: 0;
            margin-bottom: 1rem;
        }
        .rss-category, .rss-articles, .rss-sources {
            margin: 3rem 0;
        }
        .category-title, .rss-articles h2, .rss-sources h2 {
            color: var(--heading-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .category-articles, .articles-grid {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        .article-card {
            padding: 1.25rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .article-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .article-title {
            font-size: 1.2rem;
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: var(--heading-color);
        }
        .article-title a {
            color: inherit;
            text-decoration: none;
        }
        .article-title a:hover {
            color: var(--accent-color);
            text-decoration: underline;
        }
        .article-meta {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }
        .article-description {
            margin-bottom: 1rem;
        }
        .article-summary {
            font-size: 0.95rem;
            border-top: 1px solid var(--border-color);
            padding-top: 0.75rem;
        }
        .sources-list {
            list-style-type: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .sources-list li {
            background: var(--container-bg);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            border: 1px solid var(--border-color);
        }
        .sources-list a {
            color: var(--link-color);
            text-decoration: none;
        }
        .sources-list a:hover {
            text-decoration: underline;
        }
        """
        soup.append(style)
