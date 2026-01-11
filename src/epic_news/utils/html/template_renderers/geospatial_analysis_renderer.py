"""Geospatial Analysis Renderer

Converts validated geospatial analysis data into a visually appealing HTML fragment.
Uses shared BaseRenderer methods to reduce code duplication.

Sections rendered:
1. Header with company name
2. Physical Locations
3. Risk Assessment
4. Supply Chain Map
5. M&A Insights
6. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

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
        self.add_report_header(soup, container, "🗺️ Analyse Géospatiale", data.get("company_name"))
        self.render_list_as_cards(
            soup, container, data.get("physical_locations"), "Emplacements Physiques", "📍", "location-card"
        )
        self.render_list_as_cards(
            soup, container, data.get("risk_assessment"), "Évaluation des Risques", "⚠️", "risk-card"
        )
        self.render_list_as_cards(
            soup,
            container,
            data.get("supply_chain_map"),
            "Cartographie de la Chaîne d'Approvisionnement",
            "🔗",
            "supply-card",
        )
        self.render_list_as_cards(
            soup,
            container,
            data.get("mergers_and_acquisitions_insights"),
            "Intelligence M&A",
            "🤝",
            "ma-card",
        )
        self.add_raw_json_section(soup, container, data, "Voir les données brutes")

        return str(soup)

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
            .report-header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem 0; }
            .report-header h2 { font-size: 1.25rem; font-weight: 500; color: var(--subheader-color, #6b7280); margin: 0; }
            .report-section { margin-bottom: 2rem; }
            .report-section h2 { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color, #e5e7eb); padding-bottom: 0.5rem; }
            .cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
            .info-card, .location-card, .risk-card, .supply-card, .ma-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
            }
            .location-card { border-left: 4px solid #3b82f6; }
            .risk-card { border-left: 4px solid #ef4444; }
            .supply-card { border-left: 4px solid #10b981; }
            .ma-card { border-left: 4px solid #8b5cf6; }
            .info-card h3, .location-card h3, .risk-card h3, .supply-card h3, .ma-card h3 {
                margin: 0 0 1rem 0;
                color: var(--header-color, #111827);
            }
            .info-card p, .location-card p, .risk-card p, .supply-card p, .ma-card p {
                margin: 0.5rem 0;
                font-size: 0.9rem;
            }
            .raw-data { margin-top: 2.5rem; border-top: 1px solid var(--border-color, #e5e7eb); padding-top: 1.5rem; }
            .raw-data summary { cursor: pointer; font-weight: 500; }
            .raw-data pre { background: var(--pre-bg, #f3f4f6); padding: 1rem; border-radius: 8px; overflow-x: auto; margin-top: 1rem; }
            @media (prefers-color-scheme: dark) {
                .geospatial-report { background-color: #1f2937; color: #e5e7eb; }
                .info-card, .location-card, .risk-card, .supply-card, .ma-card { background: #374151; border-color: #4b5563; }
                .raw-data pre { background: #374151; }
            }
        """
        soup.append(style)
