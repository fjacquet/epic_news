"""Web Presence Renderer

Converts validated web presence data into a visually appealing HTML fragment.
Uses shared BaseRenderer methods to reduce code duplication.

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

        self.add_report_header(soup, container, "🌐 Analyse de Présence Web", data.get("company_name"))
        self.render_text_section(soup, container, data.get("executive_summary"), "Résumé Exécutif", "📋")
        self._add_website_analysis(soup, container, data)
        self._add_social_media(soup, container, data)
        self._add_technical_infrastructure(soup, container, data)
        self._add_data_leaks(soup, container, data)
        self._add_competitive_analysis(soup, container, data)
        self.add_raw_json_section(soup, container, data, "Voir les données brutes")

        return str(soup)

    def _add_website_analysis(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render website analysis section."""
        website = data.get("website_analysis")
        if not website:
            return

        section = self.create_section(soup, "Analyse du Site Web", "🔍")
        card = soup.new_tag("div", **{"class": "website-card"})  # type: ignore[arg-type]

        if domain := website.get("domain"):
            domain_p = soup.new_tag("p", **{"class": "domain"})  # type: ignore[arg-type]
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
            recs_div = soup.new_tag("div", **{"class": "recommendations"})  # type: ignore[arg-type]
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

    def _add_social_media(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render social media footprint section."""
        socials = data.get("social_media_footprint", [])
        if not socials:
            return

        section = self.create_section(soup, "Empreinte Réseaux Sociaux", "📱")
        grid = soup.new_tag("div", **{"class": "social-grid"})  # type: ignore[arg-type]

        for social in socials:
            card = soup.new_tag("div", **{"class": "social-card"})  # type: ignore[arg-type]

            platform = soup.new_tag("h3")
            platform.string = social.get("platform", "N/A")
            card.append(platform)

            if url := social.get("url"):
                link = soup.new_tag("a", href=url)
                link.attrs["target"] = "_blank"
                link.string = url
                card.append(link)

            stats = soup.new_tag("div", **{"class": "social-stats"})  # type: ignore[arg-type]

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
                notes_p = soup.new_tag("p", **{"class": "notes"})  # type: ignore[arg-type]
                notes_p.string = notes
                card.append(notes_p)

            grid.append(card)

        section.append(grid)
        container.append(section)

    def _add_technical_infrastructure(
        self, soup: BeautifulSoup, container: Any, data: dict[str, Any]
    ) -> None:
        """Render technical infrastructure section."""
        infra = data.get("technical_infrastructure")
        if not infra:
            return

        section = self.create_section(soup, "Infrastructure Technique", "🔧")
        table = soup.new_tag("table", **{"class": "infra-table"})  # type: ignore[arg-type]

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

    def _add_data_leaks(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render data leak analysis section."""
        leaks = data.get("data_leak_analysis", [])
        if not leaks:
            return

        section = self.create_section(soup, "Analyse des Fuites de Données", "🚨")

        for leak in leaks:
            risk = leak.get("risk_level", "unknown").lower()
            card = soup.new_tag("div", **{"class": f"leak-card risk-{risk}"})  # type: ignore[arg-type]

            header = soup.new_tag("div", **{"class": "leak-header"})  # type: ignore[arg-type]
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

            risk_badge = soup.new_tag("span", **{"class": f"risk-badge risk-{risk}"})  # type: ignore[arg-type]
            risk_badge.string = f"Risque: {leak.get('risk_level', 'N/A')}"
            card.append(risk_badge)

            section.append(card)

        container.append(section)

    def _add_competitive_analysis(self, soup: BeautifulSoup, container: Any, data: dict[str, Any]) -> None:
        """Render competitive analysis section."""
        competitors = data.get("competitive_analysis", [])
        if not competitors:
            return

        section = self.create_section(soup, "Analyse Concurrentielle", "⚔️")

        for comp in competitors:
            card = soup.new_tag("div", **{"class": "competitor-card"})  # type: ignore[arg-type]

            header = soup.new_tag("h3")
            header.string = comp.get("competitor_name", "N/A")
            card.append(header)

            if website := comp.get("website"):
                link = soup.new_tag("a", href=website)
                link.attrs["target"] = "_blank"
                link.string = website
                card.append(link)

            grid = soup.new_tag("div", **{"class": "comp-grid"})  # type: ignore[arg-type]

            if strengths := comp.get("strengths", []):
                str_div = soup.new_tag("div", **{"class": "comp-strengths"})  # type: ignore[arg-type]
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
                weak_div = soup.new_tag("div", **{"class": "comp-weaknesses"})  # type: ignore[arg-type]
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
