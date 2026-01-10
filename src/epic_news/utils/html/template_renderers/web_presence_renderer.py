"""Web Presence Renderer

Converts validated web presence data into a visually appealing HTML fragment.
This renderer displays website analysis, social media footprint, technical
infrastructure, data leaks, and competitive analysis.

Sections rendered:
1. Header with company name
2. Executive Summary
3. Website Analysis
4. Social Media Footprint
5. Technical Infrastructure
6. Data Leak Analysis
7. Competitive Analysis
8. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class WebPresenceRenderer(BaseRenderer):
    """Render a web presence report into a modern HTML fragment."""

    def __init__(self) -> None:
        """Initialize the web presence renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore: Any, **__ignore: Any) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="web-presence-report")
        container = soup.div

        self._add_styles(soup)
        self._add_header(soup, container, data)
        self._add_executive_summary(soup, container, data)
        self._add_website_analysis(soup, container, data)
        self._add_social_media(soup, container, data)
        self._add_technical_infrastructure(soup, container, data)
        self._add_data_leaks(soup, container, data)
        self._add_competitive_analysis(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        header = soup.new_tag("div")
        header.attrs["class"] = "report-header"  # type: ignore[assignment]
        title = soup.new_tag("h1")
        title.string = "🌐 Analyse de Présence Web"
        header.append(title)
        if company := data.get("company_name"):
            subtitle = soup.new_tag("h2")
            subtitle.string = company
            header.append(subtitle)
        container.append(header)

    @staticmethod
    def _add_executive_summary(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        summary = data.get("executive_summary")
        if not summary:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "📋 Résumé Exécutif"
        section.append(title)
        para = soup.new_tag("p")
        para.string = summary
        section.append(para)
        container.append(section)

    @staticmethod
    def _add_website_analysis(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        website = data.get("website_analysis")
        if not website:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "🔍 Analyse du Site Web"
        section.append(title)

        card = soup.new_tag("div")
        card.attrs["class"] = "website-card"  # type: ignore[assignment]

        if domain := website.get("domain"):
            domain_p = soup.new_tag("p")
            domain_p.attrs["class"] = "domain"  # type: ignore[assignment]
            domain_p.string = f"Domaine: {domain}"
            card.append(domain_p)

        for field, label in [
            ("structure", "Structure"),
            ("content_quality", "Qualité du contenu"),
            ("seo", "SEO"),
        ]:
            if value := website.get(field):
                p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = f"{label}: "
                p.append(strong)
                p.append(value)
                card.append(p)

        if recs := website.get("recommendations", []):
            recs_div = soup.new_tag("div")
            recs_div.attrs["class"] = "recommendations"  # type: ignore[assignment]
            recs_title = soup.new_tag("h4")
            recs_title.string = "Recommandations"
            recs_div.append(recs_title)
            ul = soup.new_tag("ul")
            for rec in recs:
                li = soup.new_tag("li")
                li.string = rec
                ul.append(li)
            recs_div.append(ul)
            card.append(recs_div)

        section.append(card)
        container.append(section)

    @staticmethod
    def _add_social_media(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        socials = data.get("social_media_footprint", [])
        if not socials:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "📱 Empreinte Réseaux Sociaux"
        section.append(title)

        grid = soup.new_tag("div")
        grid.attrs["class"] = "social-grid"  # type: ignore[assignment]

        for social in socials:
            card = soup.new_tag("div")
            card.attrs["class"] = "social-card"  # type: ignore[assignment]

            platform = soup.new_tag("h3")
            platform.string = social.get("platform", "N/A")
            card.append(platform)

            if url := social.get("url"):
                link = soup.new_tag("a", href=url)
                link.attrs["target"] = "_blank"
                link.string = url
                card.append(link)

            stats = soup.new_tag("div")
            stats.attrs["class"] = "social-stats"  # type: ignore[assignment]

            if followers := social.get("followers"):
                f_span = soup.new_tag("span")
                f_span.string = f"👥 {followers:,} abonnés"
                stats.append(f_span)

            if engagement := social.get("engagement_rate"):
                e_span = soup.new_tag("span")
                e_span.string = f"📊 {engagement:.1%} engagement"
                stats.append(e_span)

            card.append(stats)

            if notes := social.get("notes"):
                notes_p = soup.new_tag("p")
                notes_p.attrs["class"] = "notes"  # type: ignore[assignment]
                notes_p.string = notes
                card.append(notes_p)

            grid.append(card)

        section.append(grid)
        container.append(section)

    @staticmethod
    def _add_technical_infrastructure(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        infra = data.get("technical_infrastructure")
        if not infra:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "🔧 Infrastructure Technique"
        section.append(title)

        table = soup.new_tag("table")
        table.attrs["class"] = "infra-table"  # type: ignore[assignment]

        for field, label in [
            ("hosting_provider", "Hébergeur"),
            ("dns_provider", "Fournisseur DNS"),
            ("cdn_provider", "CDN"),
            ("ssl_issuer", "Émetteur SSL"),
        ]:
            if value := infra.get(field):
                tr = soup.new_tag("tr")
                th = soup.new_tag("th")
                th.string = label
                td = soup.new_tag("td")
                td.string = value
                tr.append(th)
                tr.append(td)
                table.append(tr)

        section.append(table)
        container.append(section)

    @staticmethod
    def _add_data_leaks(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        leaks = data.get("data_leak_analysis", [])
        if not leaks:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "🚨 Analyse des Fuites de Données"
        section.append(title)

        for leak in leaks:
            card = soup.new_tag("div")
            risk = leak.get("risk_level", "unknown").lower()
            card.attrs["class"] = f"leak-card risk-{risk}"  # type: ignore[assignment]

            header = soup.new_tag("div")
            header.attrs["class"] = "leak-header"  # type: ignore[assignment]
            source = soup.new_tag("h4")
            source.string = leak.get("source", "N/A")
            header.append(source)
            if date := leak.get("date"):
                date_span = soup.new_tag("span")
                date_span.string = date
                header.append(date_span)
            card.append(header)

            if desc := leak.get("description"):
                desc_p = soup.new_tag("p")
                desc_p.string = desc
                card.append(desc_p)

            risk_badge = soup.new_tag("span")
            risk_badge.attrs["class"] = f"risk-badge risk-{risk}"  # type: ignore[assignment]
            risk_badge.string = f"Risque: {leak.get('risk_level', 'N/A')}"
            card.append(risk_badge)

            section.append(card)

        container.append(section)

    @staticmethod
    def _add_competitive_analysis(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        competitors = data.get("competitive_analysis", [])
        if not competitors:
            return

        section = soup.new_tag("section")
        section.attrs["class"] = "report-section"  # type: ignore[assignment]
        title = soup.new_tag("h2")
        title.string = "⚔️ Analyse Concurrentielle"
        section.append(title)

        for comp in competitors:
            card = soup.new_tag("div")
            card.attrs["class"] = "competitor-card"  # type: ignore[assignment]

            header = soup.new_tag("h3")
            header.string = comp.get("competitor_name", "N/A")
            card.append(header)

            if website := comp.get("website"):
                link = soup.new_tag("a", href=website)
                link.attrs["target"] = "_blank"
                link.string = website
                card.append(link)

            grid = soup.new_tag("div")
            grid.attrs["class"] = "comp-grid"  # type: ignore[assignment]

            if strengths := comp.get("strengths", []):
                str_div = soup.new_tag("div")
                str_div.attrs["class"] = "comp-strengths"  # type: ignore[assignment]
                str_title = soup.new_tag("h4")
                str_title.string = "✅ Forces"
                str_div.append(str_title)
                ul = soup.new_tag("ul")
                for s in strengths:
                    li = soup.new_tag("li")
                    li.string = s
                    ul.append(li)
                str_div.append(ul)
                grid.append(str_div)

            if weaknesses := comp.get("weaknesses", []):
                weak_div = soup.new_tag("div")
                weak_div.attrs["class"] = "comp-weaknesses"  # type: ignore[assignment]
                weak_title = soup.new_tag("h4")
                weak_title.string = "⚠️ Faiblesses"
                weak_div.append(weak_title)
                ul = soup.new_tag("ul")
                for w in weaknesses:
                    li = soup.new_tag("li")
                    li.string = w
                    ul.append(li)
                weak_div.append(ul)
                grid.append(weak_div)

            card.append(grid)
            section.append(card)

        container.append(section)

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        details = soup.new_tag("details")
        details.attrs["class"] = "raw-data"  # type: ignore[assignment]
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
            .web-presence-report {
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
            .website-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
            }
            .website-card .domain {
                font-weight: 600;
                font-size: 1.125rem;
                margin-bottom: 1rem;
            }
            .social-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 1rem;
            }
            .social-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1rem;
            }
            .social-card h3 {
                margin: 0 0 0.5rem 0;
            }
            .social-card a {
                color: var(--link-color, #2563eb);
                font-size: 0.875rem;
            }
            .social-stats {
                display: flex;
                gap: 1rem;
                margin-top: 0.75rem;
            }
            .social-stats span {
                font-size: 0.875rem;
                color: var(--text-muted, #6b7280);
            }
            .notes {
                font-size: 0.875rem;
                color: var(--text-muted, #6b7280);
                margin-top: 0.5rem;
            }
            .infra-table {
                width: 100%;
                border-collapse: collapse;
            }
            .infra-table th, .infra-table td {
                padding: 0.75rem;
                text-align: left;
                border-bottom: 1px solid var(--border-color, #e5e7eb);
            }
            .infra-table th {
                width: 40%;
                font-weight: 500;
                color: var(--text-muted, #6b7280);
            }
            .leak-card {
                background: var(--card-bg, #f9fafb);
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                border-left: 4px solid;
            }
            .leak-card.risk-high { border-color: #ef4444; background: #fef2f2; }
            .leak-card.risk-medium { border-color: #f59e0b; background: #fffbeb; }
            .leak-card.risk-low { border-color: #10b981; background: #ecfdf5; }
            .leak-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
            }
            .leak-header h4 { margin: 0; }
            .risk-badge {
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 500;
            }
            .risk-badge.risk-high { background: #fecaca; color: #dc2626; }
            .risk-badge.risk-medium { background: #fed7aa; color: #ea580c; }
            .risk-badge.risk-low { background: #a7f3d0; color: #059669; }
            .competitor-card {
                background: var(--card-bg, #f9fafb);
                border: 1px solid var(--card-border, #e5e7eb);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            }
            .competitor-card h3 { margin: 0 0 0.5rem 0; }
            .comp-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }
            .comp-strengths, .comp-weaknesses {
                padding: 1rem;
                border-radius: 8px;
            }
            .comp-strengths { background: #ecfdf5; }
            .comp-weaknesses { background: #fef3c7; }
            .comp-strengths h4, .comp-weaknesses h4 { margin: 0 0 0.5rem 0; }
            .comp-strengths ul, .comp-weaknesses ul { margin: 0; padding-left: 1rem; }
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
                .web-presence-report {
                    background-color: #1f2937;
                    color: #e5e7eb;
                }
                .website-card, .social-card, .competitor-card {
                    background: #374151;
                    border-color: #4b5563;
                }
                .leak-card.risk-high { background: #7f1d1d; }
                .leak-card.risk-medium { background: #78350f; }
                .leak-card.risk-low { background: #064e3b; }
                .comp-strengths { background: #064e3b; }
                .comp-weaknesses { background: #78350f; }
            }
        """
        soup.append(style)
