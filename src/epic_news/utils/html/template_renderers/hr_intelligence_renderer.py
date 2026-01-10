"""HR Intelligence Renderer

Converts validated HR intelligence data into a visually appealing HTML fragment.
This renderer displays leadership assessment, employee sentiment, organizational
culture, talent acquisition strategy, and recommendations.

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

import json
from typing import Any

from bs4 import BeautifulSoup

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

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_summary(soup, container, data)
        self._add_leadership(soup, container, data)
        self._add_sentiment(soup, container, data)
        self._add_culture(soup, container, data)
        self._add_talent(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h1")
        title.string = "👥 Intelligence RH"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _add_summary(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        summary = data.get("summary_and_recommendations")
        if not summary:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "📋 Résumé et Recommandations"
        section.append(title)
        para = soup.new_tag("p")
        para.string = summary
        section.append(para)
        container.append(section)

    @staticmethod
    def _add_dict_section(
        soup: BeautifulSoup,
        container: Any,
        data: dict[str, Any],
        key: str,
        title_text: str,
        icon: str,
    ) -> None:
        section_data = data.get(key)
        if not section_data:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = f"{icon} {title_text}"
        section.append(title)

        if isinstance(section_data, dict):
            for sub_key, sub_value in section_data.items():
                card = soup.new_tag("div", **{"class": "info-card"})  # type: ignore[arg-type]
                card_title = soup.new_tag("h3")
                card_title.string = sub_key.replace("_", " ").title()
                card.append(card_title)

                if isinstance(sub_value, list):
                    ul = soup.new_tag("ul")
                    for item in sub_value:
                        li = soup.new_tag("li")
                        li.string = str(item)
                        ul.append(li)
                    card.append(ul)
                elif isinstance(sub_value, dict):
                    for k, v in sub_value.items():
                        p = soup.new_tag("p")
                        strong = soup.new_tag("strong")
                        strong.string = f"{k.replace('_', ' ').title()}: "
                        p.append(strong)
                        p.append(str(v))
                        card.append(p)
                else:
                    p = soup.new_tag("p")
                    p.string = str(sub_value)
                    card.append(p)

                section.append(card)
        else:
            para = soup.new_tag("p")
            para.string = str(section_data)
            section.append(para)

        container.append(section)

    def _add_leadership(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._add_dict_section(soup, container, data, "leadership_assessment", "Évaluation du Leadership", "👔")

    def _add_sentiment(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._add_dict_section(soup, container, data, "employee_sentiment", "Sentiment des Employés", "💭")

    def _add_culture(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._add_dict_section(soup, container, data, "organizational_culture", "Culture Organisationnelle", "🏢")

    def _add_talent(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        self._add_dict_section(
            soup, container, data, "talent_acquisition_strategy", "Stratégie d'Acquisition de Talents", "🎯"
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
            .hr-intelligence-report {
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
            .report-section p {
                line-height: 1.7;
            }
            .info-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            }
            .info-card h3 {
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
            .info-card p {
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
                .hr-intelligence-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .info-card {
                    background: #374151;
                    border-color: #4b5563;
                }
                .raw-data pre {
                    background: #374151;
                }
            }
        """
        soup.append(style)
