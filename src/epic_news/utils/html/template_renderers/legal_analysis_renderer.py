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

from bs4 import BeautifulSoup

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

        self._add_styles(soup)
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

    @staticmethod
    def _add_styles(soup: BeautifulSoup) -> None:
        style = soup.new_tag("style")
        style.string = """
            .legal-analysis-report {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 900px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: var(--background-light, #ffffff);
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: var(--text-light, #333);
            }
            .report-header { text-align: center; margin-bottom: 2.5rem; border-bottom: 1px solid var(--border-color, #e5e7eb); padding-bottom: 1rem; }
            .report-header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem 0; }
            .report-header h2 { font-size: 1.25rem; font-weight: 500; color: var(--subheader-color, #6b7280); margin: 0; }
            .report-section { margin-bottom: 2rem; }
            .report-section h2 { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; border-bottom: 1px solid var(--border-color, #e5e7eb); padding-bottom: 0.5rem; }
            .info-card, .litigation-card { background: var(--card-bg, #f9fafb); border: 1px solid var(--card-border, #e5e7eb); border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
            .litigation-card { border-left: 4px solid var(--accent-color, #6366f1); }
            .info-card h3, .litigation-card h3 { margin: 0 0 1rem 0; color: var(--header-color, #111827); }
            .info-card ul { margin: 0; padding-left: 1.25rem; }
            .info-card li { margin-bottom: 0.5rem; }
            .info-card p, .litigation-card p { margin: 0.5rem 0; }
            .cards-grid { display: grid; gap: 1rem; }
            .raw-data { margin-top: 2.5rem; border-top: 1px solid var(--border-color, #e5e7eb); padding-top: 1.5rem; }
            .raw-data summary { cursor: pointer; font-weight: 500; }
            .raw-data pre { background: var(--pre-bg, #f3f4f6); padding: 1rem; border-radius: 8px; overflow-x: auto; margin-top: 1rem; }
            @media (prefers-color-scheme: dark) {
                .legal-analysis-report { background-color: #1f2937; color: #e5e7eb; }
                .info-card, .litigation-card { background: #374151; border-color: #4b5563; }
                .raw-data pre { background: #374151; }
            }
        """
        soup.append(style)
