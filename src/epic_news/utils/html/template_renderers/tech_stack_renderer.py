"""Tech Stack Renderer

Converts validated tech stack data into a visually appealing HTML fragment.
Uses shared BaseRenderer methods to reduce code duplication.

Sections rendered:
1. Header with company name
2. Executive Summary
3. Technology Stack (grouped by category)
4. Strengths & Weaknesses
5. Open Source Contributions
6. Talent Assessment
7. Recommendations
8. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class TechStackRenderer(BaseRenderer):
    """Render a tech stack report into a modern HTML fragment."""

    def __init__(self) -> None:
        """Initialize the tech stack renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="tech-stack-report")
        container = soup.div

        self.add_report_header(
            soup, container, "🔧 Analyse de la Stack Technologique", data.get("company_name")
        )
        self.render_text_section(soup, container, data.get("executive_summary"), "Résumé Exécutif", "📋")
        self._add_technology_stack(soup, container, data)
        self._add_strengths_weaknesses(soup, container, data)
        self._add_open_source(soup, container, data)
        self.render_text_section(
            soup, container, data.get("talent_assessment"), "Évaluation des Talents", "👥"
        )
        self._add_recommendations(soup, container, data)
        self.add_raw_json_section(soup, container, data, "Voir les données brutes")

        return str(soup)

    def _add_technology_stack(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render technology stack grouped by category."""
        stack = data.get("technology_stack", [])
        if not stack:
            return

        section = self.create_section(soup, "Technologies Utilisées", "💻")

        # Group by category
        categories: dict[str, list[dict[str, Any]]] = {}
        for tech in stack:
            cat = tech.get("category", "Autre")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tech)

        for cat_name, techs in categories.items():
            cat_div = soup.new_tag("div", **{"class": "tech-category"})  # type: ignore[arg-type]
            cat_title = soup.new_tag("h3")
            cat_title.string = cat_name
            cat_div.append(cat_title)

            grid = soup.new_tag("div", **{"class": "tech-grid"})  # type: ignore[arg-type]
            for tech in techs:
                card = soup.new_tag("div", **{"class": "tech-card"})  # type: ignore[arg-type]
                name = soup.new_tag("h4")
                name.string = tech.get("name", "N/A")
                card.append(name)
                if desc := tech.get("description"):
                    desc_p = soup.new_tag("p")
                    desc_p.string = desc
                    card.append(desc_p)
                grid.append(card)
            cat_div.append(grid)
            section.append(cat_div)

        container.append(section)

    def _add_strengths_weaknesses(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render strengths and weaknesses in a SWOT-style grid."""
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        if not strengths and not weaknesses:
            return

        section = self.create_section(soup, "Forces et Faiblesses", "⚖️")
        grid = soup.new_tag("div", **{"class": "swot-grid"})  # type: ignore[arg-type]

        if strengths:
            str_div = soup.new_tag("div", **{"class": "strengths-card"})  # type: ignore[arg-type]
            str_title = soup.new_tag("h3")
            str_title.string = "✅ Forces"
            str_div.append(str_title)
            ul = soup.new_tag("ul")
            for s in strengths:
                li = soup.new_tag("li")
                li.string = s
                ul.append(li)
            str_div.append(ul)
            grid.append(str_div)

        if weaknesses:
            weak_div = soup.new_tag("div", **{"class": "weaknesses-card"})  # type: ignore[arg-type]
            weak_title = soup.new_tag("h3")
            weak_title.string = "⚠️ Faiblesses"
            weak_div.append(weak_title)
            ul = soup.new_tag("ul")
            for w in weaknesses:
                li = soup.new_tag("li")
                li.string = w
                ul.append(li)
            weak_div.append(ul)
            grid.append(weak_div)

        section.append(grid)
        container.append(section)

    def _add_open_source(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render open source contributions as a list."""
        oss = data.get("open_source_contributions", [])
        if not oss:
            return

        section = self.create_section(soup, "Contributions Open Source", "🌐")
        ul = soup.new_tag("ul")
        for item in oss:
            li = soup.new_tag("li")
            li.string = item
            ul.append(li)
        section.append(ul)
        container.append(section)

    def _add_recommendations(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render recommendations as a styled list."""
        recs = data.get("recommendations", [])
        if not recs:
            return

        section = self.create_section(soup, "Recommandations", "💡")
        ul = soup.new_tag("ul", **{"class": "recommendations-list"})  # type: ignore[arg-type]
        for rec in recs:
            li = soup.new_tag("li")
            li.string = rec
            ul.append(li)
        section.append(ul)
        container.append(section)
