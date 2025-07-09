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

    def __init__(self) -> None:
        """Initialize the SaintRenderer."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render saint data to HTML.

        Args:
            data: Dictionary containing saint data

        Returns:
            HTML string for saint content
        """
        # Create main container
        soup = BeautifulSoup()
        soup.append(soup.new_tag("div", attrs={"class": "saint-report"}))
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add biography
        self._add_biography(soup, container, data)

        # Add feast day and details
        self._add_feast_details(soup, container, data)

        # Add miracles section
        self._add_miracles(soup, container, data)

        # Add swiss connection
        self._add_swiss_connection(soup, container, data)

        # Add spiritual significance
        self._add_spiritual_significance(soup, container, data)

        # Add prayer and reflection
        self._add_prayer_reflection(soup, container, data)

        # Add sources
        self._add_sources(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add saint header."""
        header_div = soup.new_tag("div", attrs={"class": "saint-header"})

        name = data.get("name", "Saint")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"✨ {name}"
        header_div.append(title_tag)

        # Add subtitle if available
        title = data.get("title") or data.get("epithet")
        if title:
            subtitle_p = soup.new_tag("p", attrs={"class": "saint-title"})
            subtitle_p.string = title
            header_div.append(subtitle_p)

        container.append(header_div)

    def _add_biography(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add saint biography section."""
        biography = data.get("biography") or data.get("life_story") or data.get("summary")
        if not biography:
            return

        bio_div = soup.new_tag("div", attrs={"class": "saint-biography"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "📖 Biographie"
        bio_div.append(title_tag)

        bio_p = soup.new_tag("p")
        bio_p.string = biography
        bio_div.append(bio_p)

        container.append(bio_div)

    def _add_feast_details(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add feast day and celebration details."""
        details_div = soup.new_tag("div", attrs={"class": "feast-details"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "🎉 Détails de la Fête"
        details_div.append(title_tag)

        details_added = False

        # Feast day
        feast_day = data.get("feast_day") or data.get("feast_date") or data.get("celebration_date")
        if feast_day:
            feast_p = soup.new_tag("p")
            feast_strong = soup.new_tag("strong")
            feast_strong.string = "📅 Jour de fête:"
            feast_p.append(feast_strong)
            feast_p.append(f" {feast_day}")
            details_div.append(feast_p)
            details_added = True

        # Birth year
        birth_year = data.get("birth_year")
        if birth_year:
            birth_p = soup.new_tag("p")
            birth_strong = soup.new_tag("strong")
            birth_strong.string = "🌟 Année de naissance:"
            birth_p.append(birth_strong)
            birth_p.append(f" {birth_year}")
            details_div.append(birth_p)
            details_added = True

        # Death year
        death_year = data.get("death_year")
        if death_year:
            death_p = soup.new_tag("p")
            death_strong = soup.new_tag("strong")
            death_strong.string = "✝️ Année de décès:"
            death_p.append(death_strong)
            death_p.append(f" {death_year}")
            details_div.append(death_p)
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

    def _add_miracles(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add miracles section."""
        miracles = data.get("miracles")
        if not miracles:
            return

        miracles_div = soup.new_tag("div", attrs={"class": "miracles"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "✨ Miracles"
        miracles_div.append(title_tag)

        if isinstance(miracles, str):
            miracles_p = soup.new_tag("p")
            miracles_p.string = miracles
            miracles_div.append(miracles_p)
        elif isinstance(miracles, list):
            miracles_ul = soup.new_tag("ul")
            for item in miracles:
                li = soup.new_tag("li")
                li.string = str(item)
                miracles_ul.append(li)
            miracles_div.append(miracles_ul)

        container.append(miracles_div)

    def _add_swiss_connection(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add Swiss connection section."""
        swiss_connection = data.get("swiss_connection")
        if not swiss_connection:
            return

        swiss_div = soup.new_tag("div", attrs={"class": "swiss-connection"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "🇨🇭 Lien avec la Suisse"
        swiss_div.append(title_tag)

        swiss_p = soup.new_tag("p")
        swiss_p.string = swiss_connection
        swiss_div.append(swiss_p)

        container.append(swiss_div)

    def _add_spiritual_significance(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add spiritual significance section."""
        significance = (
            data.get("spiritual_significance")
            or data.get("significance")
            or data.get("teachings")
            or data.get("legacy")
        )
        if not significance:
            return

        spiritual_div = soup.new_tag("div", attrs={"class": "spiritual-significance"})

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

    def _add_prayer_reflection(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add prayer and reflection section."""
        prayer = data.get("prayer_reflection") or data.get("prayer") or data.get("reflection")
        if not prayer:
            return

        prayer_div = soup.new_tag("div", attrs={"class": "prayer-reflection"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "📿 Prière et Réflexion"
        prayer_div.append(title_tag)

        prayer_p = soup.new_tag("p")
        prayer_p.string = prayer
        prayer_div.append(prayer_p)

        container.append(prayer_div)

    def _add_sources(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add sources section."""
        sources = data.get("sources")
        if not sources or not isinstance(sources, list) or not sources:
            return

        sources_div = soup.new_tag("div", attrs={"class": "sources"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "📚 Sources"
        sources_div.append(title_tag)

        sources_ul = soup.new_tag("ul")
        for source in sources:
            li = soup.new_tag("li")
            li.string = source
            sources_ul.append(li)
        sources_div.append(sources_ul)

        container.append(sources_div)

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
        .saint-biography, .feast-details, .spiritual-significance, .miracles, .swiss-connection, .prayer-reflection, .sources {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .saint-biography h3, .feast-details h3, .spiritual-significance h3, .miracles h3, .swiss-connection h3, .prayer-reflection h3, .sources h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .saint-biography p, .feast-details p, .spiritual-significance p, .miracles p, .swiss-connection p, .prayer-reflection p, .sources p {
            color: var(--text-color);
            line-height: 1.6;
            margin: 0.75rem 0;
        }
        .feast-details strong, .spiritual-significance strong, .sources strong {
            color: var(--heading-color);
        }
        .spiritual-significance ul, .sources ul {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }
        .spiritual-significance li, .sources li {
            color: var(--text-color);
            margin: 0.5rem 0;
            line-height: 1.5;
        }
        """
        soup.append(style_tag)
