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
