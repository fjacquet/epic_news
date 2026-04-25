"""Legal Analysis Renderer

Converts validated legal analysis data into a visually appealing HTML fragment.
Uses shared BaseRenderer methods to reduce code duplication.

Sections rendered:
1. Header with company name
2. Compliance Assessment
3. IP Portfolio Analysis
4. Regulatory Risk Assessment
5. Litigation History
6. M&A Due Diligence
7. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

from typing import Any

from .base_renderer import BaseRenderer


class LegalAnalysisRenderer(BaseRenderer):
    """Render a legal analysis report into a modern HTML fragment."""

    def __init__(self) -> None:
        """Initialize the legal analysis renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="legal-analysis-report")
        container = soup.div

        self.add_report_header(soup, container, "⚖️ Analyse Juridique", data.get("company_name"))
        self.render_dict_as_cards(
            soup, container, data.get("compliance_assessment"), "Évaluation de la Conformité", "✅"
        )
        self.render_dict_as_cards(
            soup,
            container,
            data.get("ip_portfolio_analysis"),
            "Portefeuille de Propriété Intellectuelle",
            "📜",
        )
        self.render_dict_as_cards(
            soup,
            container,
            data.get("regulatory_risk_assessment"),
            "Évaluation des Risques Réglementaires",
            "⚠️",
        )
        self.render_list_as_cards(
            soup, container, data.get("litigation_history"), "Historique des Litiges", "📂", "litigation-card"
        )
        self.render_dict_as_cards(soup, container, data.get("ma_due_diligence"), "Due Diligence M&A", "🤝")
        self.add_raw_json_section(soup, container, data, "Voir les données brutes")

        return str(soup)
