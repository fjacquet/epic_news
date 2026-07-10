"""
Financial Renderer

Renders financial report data to structured HTML using BeautifulSoup.

The renderer consumes exactly the ``FinancialReport`` model contract
(``title``, ``executive_summary``, ``analyses``, ``suggestions``,
``report_date``). Data always reaches it as ``FinancialReport.model_dump()``
via ``TemplateManager`` (the legacy fallback path also runs
``FinancialReport.model_validate`` first, which drops unknown keys), so
free-form legacy keys never appear and are not handled here.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class FinancialRenderer(BaseRenderer):
    """Renders financial report content with structured formatting."""

    def __init__(self):
        """Initialize the financial renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """
        Render financial report data to HTML.

        Args:
            data: Dictionary containing financial report data

        Returns:
            HTML string for financial report content
        """
        # Create main container
        soup = self.create_soup("div", class_="financial-report")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add executive summary
        self._add_executive_summary(soup, container, data)

        # Add analysis sections
        self._add_analysis_sections(soup, container, data)

        # Add recommendations
        self._add_recommendations(soup, container, data)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add financial report header."""
        header_div = soup.new_tag("div", attrs={"class": "financial-header"})

        title_tag = soup.new_tag("h2")
        title = data.get("title")
        if title:
            title_tag.append("💰 ")
            self.render_markdown_inline(title_tag, title)
        else:
            title_tag.string = "💰 Rapport Financier"
        header_div.append(title_tag)

        # Add date if available
        date = data.get("report_date")
        if date:
            date_p = soup.new_tag("p", attrs={"class": "report-date"})
            date_p.string = f"📅 {date}"
            header_div.append(date_p)

        container.append(header_div)

    def _add_executive_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add executive summary section."""
        summary = data.get("executive_summary")
        if not summary:
            return

        summary_div = soup.new_tag("div", attrs={"class": "executive-summary"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "📋 Résumé Exécutif"
        summary_div.append(title_tag)

        summary_p = soup.new_tag("p")
        self.render_markdown_inline(summary_p, summary)
        summary_div.append(summary_p)

        container.append(summary_div)

    def _add_analysis_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the detailed analysis section from the ``analyses`` field.

        Each analysis is an ``AssetAnalysis`` (``asset_class``, ``summary``,
        ``details``). The whole section -- title included -- is skipped when
        there is no renderable analysis (empty list or no dict items).
        """
        analyses = data.get("analyses")
        if not (isinstance(analyses, list) and any(isinstance(item, dict) for item in analyses)):
            return

        analysis_div = soup.new_tag("div", attrs={"class": "financial-analysis"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "🔍 Analyse Détaillée"
        analysis_div.append(title_tag)

        for item in analyses:
            if not isinstance(item, dict):
                continue
            section_div = soup.new_tag("div", attrs={"class": "analysis-section"})
            asset_class = item.get("asset_class")
            summary = item.get("summary")
            details = item.get("details")
            if asset_class:
                section_h4 = soup.new_tag("h4")
                self.render_markdown_inline(section_h4, asset_class)
                section_div.append(section_h4)
            if summary:
                summary_p = soup.new_tag("p")
                self.render_markdown_inline(summary_p, summary)
                section_div.append(summary_p)
            if details and isinstance(details, list):
                details_ul = soup.new_tag("ul")
                for detail in details:
                    li = soup.new_tag("li")
                    self.append_prose(li, detail)
                    details_ul.append(li)
                section_div.append(details_ul)
            analysis_div.append(section_div)

        container.append(analysis_div)

    def _add_recommendations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the recommendations section from the ``suggestions`` field.

        Each suggestion is an ``AssetSuggestion`` (``asset_class``,
        ``suggestion``, ``rationale``). The whole section is skipped when there
        are no suggestions.
        """
        suggestions = data.get("suggestions")
        if not suggestions:
            return

        rec_div = soup.new_tag("div", attrs={"class": "recommendations"})

        title_tag = soup.new_tag("h3")
        title_tag.string = "💡 Recommandations"
        rec_div.append(title_tag)

        sugg_ul = soup.new_tag("ul", attrs={"class": "recommendations-list"})
        for sugg in suggestions:
            if not isinstance(sugg, dict):
                continue
            li = soup.new_tag("li")
            asset_class = sugg.get("asset_class")
            suggestion = sugg.get("suggestion")
            rationale = sugg.get("rationale")
            if asset_class:
                li.append(f"[{asset_class}] ")
            if suggestion:
                self.render_markdown_inline(li, suggestion)
            if rationale:
                li.append(" → ")
                self.render_markdown_inline(li, rationale)
            sugg_ul.append(li)
        rec_div.append(sugg_ul)

        container.append(rec_div)
