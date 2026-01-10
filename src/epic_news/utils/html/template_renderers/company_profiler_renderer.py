"""Company Profiler Renderer

Converts validated company profile data into a professional French HTML report.
Follows output-standards with strategic emoji usage and proper sections.

Sections rendered:
1. Header with company name
2. Informations Clés (Core Info)
3. Histoire de l'Entreprise (History)
4. Analyse Financière (Financials)
5. Position sur le Marché (Market Position)
6. Produits et Services (Products & Services)
7. Direction et Gouvernance (Management)
8. Conformité Légale (Legal Compliance)
9. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class CompanyProfilerRenderer(BaseRenderer):
    """Render a company profile report into a professional French HTML fragment."""

    def __init__(self) -> None:
        """Initialize the company profiler renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="company-profiler-report")
        container = soup.div

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_core_info(soup, container, data)
        self._add_history(soup, container, data)
        self._add_financials(soup, container, data)
        self._add_market_position(soup, container, data)
        self._add_products_services(soup, container, data)
        self._add_management(soup, container, data)
        self._add_legal_compliance(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add report header with company name."""
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]

        h1 = soup.new_tag("h1")
        h1.string = "🏢 Profil d'Entreprise"
        header.append(h1)

        company_name = data.get("company_name", "Entreprise")
        subtitle = soup.new_tag("p", **{"class": "company-name"})  # type: ignore[arg-type]
        subtitle.string = company_name
        header.append(subtitle)

        container.append(header)

    @staticmethod
    def _add_core_info(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add core company information section."""
        core_info = data.get("core_info", {})
        if not core_info:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "📋 Informations Clés"
        section.append(h2)

        # Info grid
        grid = soup.new_tag("div", **{"class": "info-grid"})  # type: ignore[arg-type]

        info_items = [
            ("Nom légal", core_info.get("legal_name")),
            ("Société mère", core_info.get("parent_company")),
            ("Année de création", core_info.get("year_founded")),
            ("Siège social", core_info.get("headquarters_location")),
            ("Secteur d'activité", core_info.get("industry_classification")),
            ("Nombre d'employés", core_info.get("employee_count")),
            ("Chiffre d'affaires", CompanyProfilerRenderer._format_currency(core_info.get("revenue"))),
            ("Capitalisation boursière", CompanyProfilerRenderer._format_currency(core_info.get("market_cap"))),
        ]

        for label, value in info_items:
            if value:
                item = soup.new_tag("div", **{"class": "info-item"})  # type: ignore[arg-type]
                label_tag = soup.new_tag("span", **{"class": "info-label"})  # type: ignore[arg-type]
                label_tag.string = label
                value_tag = soup.new_tag("span", **{"class": "info-value"})  # type: ignore[arg-type]
                value_tag.string = str(value)
                item.append(label_tag)
                item.append(value_tag)
                grid.append(item)

        section.append(grid)

        # Business activities
        activities = core_info.get("business_activities", [])
        if activities:
            activities_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Activités principales"
            activities_div.append(h3)
            ul = soup.new_tag("ul")
            for activity in activities:
                li = soup.new_tag("li")
                li.string = activity
                ul.append(li)
            activities_div.append(ul)
            section.append(activities_div)

        # Mission statement
        if mission := core_info.get("mission_statement"):
            mission_div = soup.new_tag("div", **{"class": "highlight-box"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🎯 Mission"
            mission_div.append(h3)
            p = soup.new_tag("p")
            p.string = mission
            mission_div.append(p)
            section.append(mission_div)

        # Core values
        values = core_info.get("core_values", [])
        if values:
            values_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Valeurs fondamentales"
            values_div.append(h3)
            tags_div = soup.new_tag("div", **{"class": "tags"})  # type: ignore[arg-type]
            for value in values:
                tag = soup.new_tag("span", **{"class": "tag"})  # type: ignore[arg-type]
                tag.string = value
                tags_div.append(tag)
            values_div.append(tags_div)
            section.append(values_div)

        container.append(section)

    @staticmethod
    def _add_history(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add company history section."""
        history = data.get("history", {})
        if not history:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "📜 Histoire de l'Entreprise"
        section.append(h2)

        # Founding story
        if founding := history.get("founding_story"):
            founding_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Origine"
            founding_div.append(h3)
            p = soup.new_tag("p")
            p.string = founding
            founding_div.append(p)
            section.append(founding_div)

        # Key milestones
        milestones = history.get("key_milestones", [])
        if milestones:
            milestones_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "📈 Jalons importants"
            milestones_div.append(h3)
            ul = soup.new_tag("ul", **{"class": "timeline"})  # type: ignore[arg-type]
            for milestone in milestones:
                li = soup.new_tag("li")
                li.string = milestone
                ul.append(li)
            milestones_div.append(ul)
            section.append(milestones_div)

        # Acquisitions
        acquisitions = history.get("acquisitions_and_mergers", [])
        if acquisitions:
            acq_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🤝 Acquisitions et fusions"
            acq_div.append(h3)
            for acq in acquisitions:
                if isinstance(acq, dict):
                    card = soup.new_tag("div", **{"class": "card"})  # type: ignore[arg-type]
                    for key, val in acq.items():
                        p = soup.new_tag("p")
                        p.string = f"{key}: {val}"
                        card.append(p)
                    acq_div.append(card)
                else:
                    p = soup.new_tag("p")
                    p.string = str(acq)
                    acq_div.append(p)
            section.append(acq_div)

        container.append(section)

    @staticmethod
    def _add_financials(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add financial analysis section."""
        financials = data.get("financials", {})
        if not financials:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "💰 Analyse Financière"
        section.append(h2)

        # Revenue trends
        trends = financials.get("revenue_and_profit_trends", [])
        if trends:
            trends_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "📊 Tendances des revenus et profits"
            trends_div.append(h3)

            table = soup.new_tag("table", **{"class": "data-table"})  # type: ignore[arg-type]
            # Extract headers from first item
            if trends and isinstance(trends[0], dict):
                thead = soup.new_tag("thead")
                tr = soup.new_tag("tr")
                for key in trends[0]:
                    th = soup.new_tag("th")
                    th.string = str(key).replace("_", " ").title()
                    tr.append(th)
                thead.append(tr)
                table.append(thead)

                tbody = soup.new_tag("tbody")
                for trend in trends:
                    tr = soup.new_tag("tr")
                    for val in trend.values():
                        td = soup.new_tag("td")
                        td.string = str(val) if val is not None else "N/A"
                        tr.append(td)
                    tbody.append(tr)
                table.append(tbody)
            trends_div.append(table)
            section.append(trends_div)

        # Key ratios
        ratios = financials.get("key_financial_ratios", {})
        if ratios:
            ratios_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "📈 Ratios financiers clés"
            ratios_div.append(h3)

            grid = soup.new_tag("div", **{"class": "metrics-grid"})  # type: ignore[arg-type]
            for name, value in ratios.items():
                metric = soup.new_tag("div", **{"class": "metric-card"})  # type: ignore[arg-type]
                label = soup.new_tag("span", **{"class": "metric-label"})  # type: ignore[arg-type]
                label.string = name.replace("_", " ").title()
                val_span = soup.new_tag("span", **{"class": "metric-value"})  # type: ignore[arg-type]
                val_span.string = str(value)
                metric.append(label)
                metric.append(val_span)
                grid.append(metric)
            ratios_div.append(grid)
            section.append(ratios_div)

        # Debt structure
        debt = financials.get("debt_structure")
        if debt:
            debt_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "💳 Structure de la dette"
            debt_div.append(h3)
            if isinstance(debt, dict):
                grid = soup.new_tag("div", **{"class": "info-grid"})  # type: ignore[arg-type]
                for key, val in debt.items():
                    item = soup.new_tag("div", **{"class": "info-item"})  # type: ignore[arg-type]
                    label_tag = soup.new_tag("span", **{"class": "info-label"})  # type: ignore[arg-type]
                    label_tag.string = key.replace("_", " ").title()
                    value_tag = soup.new_tag("span", **{"class": "info-value"})  # type: ignore[arg-type]
                    value_tag.string = str(val)
                    item.append(label_tag)
                    item.append(value_tag)
                    grid.append(item)
                debt_div.append(grid)
            else:
                p = soup.new_tag("p")
                p.string = str(debt)
                debt_div.append(p)
            section.append(debt_div)

        # Major investors
        investors = financials.get("major_investors", [])
        if investors:
            inv_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🏦 Investisseurs majeurs"
            inv_div.append(h3)
            tags_div = soup.new_tag("div", **{"class": "tags"})  # type: ignore[arg-type]
            for investor in investors:
                tag = soup.new_tag("span", **{"class": "tag investor"})  # type: ignore[arg-type]
                tag.string = investor
                tags_div.append(tag)
            inv_div.append(tags_div)
            section.append(inv_div)

        container.append(section)

    @staticmethod
    def _add_market_position(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add market position section."""
        market = data.get("market_position", {})
        if not market:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "🎯 Position sur le Marché"
        section.append(h2)

        # Market share
        if share := market.get("market_share"):
            share_div = soup.new_tag("div", **{"class": "highlight-box success"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Part de marché"
            share_div.append(h3)
            p = soup.new_tag("p", **{"class": "big-number"})  # type: ignore[arg-type]
            p.string = share
            share_div.append(p)
            section.append(share_div)

        # Competitive landscape
        if landscape := market.get("competitive_landscape"):
            landscape_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🔍 Paysage concurrentiel"
            landscape_div.append(h3)
            p = soup.new_tag("p")
            p.string = landscape
            landscape_div.append(p)
            section.append(landscape_div)

        # Key competitors
        competitors = market.get("key_competitors", [])
        if competitors:
            comp_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "⚔️ Concurrents principaux"
            comp_div.append(h3)
            tags_div = soup.new_tag("div", **{"class": "tags"})  # type: ignore[arg-type]
            for competitor in competitors:
                tag = soup.new_tag("span", **{"class": "tag competitor"})  # type: ignore[arg-type]
                tag.string = competitor
                tags_div.append(tag)
            comp_div.append(tags_div)
            section.append(comp_div)

        # Comparative advantages
        advantages = market.get("comparative_advantages", [])
        if advantages:
            adv_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "✅ Avantages compétitifs"
            adv_div.append(h3)
            ul = soup.new_tag("ul", **{"class": "advantages-list"})  # type: ignore[arg-type]
            for adv in advantages:
                li = soup.new_tag("li")
                li.string = adv
                ul.append(li)
            adv_div.append(ul)
            section.append(adv_div)

        # Growth opportunities
        opportunities = market.get("growth_opportunities", [])
        if opportunities:
            opp_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🚀 Opportunités de croissance"
            opp_div.append(h3)
            ul = soup.new_tag("ul")
            for opp in opportunities:
                li = soup.new_tag("li")
                li.string = opp
                ul.append(li)
            opp_div.append(ul)
            section.append(opp_div)

        # Challenges
        challenges = market.get("challenges", [])
        if challenges:
            chal_div = soup.new_tag("div", **{"class": "subsection warning"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "⚠️ Défis"
            chal_div.append(h3)
            ul = soup.new_tag("ul")
            for challenge in challenges:
                li = soup.new_tag("li")
                li.string = challenge
                ul.append(li)
            chal_div.append(ul)
            section.append(chal_div)

        container.append(section)

    @staticmethod
    def _add_products_services(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add products and services section."""
        products = data.get("products_and_services", {})
        if not products:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "📦 Produits et Services"
        section.append(h2)

        # Core product lines
        core_products = products.get("core_product_lines", [])
        if core_products:
            core_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Lignes de produits principales"
            core_div.append(h3)
            ul = soup.new_tag("ul")
            for product in core_products:
                li = soup.new_tag("li")
                li.string = product
                ul.append(li)
            core_div.append(ul)
            section.append(core_div)

        # Recent launches
        launches = products.get("recent_launches", [])
        if launches:
            launch_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🆕 Lancements récents"
            launch_div.append(h3)
            tags_div = soup.new_tag("div", **{"class": "tags"})  # type: ignore[arg-type]
            for launch in launches:
                tag = soup.new_tag("span", **{"class": "tag new"})  # type: ignore[arg-type]
                tag.string = launch
                tags_div.append(tag)
            launch_div.append(tags_div)
            section.append(launch_div)

        # Pricing strategy
        if pricing := products.get("pricing_strategy"):
            pricing_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "💵 Stratégie de prix"
            pricing_div.append(h3)
            p = soup.new_tag("p")
            p.string = pricing
            pricing_div.append(p)
            section.append(pricing_div)

        # Customer segments
        segments = products.get("customer_segments", [])
        if segments:
            seg_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "👥 Segments de clientèle"
            seg_div.append(h3)
            tags_div = soup.new_tag("div", **{"class": "tags"})  # type: ignore[arg-type]
            for segment in segments:
                tag = soup.new_tag("span", **{"class": "tag segment"})  # type: ignore[arg-type]
                tag.string = segment
                tags_div.append(tag)
            seg_div.append(tags_div)
            section.append(seg_div)

        container.append(section)

    @staticmethod
    def _add_management(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add management section."""
        management = data.get("management", {})
        if not management:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "👔 Direction et Gouvernance"
        section.append(h2)

        # Key executives
        executives = management.get("key_executives", [])
        if executives:
            exec_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Équipe de direction"
            exec_div.append(h3)

            grid = soup.new_tag("div", **{"class": "executives-grid"})  # type: ignore[arg-type]
            for exec_info in executives:
                if isinstance(exec_info, dict):
                    card = soup.new_tag("div", **{"class": "executive-card"})  # type: ignore[arg-type]
                    name = exec_info.get("name", exec_info.get("nom", "N/A"))
                    role = exec_info.get("role", exec_info.get("position", exec_info.get("titre", "")))

                    name_tag = soup.new_tag("h4")
                    name_tag.string = str(name)
                    card.append(name_tag)

                    if role:
                        role_tag = soup.new_tag("p", **{"class": "role"})  # type: ignore[arg-type]
                        role_tag.string = str(role)
                        card.append(role_tag)

                    grid.append(card)
            exec_div.append(grid)
            section.append(exec_div)

        # Board of directors
        board = management.get("board_of_directors", [])
        if board:
            board_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Conseil d'administration"
            board_div.append(h3)
            ul = soup.new_tag("ul")
            for member in board:
                li = soup.new_tag("li")
                li.string = member
                ul.append(li)
            board_div.append(ul)
            section.append(board_div)

        # Corporate culture
        if culture := management.get("corporate_culture"):
            culture_div = soup.new_tag("div", **{"class": "highlight-box"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "🌟 Culture d'entreprise"
            culture_div.append(h3)
            p = soup.new_tag("p")
            p.string = culture
            culture_div.append(p)
            section.append(culture_div)

        container.append(section)

    @staticmethod
    def _add_legal_compliance(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add legal compliance section."""
        legal = data.get("legal_compliance", {})
        if not legal:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]

        h2 = soup.new_tag("h2")
        h2.string = "⚖️ Conformité Légale"
        section.append(h2)

        # Regulatory framework
        if framework := legal.get("regulatory_framework"):
            framework_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Cadre réglementaire"
            framework_div.append(h3)
            p = soup.new_tag("p")
            p.string = framework
            framework_div.append(p)
            section.append(framework_div)

        # Compliance history
        history = legal.get("compliance_history", [])
        if history:
            hist_div = soup.new_tag("div", **{"class": "subsection"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "Historique de conformité"
            hist_div.append(h3)
            ul = soup.new_tag("ul")
            for item in history:
                li = soup.new_tag("li")
                li.string = item
                ul.append(li)
            hist_div.append(ul)
            section.append(hist_div)

        # Ongoing litigation
        litigation = legal.get("ongoing_litigation", [])
        if litigation:
            lit_div = soup.new_tag("div", **{"class": "subsection warning"})  # type: ignore[arg-type]
            h3 = soup.new_tag("h3")
            h3.string = "⚠️ Litiges en cours"
            lit_div.append(h3)
            ul = soup.new_tag("ul")
            for item in litigation:
                li = soup.new_tag("li")
                li.string = item
                ul.append(li)
            lit_div.append(ul)
            section.append(lit_div)

        container.append(section)

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Add collapsible raw JSON data for debugging."""
        details = soup.new_tag("details", **{"class": "raw-data"})  # type: ignore[arg-type]
        summary = soup.new_tag("summary")
        summary.string = "📄 Voir les données brutes"
        details.append(summary)
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        container.append(details)

    @staticmethod
    def _format_currency(value: float | int | None) -> str | None:
        """Format currency value with proper notation."""
        if value is None:
            return None
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f} Mrd €"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f} M€"
        if value >= 1_000:
            return f"{value / 1_000:.1f} k€"
        return f"{value:.0f} €"

    @staticmethod
    def _add_styles(soup: BeautifulSoup) -> None:
        """Add CSS styles for the report."""
        style = soup.new_tag("style")
        style.string = """
            :root {
                --primary-color: #2563eb;
                --success-color: #059669;
                --warning-color: #d97706;
                --danger-color: #dc2626;

                --background-light: #ffffff;
                --text-light: #1f2937;
                --text-secondary-light: #6b7280;
                --border-light: #e5e7eb;
                --card-bg-light: #f9fafb;

                --background-dark: #111827;
                --text-dark: #f3f4f6;
                --text-secondary-dark: #9ca3af;
                --border-dark: #374151;
                --card-bg-dark: #1f2937;
            }

            .company-profiler-report {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 900px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: var(--background-light);
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: var(--text-light);
            }

            .report-header {
                text-align: center;
                margin-bottom: 2.5rem;
                padding-bottom: 1.5rem;
                border-bottom: 2px solid var(--primary-color);
            }

            .report-header h1 {
                font-size: 2rem;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 0.5rem;
            }

            .report-header .company-name {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-light);
            }

            .report-section {
                margin-bottom: 2.5rem;
                padding-bottom: 1.5rem;
                border-bottom: 1px solid var(--border-light);
            }

            .report-section h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-light);
                margin-bottom: 1.5rem;
            }

            .subsection {
                margin-top: 1.5rem;
            }

            .subsection h3 {
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--text-light);
                margin-bottom: 0.75rem;
            }

            .subsection.warning {
                background-color: #fef3c7;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid var(--warning-color);
            }

            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }

            .info-item {
                display: flex;
                flex-direction: column;
                padding: 0.75rem;
                background-color: var(--card-bg-light);
                border-radius: 8px;
            }

            .info-label {
                font-size: 0.875rem;
                color: var(--text-secondary-light);
                margin-bottom: 0.25rem;
            }

            .info-value {
                font-weight: 600;
                color: var(--text-light);
            }

            .highlight-box {
                background-color: #eff6ff;
                padding: 1.25rem;
                border-radius: 8px;
                border-left: 4px solid var(--primary-color);
                margin-top: 1.5rem;
            }

            .highlight-box.success {
                background-color: #ecfdf5;
                border-left-color: var(--success-color);
            }

            .highlight-box h3 {
                margin-bottom: 0.5rem;
            }

            .big-number {
                font-size: 2rem;
                font-weight: 700;
                color: var(--success-color);
            }

            .tags {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }

            .tag {
                display: inline-block;
                padding: 0.375rem 0.75rem;
                background-color: #e0e7ff;
                color: #3730a3;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 500;
            }

            .tag.investor {
                background-color: #fef3c7;
                color: #92400e;
            }

            .tag.competitor {
                background-color: #fee2e2;
                color: #991b1b;
            }

            .tag.new {
                background-color: #d1fae5;
                color: #065f46;
            }

            .tag.segment {
                background-color: #e0e7ff;
                color: #3730a3;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
            }

            .metric-card {
                text-align: center;
                padding: 1rem;
                background-color: var(--card-bg-light);
                border-radius: 8px;
                border: 1px solid var(--border-light);
            }

            .metric-label {
                display: block;
                font-size: 0.75rem;
                color: var(--text-secondary-light);
                text-transform: uppercase;
                margin-bottom: 0.5rem;
            }

            .metric-value {
                font-size: 1.25rem;
                font-weight: 700;
                color: var(--primary-color);
            }

            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }

            .data-table th,
            .data-table td {
                padding: 0.75rem;
                text-align: left;
                border-bottom: 1px solid var(--border-light);
            }

            .data-table th {
                background-color: var(--card-bg-light);
                font-weight: 600;
                color: var(--text-light);
            }

            .executives-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }

            .executive-card {
                padding: 1rem;
                background-color: var(--card-bg-light);
                border-radius: 8px;
                border: 1px solid var(--border-light);
            }

            .executive-card h4 {
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }

            .executive-card .role {
                font-size: 0.875rem;
                color: var(--text-secondary-light);
            }

            .timeline {
                list-style: none;
                padding-left: 1.5rem;
                border-left: 2px solid var(--primary-color);
            }

            .timeline li {
                position: relative;
                padding-bottom: 1rem;
                padding-left: 1rem;
            }

            .timeline li::before {
                content: '';
                position: absolute;
                left: -0.5rem;
                top: 0.5rem;
                width: 0.5rem;
                height: 0.5rem;
                background-color: var(--primary-color);
                border-radius: 50%;
            }

            .advantages-list li {
                position: relative;
                padding-left: 1.5rem;
                margin-bottom: 0.5rem;
            }

            .advantages-list li::before {
                content: '✓';
                position: absolute;
                left: 0;
                color: var(--success-color);
                font-weight: bold;
            }

            .raw-data {
                margin-top: 2.5rem;
                padding-top: 1.5rem;
                border-top: 1px solid var(--border-light);
            }

            .raw-data summary {
                cursor: pointer;
                font-weight: 500;
                color: var(--text-secondary-light);
            }

            .raw-data pre {
                background-color: var(--card-bg-light);
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
                font-size: 0.75rem;
                margin-top: 1rem;
            }

            ul {
                padding-left: 1.5rem;
            }

            li {
                margin-bottom: 0.5rem;
                line-height: 1.6;
            }

            p {
                line-height: 1.6;
                margin-bottom: 0.75rem;
            }

            .card {
                padding: 1rem;
                background-color: var(--card-bg-light);
                border-radius: 8px;
                margin-bottom: 0.75rem;
            }

            @media (prefers-color-scheme: dark) {
                .company-profiler-report {
                    background-color: var(--background-dark);
                    color: var(--text-dark);
                }

                .report-header .company-name,
                .report-section h2,
                .subsection h3,
                .info-value,
                .executive-card h4,
                .data-table th {
                    color: var(--text-dark);
                }

                .info-label,
                .metric-label,
                .executive-card .role,
                .raw-data summary {
                    color: var(--text-secondary-dark);
                }

                .info-item,
                .metric-card,
                .executive-card,
                .data-table th,
                .raw-data pre,
                .card {
                    background-color: var(--card-bg-dark);
                    border-color: var(--border-dark);
                }

                .report-section,
                .raw-data,
                .data-table th,
                .data-table td {
                    border-color: var(--border-dark);
                }

                .highlight-box {
                    background-color: #1e3a5f;
                }

                .highlight-box.success {
                    background-color: #064e3b;
                }

                .subsection.warning {
                    background-color: #451a03;
                }

                .tag {
                    background-color: #312e81;
                    color: #c7d2fe;
                }

                .tag.investor {
                    background-color: #451a03;
                    color: #fde68a;
                }

                .tag.competitor {
                    background-color: #450a0a;
                    color: #fecaca;
                }

                .tag.new {
                    background-color: #064e3b;
                    color: #a7f3d0;
                }
            }
        """
        soup.append(style)
