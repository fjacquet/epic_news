"""Geospatial Analysis Renderer

Converts validated geospatial analysis data into a visually appealing HTML fragment.
This renderer displays physical locations, risk assessment, supply chain mapping,
and M&A insights.

Sections rendered:
1. Header with company name
2. Physical Locations
3. Risk Assessment
4. Supply Chain Map
5. M&A Insights
6. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class GeospatialAnalysisRenderer(BaseRenderer):
    """Render a geospatial analysis report into a modern HTML fragment."""

    def __init__(self) -> None:
        """Initialize the geospatial analysis renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="geospatial-report")
        container = soup.div

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_locations(soup, container, data)
        self._add_risk_assessment(soup, container, data)
        self._add_supply_chain(soup, container, data)
        self._add_ma_insights(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h1")
        title.string = "🗺️ Analyse Géospatiale"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _render_list_section(
        soup: BeautifulSoup,
        container: Any,
        items: list[dict[str, Any]],
        title_text: str,
        icon: str,
        card_class: str = "info-card",
    ) -> None:
        if not items:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = f"{icon} {title_text}"
        section.append(title)

        grid = soup.new_tag("div", **{"class": "cards-grid"})  # type: ignore[arg-type]

        for item in items:
            card = soup.new_tag("div", **{"class": card_class})  # type: ignore[arg-type]

            if isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, list):
                        h4 = soup.new_tag("h4")
                        h4.string = k.replace("_", " ").title()
                        card.append(h4)
                        ul = soup.new_tag("ul")
                        for list_item in v:
                            li = soup.new_tag("li")
                            li.string = str(list_item)
                            ul.append(li)
                        card.append(ul)
                    elif isinstance(v, dict):
                        h4 = soup.new_tag("h4")
                        h4.string = k.replace("_", " ").title()
                        card.append(h4)
                        for sub_k, sub_v in v.items():
                            p = soup.new_tag("p")
                            strong = soup.new_tag("strong")
                            strong.string = f"{sub_k.replace('_', ' ').title()}: "
                            p.append(strong)
                            p.append(str(sub_v))
                            card.append(p)
                    else:
                        p = soup.new_tag("p")
                        strong = soup.new_tag("strong")
                        strong.string = f"{k.replace('_', ' ').title()}: "
                        p.append(strong)
                        p.append(str(v))
                        card.append(p)
            else:
                p = soup.new_tag("p")
                p.string = str(item)
                card.append(p)

            grid.append(card)

        section.append(grid)
        container.append(section)

    def _add_locations(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_list_section(
            soup, container, data.get("physical_locations", []), "Emplacements Physiques", "📍", "location-card"
        )

    def _add_risk_assessment(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_list_section(
            soup, container, data.get("risk_assessment", []), "Évaluation des Risques", "⚠️", "risk-card"
        )

    def _add_supply_chain(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_list_section(
            soup, container, data.get("supply_chain_map", []), "Cartographie de la Chaîne d'Approvisionnement", "🔗", "supply-card"
        )

    def _add_ma_insights(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_list_section(
            soup,
            container,
            data.get("mergers_and_acquisitions_insights", []),
            "Intelligence M&A",
            "🤝",
            "ma-card",
        )

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        details = soup.new_tag("details", **{"class": "raw-data"})  # type: ignore[arg-type]
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
            .geospatial-report {
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
                margin-bottom: 1rem;
                border-bottom: 1px solid var(--border-color, #e5e7eb);
                padding-bottom: 0.5rem;
            }
            .cards-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 1rem;
            }
            .info-card, .location-card, .risk-card, .supply-card, .ma-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
            }
            .location-card {
                border-left: 4px solid #3b82f6;
            }
            .risk-card {
                border-left: 4px solid #ef4444;
            }
            .supply-card {
                border-left: 4px solid #10b981;
            }
            .ma-card {
                border-left: 4px solid #8b5cf6;
            }
            .info-card h4, .location-card h4, .risk-card h4, .supply-card h4, .ma-card h4 {
                margin: 0.5rem 0;
                color: var(--header-color, #111827);
                font-size: 1rem;
            }
            .info-card ul, .location-card ul, .risk-card ul, .supply-card ul, .ma-card ul {
                margin: 0.5rem 0;
                padding-left: 1.25rem;
            }
            .info-card li {
                margin-bottom: 0.25rem;
            }
            .info-card p, .location-card p, .risk-card p, .supply-card p, .ma-card p {
                margin: 0.5rem 0;
                font-size: 0.9rem;
            }
            .raw-data {
                margin-top: 2.5rem;
                border-top: 1px solid var(--border-color, #e5e7eb);
                padding-top: 1.5rem;
            }
            .raw-data summary {
                cursor: pointer;
                font-weight: 500;
            }
            .raw-data pre {
                background: var(--pre-bg, #f3f4f6);
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
                margin-top: 1rem;
            }
            @media (prefers-color-scheme: dark) {
                .geospatial-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .info-card, .location-card, .risk-card, .supply-card, .ma-card {
                    background: #374151;
                    border-color: #4b5563;
                }
                .raw-data pre {
                    background: #374151;
                }
            }
        """
        soup.append(style)
