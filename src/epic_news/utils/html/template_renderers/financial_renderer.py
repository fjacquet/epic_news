"""
Financial Renderer

Renders financial report data to structured HTML using BeautifulSoup.
Handles financial metrics, analysis, and recommendations.
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

        # Add key metrics
        self._add_key_metrics(soup, container, data)

        # Add analysis sections
        self._add_analysis_sections(soup, container, data)

        # Add recommendations
        self._add_recommendations(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add financial report header."""
        header_div = soup.new_tag("div", class_="financial-header")

        title_tag = soup.new_tag("h2")
        title_tag.string = "💰 Rapport Financier"
        header_div.append(title_tag)

        # Add date if available
        date = data.get("date") or data.get("report_date")
        if date:
            date_p = soup.new_tag("p", class_="report-date")
            date_p.string = f"📅 {date}"
            header_div.append(date_p)

        container.append(header_div)

    def _add_executive_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add executive summary section."""
        summary = data.get("executive_summary") or data.get("summary")
        if not summary:
            return

        summary_div = soup.new_tag("div", class_="executive-summary")

        title_tag = soup.new_tag("h3")
        title_tag.string = "📋 Résumé Exécutif"
        summary_div.append(title_tag)

        summary_p = soup.new_tag("p")
        summary_p.string = summary
        summary_div.append(summary_p)

        container.append(summary_div)

    def _add_key_metrics(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add key financial metrics."""
        metrics = data.get("key_metrics") or data.get("metrics")
        if not metrics:
            return

        metrics_div = soup.new_tag("div", class_="key-metrics")

        title_tag = soup.new_tag("h3")
        title_tag.string = "📊 Métriques Clés"
        metrics_div.append(title_tag)

        metrics_grid = soup.new_tag("div", class_="metrics-grid")

        if isinstance(metrics, dict):
            for metric_name, metric_value in metrics.items():
                metric_card = soup.new_tag("div", class_="metric-card")

                metric_title = soup.new_tag("h4")
                metric_title.string = metric_name.replace("_", " ").title()
                metric_card.append(metric_title)

                metric_val = soup.new_tag("p", class_="metric-value")
                metric_val.string = str(metric_value)
                metric_card.append(metric_val)

                metrics_grid.append(metric_card)

        if metrics_grid.find_all():
            metrics_div.append(metrics_grid)
            container.append(metrics_div)

    def _add_analysis_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add analysis sections, supporting both 'analysis' and 'analyses' fields."""
        # Support both singular and plural fields
        analysis = data.get("analysis") or data.get("detailed_analysis")
        analyses = data.get("analyses")
        if not analysis and not analyses:
            return

        analysis_div = soup.new_tag("div", class_="financial-analysis")

        title_tag = soup.new_tag("h3")
        title_tag.string = "🔍 Analyse Détaillée"
        analysis_div.append(title_tag)

        # Old format: string or list of dicts
        if analysis:
            if isinstance(analysis, str):
                analysis_p = soup.new_tag("p")
                analysis_p.string = analysis
                analysis_div.append(analysis_p)
            elif isinstance(analysis, list):
                for item in analysis:
                    if isinstance(item, dict):
                        section_div = soup.new_tag("div", class_="analysis-section")
                        section_title = item.get("title") or item.get("category")
                        if section_title:
                            section_h4 = soup.new_tag("h4")
                            section_h4.string = section_title
                            section_div.append(section_h4)
                        section_content = item.get("content") or item.get("description")
                        if section_content:
                            section_p = soup.new_tag("p")
                            section_p.string = section_content
                            section_div.append(section_p)
                        analysis_div.append(section_div)
        # New format: list of analyses (each with asset_class, summary, details)
        if analyses:
            for item in analyses:
                if isinstance(item, dict):
                    section_div = soup.new_tag("div", class_="analysis-section")
                    asset_class = item.get("asset_class")
                    summary = item.get("summary")
                    details = item.get("details")
                    if asset_class:
                        section_h4 = soup.new_tag("h4")
                        section_h4.string = f"{asset_class}"
                        section_div.append(section_h4)
                    if summary:
                        summary_p = soup.new_tag("p")
                        summary_p.string = summary
                        section_div.append(summary_p)
                    if details and isinstance(details, list):
                        details_ul = soup.new_tag("ul")
                        for detail in details:
                            li = soup.new_tag("li")
                            li.string = str(detail)
                            details_ul.append(li)
                        section_div.append(details_ul)
                    analysis_div.append(section_div)

        if analysis_div.find_all("p") or analysis_div.find_all("div"):
            container.append(analysis_div)

    def _add_recommendations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recommendations section, supporting both 'recommendations' and 'suggestions'."""
        recommendations = data.get("recommendations") or data.get("advice")
        suggestions = data.get("suggestions")
        if not recommendations and not suggestions:
            return

        rec_div = soup.new_tag("div", class_="recommendations")

        title_tag = soup.new_tag("h3")
        title_tag.string = "💡 Recommandations"
        rec_div.append(title_tag)

        # Old format: list or string
        if recommendations:
            if isinstance(recommendations, list):
                rec_ul = soup.new_tag("ul", class_="recommendations-list")
                for rec in recommendations:
                    li = soup.new_tag("li")
                    if isinstance(rec, dict):
                        rec_text = rec.get("text") or rec.get("recommendation") or str(rec)
                    else:
                        rec_text = str(rec)
                    li.string = rec_text
                    rec_ul.append(li)
                rec_div.append(rec_ul)
            elif isinstance(recommendations, str):
                rec_p = soup.new_tag("p")
                rec_p.string = recommendations
                rec_div.append(rec_p)
        # New format: suggestions (each with asset_class, suggestion, rationale)
        if suggestions:
            sugg_ul = soup.new_tag("ul", class_="recommendations-list")
            for sugg in suggestions:
                if isinstance(sugg, dict):
                    li = soup.new_tag("li")
                    asset_class = sugg.get("asset_class")
                    suggestion = sugg.get("suggestion")
                    rationale = sugg.get("rationale")
                    li_content = ""
                    if asset_class:
                        li_content += f"[{asset_class}] "
                    if suggestion:
                        li_content += suggestion
                    if rationale:
                        li_content += f"\n→ {rationale}"
                    li.string = li_content
                    sugg_ul.append(li)
            rec_div.append(sugg_ul)

        if rec_div.find_all():
            container.append(rec_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for financial report formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .financial-report {
            max-width: 900px;
            margin: 0 auto;
        }
        .financial-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .financial-header h2 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }
        .report-date {
            color: var(--text-color);
            font-size: 1.1rem;
            margin: 0;
        }
        .executive-summary, .key-metrics, .financial-analysis, .recommendations {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .executive-summary h3, .key-metrics h3, .financial-analysis h3, .recommendations h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .metric-card {
            padding: 1rem;
            background: rgba(0, 123, 179, 0.1);
            border-radius: 6px;
            text-align: center;
        }
        .metric-card h4 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        .metric-value {
            color: var(--text-color);
            font-size: 1.2rem;
            font-weight: bold;
            margin: 0;
        }
        .analysis-section {
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(108, 117, 125, 0.1);
            border-radius: 6px;
            border-left: 4px solid var(--heading-color);
        }
        .analysis-section h4 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .analysis-section p {
            color: var(--text-color);
            line-height: 1.5;
            margin: 0;
        }
        .recommendations-list {
            list-style: none;
            padding: 0;
        }
        .recommendations-list li {
            margin: 0.5rem 0;
            padding: 0.75rem;
            background: rgba(40, 167, 69, 0.1);
            border-radius: 4px;
            border-left: 3px solid #28a745;
            color: var(--text-color);
        }
        """
        soup.append(style_tag)
