"""Tech Stack Renderer

Converts validated tech stack data into a visually appealing HTML fragment.
This renderer displays technology stack analysis with categories, strengths,
weaknesses, and recommendations.

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

import json
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

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_executive_summary(soup, container, data)
        self._add_technology_stack(soup, container, data)
        self._add_strengths_weaknesses(soup, container, data)
        self._add_open_source(soup, container, data)
        self._add_talent_assessment(soup, container, data)
        self._add_recommendations(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h1")
        title.string = "🔧 Analyse de la Stack Technologique"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _add_executive_summary(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        summary = data.get("executive_summary")
        if not summary:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "📋 Résumé Exécutif"
        section.append(title)
        para = soup.new_tag("p")
        para.string = summary
        section.append(para)
        container.append(section)

    @staticmethod
    def _add_technology_stack(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        stack = data.get("technology_stack", [])
        if not stack:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "💻 Technologies Utilisées"
        section.append(title)

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

    @staticmethod
    def _add_strengths_weaknesses(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        if not strengths and not weaknesses:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "⚖️ Forces et Faiblesses"
        section.append(title)

        grid = soup.new_tag("div")
        grid.attrs["class"] = "swot-grid"  # type: ignore[assignment]

        if strengths:
            str_div = soup.new_tag("div")
            str_div.attrs["class"] = "strengths-card"  # type: ignore[assignment]
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
            weak_div = soup.new_tag("div")
            weak_div.attrs["class"] = "weaknesses-card"  # type: ignore[assignment]
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

    @staticmethod
    def _add_open_source(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        oss = data.get("open_source_contributions", [])
        if not oss:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "🌐 Contributions Open Source"
        section.append(title)
        ul = soup.new_tag("ul")
        for item in oss:
            li = soup.new_tag("li")
            li.string = item
            ul.append(li)
        section.append(ul)
        container.append(section)

    @staticmethod
    def _add_talent_assessment(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        talent = data.get("talent_assessment")
        if not talent:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "👥 Évaluation des Talents"
        section.append(title)
        para = soup.new_tag("p")
        para.string = talent
        section.append(para)
        container.append(section)

    @staticmethod
    def _add_recommendations(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        recs = data.get("recommendations", [])
        if not recs:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "💡 Recommandations"
        section.append(title)
        ul = soup.new_tag("ul")
        ul.attrs["class"] = "recommendations-list"  # type: ignore[assignment]
        for rec in recs:
            li = soup.new_tag("li")
            li.string = rec
            ul.append(li)
        section.append(ul)
        container.append(section)

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        details = soup.new_tag("details")
        details.attrs["class"] = "raw-data"  # type: ignore[assignment]
        summary = soup.new_tag("summary")
        summary.string = "Voir les données brutes"
        details.append(summary)
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        container.append(details)

    @staticmethod
    def _add_styles(soup: BeautifulSoup) -> None:
        style = soup.new_tag("style")
        style.string = """
            .tech-stack-report {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 900px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: var(--background-light, #ffffff);
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: var(--text-light, #333);
            }
            .report-header {
                text-align: center;
                margin-bottom: 2.5rem;
                border-bottom: 1px solid var(--border-color, #e5e7eb);
                padding-bottom: 1rem;
            }
            .report-header h1 {
                font-size: 2rem;
                font-weight: 700;
                color: var(--header-color, #111827);
                margin: 0 0 0.5rem 0;
            }
            .report-header h2 {
                font-size: 1.25rem;
                font-weight: 500;
                color: var(--subheader-color, #6b7280);
                margin: 0;
            }
            .report-section {
                margin-bottom: 2rem;
            }
            .report-section h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--header-color, #111827);
                margin-bottom: 1rem;
                border-bottom: 1px solid var(--border-color, #e5e7eb);
                padding-bottom: 0.5rem;
            }
            .report-section p {
                line-height: 1.7;
                color: var(--text-color, #374151);
            }
            .tech-category {
                margin-bottom: 1.5rem;
            }
            .tech-category h3 {
                font-size: 1.125rem;
                color: var(--category-color, #4b5563);
                margin-bottom: 0.75rem;
            }
            .tech-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 1rem;
            }
            .tech-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1rem;
            }
            .tech-card h4 {
                margin: 0 0 0.5rem 0;
                color: var(--header-color, #111827);
            }
            .tech-card p {
                margin: 0;
                font-size: 0.875rem;
                color: var(--text-muted, #6b7280);
            }
            .swot-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
            }
            .strengths-card, .weaknesses-card {
                border-radius: 8px;
                padding: 1.5rem;
            }
            .strengths-card {
                background: var(--success-bg, #ecfdf5);
                border: 1px solid var(--success-border, #10b981);
            }
            .weaknesses-card {
                background: var(--warning-bg, #fef3c7);
                border: 1px solid var(--warning-border, #f59e0b);
            }
            .strengths-card h3, .weaknesses-card h3 {
                margin: 0 0 1rem 0;
            }
            .strengths-card ul, .weaknesses-card ul {
                margin: 0;
                padding-left: 1.25rem;
            }
            .strengths-card li, .weaknesses-card li {
                margin-bottom: 0.5rem;
            }
            .recommendations-list li {
                margin-bottom: 0.75rem;
                padding-left: 0.5rem;
            }
            .raw-data {
                margin-top: 2.5rem;
                border-top: 1px solid var(--border-color, #e5e7eb);
                padding-top: 1.5rem;
            }
            .raw-data summary {
                cursor: pointer;
                font-weight: 500;
                color: var(--summary-color, #374151);
            }
            .raw-data pre {
                background: var(--pre-bg, #f3f4f6);
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
                margin-top: 1rem;
            }
            @media (prefers-color-scheme: dark) {
                .tech-stack-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .report-header h1, .report-section h2, .tech-card h4 {
                    color: #f9fafb;
                }
                .tech-card, .raw-data pre {
                    background: #374151;
                    border-color: #4b5563;
                }
                .strengths-card {
                    background: #064e3b;
                    border-color: #10b981;
                }
                .weaknesses-card {
                    background: #78350f;
                    border-color: #f59e0b;
                }
            }
        """
        soup.append(style)
