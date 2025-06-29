"""
Saint Renderer

Renders saint data to structured HTML using BeautifulSoup.
Handles saint biography, feast days, and spiritual content.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class SaintRenderer(BaseRenderer):
    """Renders saint content with spiritual formatting."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render saint data to HTML.

        Args:
            data: Dictionary containing saint data

        Returns:
            HTML string for saint content
        """
        # Create main container
        soup = self.create_soup("div", class_="saint-report")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add biography
        self._add_biography(soup, container, data)

        # Add feast day and details
        self._add_feast_details(soup, container, data)

        # Add spiritual significance
        self._add_spiritual_significance(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add saint header."""
        header_div = soup.new_tag("div", class_="saint-header")

        name = data.get("name", "Saint")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"✨ {name}"
        header_div.append(title_tag)

        # Add subtitle if available
        title = data.get("title") or data.get("epithet")
        if title:
            subtitle_p = soup.new_tag("p", class_="saint-title")
            subtitle_p.string = title
            header_div.append(subtitle_p)

        container.append(header_div)

    def _add_biography(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add saint biography section."""
        biography = data.get("biography") or data.get("life_story") or data.get("summary")
        if not biography:
            return

        bio_div = soup.new_tag("div", class_="saint-biography")

        title_tag = soup.new_tag("h3")
        title_tag.string = "📖 Biographie"
        bio_div.append(title_tag)

        bio_p = soup.new_tag("p")
        bio_p.string = biography
        bio_div.append(bio_p)

        container.append(bio_div)

    def _add_feast_details(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add feast day and celebration details."""
        details_div = soup.new_tag("div", class_="feast-details")

        title_tag = soup.new_tag("h3")
        title_tag.string = "🎉 Détails de la Fête"
        details_div.append(title_tag)

        details_added = False

        # Feast day
        feast_day = data.get("feast_day") or data.get("celebration_date")
        if feast_day:
            feast_p = soup.new_tag("p")
            feast_strong = soup.new_tag("strong")
            feast_strong.string = "📅 Jour de fête:"
            feast_p.append(feast_strong)
            feast_p.append(f" {feast_day}")
            details_div.append(feast_p)
            details_added = True

        # Patronage
        patronage = data.get("patronage") or data.get("patron_of")
        if patronage:
            patron_p = soup.new_tag("p")
            patron_strong = soup.new_tag("strong")
            patron_strong.string = "🛡️ Patron de:"
            patron_p.append(patron_strong)

            if isinstance(patronage, list):
                patron_p.append(f" {', '.join(patronage)}")
            else:
                patron_p.append(f" {patronage}")

            details_div.append(patron_p)
            details_added = True

        # Symbols
        symbols = data.get("symbols") or data.get("attributes")
        if symbols:
            symbols_p = soup.new_tag("p")
            symbols_strong = soup.new_tag("strong")
            symbols_strong.string = "🔮 Symboles:"
            symbols_p.append(symbols_strong)

            if isinstance(symbols, list):
                symbols_p.append(f" {', '.join(symbols)}")
            else:
                symbols_p.append(f" {symbols}")

            details_div.append(symbols_p)
            details_added = True

        if details_added:
            container.append(details_div)

    def _add_spiritual_significance(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add spiritual significance section."""
        significance = data.get("spiritual_significance") or data.get("teachings") or data.get("legacy")
        if not significance:
            return

        spiritual_div = soup.new_tag("div", class_="spiritual-significance")

        title_tag = soup.new_tag("h3")
        title_tag.string = "🙏 Signification Spirituelle"
        spiritual_div.append(title_tag)

        if isinstance(significance, str):
            spiritual_p = soup.new_tag("p")
            spiritual_p.string = significance
            spiritual_div.append(spiritual_p)
        elif isinstance(significance, list):
            spiritual_ul = soup.new_tag("ul")
            for item in significance:
                li = soup.new_tag("li")
                li.string = str(item)
                spiritual_ul.append(li)
            spiritual_div.append(spiritual_ul)

        container.append(spiritual_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for saint formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .saint-report {
            max-width: 800px;
            margin: 0 auto;
        }
        .saint-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .saint-header h2 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }
        .saint-title {
            color: var(--text-color);
            font-style: italic;
            font-size: 1.1rem;
            margin: 0;
        }
        .saint-biography, .feast-details, .spiritual-significance {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .saint-biography h3, .feast-details h3, .spiritual-significance h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .saint-biography p, .feast-details p, .spiritual-significance p {
            color: var(--text-color);
            line-height: 1.6;
            margin: 0.75rem 0;
        }
        .feast-details strong, .spiritual-significance strong {
            color: var(--heading-color);
        }
        .spiritual-significance ul {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }
        .spiritual-significance li {
            color: var(--text-color);
            margin: 0.5rem 0;
            line-height: 1.5;
        }
        """
        soup.append(style_tag)
