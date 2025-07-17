"""
News Daily Renderer

Renders news daily reports with structured sections and categories.
Handles multiple news categories with proper formatting and emojis.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class NewsDailyRenderer(BaseRenderer):
    """Renders news daily content with structured sections."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render news daily data to HTML.

        Args:
            data: Dictionary containing news daily data

        Returns:
            HTML string for news daily content
        """
        # Create main container
        soup = self.create_soup("div", class_="news-daily-report")
        container = soup.find("div")

        # Add header with executive summary
        self._add_header(soup, container, data)

        # Add news sections
        self._add_news_sections(soup, container, data)

        # Add methodology if available
        self._add_methodology(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add header with executive summary."""
        header_div = soup.new_tag("div")
        header_div.attrs["class"] = ["news-header"]

        title_tag = soup.new_tag("h1")
        title_tag.string = "📰 Actualités du Jour"
        header_div.append(title_tag)

        # Add executive summary if available
        summary = data.get("summary", "")
        if summary:
            summary_div = soup.new_tag("div")
            summary_div.attrs["class"] = ["executive-summary"]
            summary_title = soup.new_tag("h2")
            summary_title.string = "📋 Résumé Exécutif"
            summary_div.append(summary_title)

            summary_content = soup.new_tag("div")
            summary_content.attrs["class"] = ["summary-content"]
            summary_p = soup.new_tag("p")
            summary_p.string = summary
            summary_content.append(summary_p)
            summary_div.append(summary_content)
            header_div.append(summary_div)

        container.append(header_div)

    def _add_news_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add news sections with categories."""
        # Define category mappings with emojis
        categories = {
            "suisse_romande": {"title": "🏔️ Suisse Romande", "emoji": "🇨🇭"},
            "suisse": {"title": "🇨🇭 Suisse", "emoji": "🇵🇺"},
            "france": {"title": "🇫🇷 France", "emoji": "🥖"},
            "europe": {"title": "🇪🇺 Europe", "emoji": "🇵🇺"},
            "world": {"title": "🌍 Monde", "emoji": "🌐"},
            "wars": {"title": "⚔️ Conflits", "emoji": "🚨"},
            "economy": {"title": "💰 Économie", "emoji": "📈"},
        }

        for category_key, category_info in categories.items():
            category_data = data.get(category_key, {})

            # Handle both dict with 'items' and direct list formats
            if isinstance(category_data, dict):
                items = category_data.get("items", [])
            elif isinstance(category_data, list):
                items = category_data
            else:
                continue

            if not items:
                continue

            # Create section
            section_div = soup.new_tag("section")
            section_div.attrs["class"] = ["news-section"]

            # Section title
            section_title = soup.new_tag("h2")
            section_title.attrs["class"] = ["section-title"]
            section_title.string = category_info["title"]
            section_div.append(section_title)

            # Add news items
            for item in items:
                self._add_news_item(soup, section_div, item)

            container.append(section_div)

    def _add_news_item(self, soup: BeautifulSoup, parent, item: dict) -> None:
        """Add individual news item."""
        article_div = soup.new_tag("article")
        article_div.attrs["class"] = ["news-item"]

        # Title (using French field name 'titre')
        title = item.get("titre") or item.get("title")
        if title:
            title_tag = soup.new_tag("h3")
            title_tag.attrs["class"] = ["news-title"]
            title_tag.string = title
            article_div.append(title_tag)

        # Meta information
        meta_div = soup.new_tag("div")
        meta_div.attrs["class"] = ["news-meta"]

        # Date
        if item.get("date"):
            date_span = soup.new_tag("span")
            date_span.attrs["class"] = ["news-date"]
            date_span.string = f"📅 {item['date']}"
            meta_div.append(date_span)

        # Source
        if item.get("source"):
            source_span = soup.new_tag("span")
            source_span.attrs["class"] = ["news-source"]
            source_span.string = f"📰 {item['source']}"
            meta_div.append(source_span)

        # Link (using French field name 'lien' or English 'link' or 'url')
        link = item.get("lien") or item.get("link") or item.get("url")
        if link and link != "#":
            link_tag = soup.new_tag("a", href=link, target="_blank", rel="noopener")
            link_tag.string = "🔗 Lire l'article"
            link_tag.attrs["class"] = ["news-link"]
            meta_div.append(link_tag)

        if meta_div.contents:
            article_div.append(meta_div)

        # Summary/Description (using French field name 'resume')
        summary = item.get("resume") or item.get("description") or item.get("summary")
        if summary:
            summary_div = soup.new_tag("div")
            summary_div.attrs["class"] = ["news-summary"]
            summary_p = soup.new_tag("p")
            summary_p.string = summary
            summary_div.append(summary_p)
            article_div.append(summary_div)

        parent.append(article_div)

    def _add_methodology(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add methodology section if available."""
        methodology = data.get("methodology")
        if not methodology:
            return

        method_div = soup.new_tag("section")
        method_div.attrs["class"] = ["methodology-section"]

        title_tag = soup.new_tag("h2")
        title_tag.string = "📊 Méthodologie"
        method_div.append(title_tag)

        content_div = soup.new_tag("div")
        content_div.attrs["class"] = ["methodology-content"]
        content_p = soup.new_tag("p")
        content_p.string = methodology
        content_div.append(content_p)
        method_div.append(content_div)

        container.append(method_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for news daily formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .news-daily-report {
            max-width: 1000px;
            margin: 0 auto;
        }
        .news-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .news-header h1 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 2.5rem;
        }
        .executive-summary {
            margin-top: 2rem;
            text-align: left;
        }
        .executive-summary h2 {
            color: var(--heading-color);
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        .summary-content {
            background: var(--highlight-bg);
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid var(--accent-color);
        }
        .news-section {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .section-title {
            color: var(--heading-color);
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent-color);
        }
        .news-item {
            margin: 1.5rem 0;
            padding: 1.5rem;
            background: var(--highlight-bg);
            border-radius: 8px;
            border-left: 4px solid var(--accent-color);
        }
        .news-title {
            color: var(--heading-color);
            font-size: 1.2rem;
            margin-bottom: 1rem;
            line-height: 1.4;
        }
        .news-meta {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: var(--text-color);
            opacity: 0.8;
        }
        .news-source {
            font-weight: 500;
        }
        .news-link {
            color: var(--accent-color);
            text-decoration: none;
            font-weight: 500;
        }
        .news-link:hover {
            text-decoration: underline;
        }
        .news-content {
            line-height: 1.6;
            color: var(--text-color);
        }
        .methodology-section {
            margin-top: 3rem;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .methodology-section h2 {
            color: var(--heading-color);
            margin-bottom: 1rem;
        }
        .methodology-content {
            font-style: italic;
            color: var(--text-color);
            opacity: 0.8;
        }
        """
        soup.head.append(style_tag) if soup.head else soup.append(style_tag)
