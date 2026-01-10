"""Legal Analysis Renderer

Converts validated legal analysis data into a visually appealing HTML fragment.
This renderer displays compliance assessment, IP portfolio analysis, regulatory
risk assessment, litigation history, and M&A due diligence.

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

import json
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
        self._add_header(soup, container, data)
        self._add_compliance(soup, container, data)
        self._add_ip_portfolio(soup, container, data)
        self._add_regulatory(soup, container, data)
        self._add_litigation(soup, container, data)
        self._add_ma_diligence(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h1")
        title.string = "⚖️ Analyse Juridique"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _render_dict_section(
        soup: BeautifulSoup,
        container: Any,
        section_data: dict[str, Any],
        title_text: str,
        icon: str,
    ) -> None:
        if not section_data:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = f"{icon} {title_text}"
        section.append(title)

        for key, value in section_data.items():
            card = soup.new_tag("div", **{"class": "info-card"})  # type: ignore[arg-type]
            card_title = soup.new_tag("h3")
            card_title.string = key.replace("_", " ").title()
            card.append(card_title)

            if isinstance(value, list):
                ul = soup.new_tag("ul")
                for item in value:
                    li = soup.new_tag("li")
                    li.string = str(item)
                    ul.append(li)
                card.append(ul)
            elif isinstance(value, dict):
                for k, v in value.items():
                    p = soup.new_tag("p")
                    strong = soup.new_tag("strong")
                    strong.string = f"{k.replace('_', ' ').title()}: "
                    p.append(strong)
                    p.append(str(v))
                    card.append(p)
            else:
                p = soup.new_tag("p")
                p.string = str(value)
                card.append(p)

            section.append(card)

        container.append(section)

    def _add_compliance(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_dict_section(
            soup, container, data.get("compliance_assessment", {}), "Évaluation de la Conformité", "✅"
        )

    def _add_ip_portfolio(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_dict_section(
            soup, container, data.get("ip_portfolio_analysis", {}), "Portefeuille de Propriété Intellectuelle", "📜"
        )

    def _add_regulatory(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_dict_section(
            soup, container, data.get("regulatory_risk_assessment", {}), "Évaluation des Risques Réglementaires", "⚠️"
        )

    @staticmethod
    def _add_litigation(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        litigation = data.get("litigation_history", [])
        if not litigation:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "📂 Historique des Litiges"
        section.append(title)

        for case in litigation:
            card = soup.new_tag("div", **{"class": "litigation-card"})  # type: ignore[arg-type]

            if isinstance(case, dict):
                for k, v in case.items():
                    p = soup.new_tag("p")
                    strong = soup.new_tag("strong")
                    strong.string = f"{k.replace('_', ' ').title()}: "
                    p.append(strong)
                    p.append(str(v))
                    card.append(p)
            else:
                p = soup.new_tag("p")
                p.string = str(case)
                card.append(p)

            section.append(card)

        container.append(section)

    def _add_ma_diligence(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._render_dict_section(
            soup, container, data.get("ma_due_diligence", {}), "Due Diligence M&A", "🤝"
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
            .info-card, .litigation-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            }
            .litigation-card {
                border-left: 4px solid var(--accent-color, #6366f1);
            }
            .info-card h3, .litigation-card h3 {
                margin: 0 0 1rem 0;
                color: var(--header-color, #111827);
            }
            .info-card ul {
                margin: 0;
                padding-left: 1.25rem;
            }
            .info-card li {
                margin-bottom: 0.5rem;
            }
            .info-card p, .litigation-card p {
                margin: 0.5rem 0;
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
                .legal-analysis-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .info-card, .litigation-card {
                    background: #374151;
                    border-color: #4b5563;
                }
                .raw-data pre {
                    background: #374151;
                }
            }
        """
        soup.append(style)
