"""HR Intelligence Renderer

Converts validated HR intelligence data into a visually appealing HTML fragment.
Uses shared BaseRenderer methods to reduce code duplication.

Sections rendered:
1. Header with company name
2. Summary & Recommendations
3. Leadership Assessment
4. Employee Sentiment
5. Organizational Culture
6. Talent Acquisition Strategy
7. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

from typing import Any

from .base_renderer import BaseRenderer


class HRIntelligenceRenderer(BaseRenderer):
    """Render an HR intelligence report into a modern HTML fragment."""

    def __init__(self) -> None:
        """Initialize the HR intelligence renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="hr-intelligence-report")
        container = soup.div

        self.add_report_header(soup, container, "👥 Intelligence RH", data.get("company_name"))
        self.render_text_section(
            soup, container, data.get("summary_and_recommendations"), "Résumé et Recommandations", "📋"
        )
        self.render_dict_as_cards(
            soup, container, data.get("leadership_assessment"), "Évaluation du Leadership", "👔"
        )
        self.render_dict_as_cards(
            soup, container, data.get("employee_sentiment"), "Sentiment des Employés", "💭"
        )
        self.render_dict_as_cards(
            soup, container, data.get("organizational_culture"), "Culture Organisationnelle", "🏢"
        )
        self.render_dict_as_cards(
            soup,
            container,
            data.get("talent_acquisition_strategy"),
            "Stratégie d'Acquisition de Talents",
            "🎯",
        )
        self.add_raw_json_section(soup, container, data, "Voir les données brutes")

        return str(soup)
