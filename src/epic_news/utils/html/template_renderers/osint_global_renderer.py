"""Global OSINT Renderer

Combines all OSINT sub-reports into a comprehensive HTML document.
This renderer aggregates data from Company Profile, Tech Stack, Web Presence,
HR Intelligence, Legal Analysis, Geospatial Analysis, and Cross Reference reports.

The rendered report includes:
1. Executive Summary with company overview
2. Table of Contents with navigation
3. All individual reports as sections
4. Collapsible raw JSON for each section
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer
from .company_profiler_renderer import CompanyProfilerRenderer
from .cross_reference_report_renderer import CrossReferenceReportRenderer
from .geospatial_analysis_renderer import GeospatialAnalysisRenderer
from .hr_intelligence_renderer import HRIntelligenceRenderer
from .legal_analysis_renderer import LegalAnalysisRenderer
from .tech_stack_renderer import TechStackRenderer
from .web_presence_renderer import WebPresenceRenderer


class OSINTGlobalRenderer(BaseRenderer):
    """Render a comprehensive OSINT report from multiple sub-reports."""

    def __init__(self) -> None:
        """Initialize the OSINT global renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """
        Return the rendered global OSINT report as an HTML string.

        Expected data structure:
        {
            "company_name": str,
            "company_profile": dict (optional),
            "tech_stack": dict (optional),
            "web_presence": dict (optional),
            "hr_intelligence": dict (optional),
            "legal_analysis": dict (optional),
            "geospatial_analysis": dict (optional),
            "cross_reference": dict (optional),
        }
        """
        soup = self.create_soup("div", class_="osint-global-report")
        container = soup.div

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_table_of_contents(soup, container, data)
        self._add_executive_summary(soup, container, data)

        # Render each sub-report section
        self._add_company_profile_section(soup, container, data.get("company_profile"))
        self._add_tech_stack_section(soup, container, data.get("tech_stack"))
        self._add_web_presence_section(soup, container, data.get("web_presence"))
        self._add_hr_intelligence_section(soup, container, data.get("hr_intelligence"))
        self._add_legal_analysis_section(soup, container, data.get("legal_analysis"))
        self._add_geospatial_section(soup, container, data.get("geospatial_analysis"))
        self._add_cross_reference_section(soup, container, data.get("cross_reference"))

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h1")
        title.string = "Rapport OSINT Complet"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _add_table_of_contents(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        toc = soup.new_tag("nav", **{"class": "table-of-contents"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "Table des Matieres"
        toc.append(title)

        sections = [
            ("executive-summary", "Resume Executif"),
            ("company-profile", "Profil de l'Entreprise"),
            ("tech-stack", "Stack Technologique"),
            ("web-presence", "Presence Web"),
            ("hr-intelligence", "Intelligence RH"),
            ("legal-analysis", "Analyse Juridique"),
            ("geospatial", "Analyse Geospatiale"),
            ("cross-reference", "Rapport de Synthese"),
        ]

        ul = soup.new_tag("ul")
        for section_id, section_name in sections:
            # Check if section has data
            data_key = section_id.replace("-", "_")
            if data_key == "executive_summary" or data.get(data_key):
                li = soup.new_tag("li")
                link = soup.new_tag("a", href=f"#{section_id}")
                link.string = section_name
                li.append(link)
                ul.append(li)
        toc.append(ul)
        container.append(toc)

    @staticmethod
    def _add_executive_summary(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        section = soup.new_tag("section", **{"class": "report-section", "id": "executive-summary"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = "Resume Executif"
        section.append(title)

        # Count available reports
        reports = ["company_profile", "tech_stack", "web_presence", "hr_intelligence", "legal_analysis", "geospatial_analysis", "cross_reference"]
        available = sum(1 for r in reports if data.get(r))

        summary_div = soup.new_tag("div", **{"class": "summary-stats"})  # type: ignore[arg-type]

        # Company name
        if company := data.get("company_name"):
            p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Entreprise: "
            p.append(strong)
            p.append(company)
            summary_div.append(p)

        # Report count
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Rapports disponibles: "
        p.append(strong)
        p.append(f"{available} sur 7")
        summary_div.append(p)

        section.append(summary_div)
        container.append(section)

    def _add_company_profile_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "company-profile", "Profil de l'Entreprise", CompanyProfilerRenderer()
        )

    def _add_tech_stack_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "tech-stack", "Stack Technologique", TechStackRenderer()
        )

    def _add_web_presence_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "web-presence", "Presence Web", WebPresenceRenderer()
        )

    def _add_hr_intelligence_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "hr-intelligence", "Intelligence RH", HRIntelligenceRenderer()
        )

    def _add_legal_analysis_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "legal-analysis", "Analyse Juridique", LegalAnalysisRenderer()
        )

    def _add_geospatial_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "geospatial", "Analyse Geospatiale", GeospatialAnalysisRenderer()
        )

    def _add_cross_reference_section(self, soup: BeautifulSoup, container: Any, data: dict[str, Any] | None) -> None:
        if not data:
            return
        self._add_sub_report_section(
            soup, container, data, "cross-reference", "Rapport de Synthese", CrossReferenceReportRenderer()
        )

    def _add_sub_report_section(
        self,
        soup: BeautifulSoup,
        container: Any,
        data: dict[str, Any],
        section_id: str,
        section_title: str,
        renderer: BaseRenderer,
    ) -> None:
        """Add a sub-report section using the appropriate renderer."""
        section = soup.new_tag("section", **{"class": "sub-report-section", "id": section_id})  # type: ignore[arg-type]

        # Section header with navigation
        header = soup.new_tag("div", **{"class": "section-header"})  # type: ignore[arg-type]
        title = soup.new_tag("h2")
        title.string = section_title
        header.append(title)
        back_link = soup.new_tag("a", href="#table-of-contents", **{"class": "back-to-top"})  # type: ignore[arg-type]
        back_link.string = "Retour au sommaire"
        header.append(back_link)
        section.append(header)

        # Render the sub-report content
        try:
            sub_content_html = renderer.render(data)
            # Parse the sub-content and extract just the inner content
            sub_soup = BeautifulSoup(sub_content_html, "html.parser")
            # Find the main container and append its children
            main_div = sub_soup.find("div")
            if main_div:
                # Clone the children to avoid modifying the original
                for child in list(main_div.children):
                    # Skip the style tag as we have our own global styles
                    if getattr(child, "name", None) != "style":
                        section.append(child)
        except Exception:
            error_p = soup.new_tag("p", **{"class": "error"})  # type: ignore[arg-type]
            error_p.string = f"Erreur lors du rendu de la section {section_title}"
            section.append(error_p)

        # Add collapsible raw JSON
        details = soup.new_tag("details", **{"class": "raw-data"})  # type: ignore[arg-type]
        summary = soup.new_tag("summary")
        summary.string = f"Donnees brutes - {section_title}"
        details.append(summary)
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        section.append(details)

        container.append(section)

    @staticmethod
    def _add_styles(soup: BeautifulSoup) -> None:
        style = soup.new_tag("style")
        style.string = """
            .osint-global-report {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 1200px;
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
                border-bottom: 2px solid var(--border-color, #3b82f6);
                padding-bottom: 1.5rem;
            }
            .report-header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                color: var(--header-color, #111827);
                margin: 0 0 0.5rem 0;
            }
            .report-header h2 {
                font-size: 1.5rem;
                font-weight: 500;
                color: var(--subheader-color, #3b82f6);
                margin: 0;
            }
            .table-of-contents {
                background: var(--toc-bg, #f8fafc);
                border: 1px solid var(--border-color, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 2rem;
            }
            .table-of-contents h2 {
                font-size: 1.25rem;
                margin: 0 0 1rem 0;
                color: var(--header-color, #111827);
            }
            .table-of-contents ul {
                margin: 0;
                padding: 0;
                list-style: none;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 0.5rem;
            }
            .table-of-contents a {
                color: var(--link-color, #3b82f6);
                text-decoration: none;
                padding: 0.5rem;
                display: block;
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            .table-of-contents a:hover {
                background-color: var(--hover-bg, #e5e7eb);
            }
            .report-section, .sub-report-section {
                margin-bottom: 3rem;
                padding-bottom: 2rem;
                border-bottom: 1px solid var(--border-color, #e5e7eb);
            }
            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid var(--accent-color, #3b82f6);
            }
            .section-header h2 {
                font-size: 1.75rem;
                font-weight: 600;
                color: var(--header-color, #111827);
                margin: 0;
            }
            .back-to-top {
                font-size: 0.875rem;
                color: var(--link-color, #3b82f6);
                text-decoration: none;
            }
            .back-to-top:hover {
                text-decoration: underline;
            }
            .summary-stats {
                background: var(--stats-bg, #f0f9ff);
                border: 1px solid var(--stats-border, #3b82f6);
                border-radius: 8px;
                padding: 1.5rem;
            }
            .summary-stats p {
                margin: 0.5rem 0;
            }
            .raw-data {
                margin-top: 2rem;
                border-top: 1px solid var(--border-color, #e5e7eb);
                padding-top: 1rem;
            }
            .raw-data summary {
                cursor: pointer;
                font-weight: 500;
                color: var(--summary-color, #6b7280);
                font-size: 0.875rem;
            }
            .raw-data pre {
                background: var(--pre-bg, #f3f4f6);
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
                margin-top: 0.5rem;
                font-size: 0.75rem;
            }
            .error {
                color: var(--error-color, #dc2626);
                background: var(--error-bg, #fef2f2);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid var(--error-border, #fecaca);
            }
            @media (prefers-color-scheme: dark) {
                .osint-global-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .report-header h1, .section-header h2 {
                    color: #f9fafb;
                }
                .table-of-contents, .summary-stats {
                    background: #374151;
                    border-color: #4b5563;
                }
                .raw-data pre {
                    background: #374151;
                }
            }
            @media print {
                .back-to-top, .table-of-contents {
                    display: none;
                }
                .osint-global-report {
                    max-width: 100%;
                    box-shadow: none;
                }
            }
        """
        soup.append(style)
