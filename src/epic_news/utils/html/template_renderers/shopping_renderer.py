"""
Shopping Renderer

Renders shopping advice to structured HTML using BeautifulSoup.

Consumes the ``ShoppingAdviceOutput`` model contract directly, exactly as it
arrives via ``render_report("SHOPPING", ShoppingAdviceOutput.model_dump())``:
``product_info`` (name, overview, key_specifications, pros, cons,
target_audience, common_issues), ``switzerland_prices`` / ``france_prices``
(lists of PriceInfo), ``competitors`` (list of CompetitorInfo),
``executive_summary``, ``final_recommendations``, ``best_deals`` and
``user_preferences_context``.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class ShoppingRenderer(BaseRenderer):
    """Renders shopping advice with structured formatting."""

    def __init__(self):
        """Initialize the shopping renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """
        Render shopping advice data to HTML.

        Args:
            data: ``ShoppingAdviceOutput.model_dump()`` (or ``{"error": ...}``)

        Returns:
            HTML string for shopping content
        """
        soup = self.create_soup("div", class_="shopping-advice")
        container = soup.find("div")

        # Handle error case
        if "error" in data:
            error_div = soup.new_tag("div", attrs={"class": "error"})
            error_div.string = f"⚠️ {data['error']}"
            container.append(error_div)  # type: ignore[union-attr]
            return str(soup)

        self._add_product_overview(soup, container, data)
        self._add_executive_summary(soup, container, data)
        self._add_prices(soup, container, data)
        self._add_pros_cons(soup, container, data)
        self._add_competitors(soup, container, data)
        self._add_best_deals(soup, container, data)
        self._add_recommendations(soup, container, data)
        self._add_user_context(soup, container, data)

        # Empty-state: if a degenerate payload produced no sections, signal it
        # visibly instead of returning a silently blank wrapper.
        if not container.find(True):  # type: ignore[union-attr]
            empty = soup.new_tag("div", attrs={"class": "empty-state"})
            empty.string = "Aucune donnée d'achat disponible."
            container.append(empty)  # type: ignore[union-attr]

        return str(soup)

    @staticmethod
    def _bullet_list(soup: BeautifulSoup, items: Any, css_class: str | None = None):
        """Build a ``<ul>`` from a list of scalars, or return None if empty."""
        if not (isinstance(items, list) and items):
            return None
        ul = soup.new_tag("ul", attrs={"class": css_class}) if css_class else soup.new_tag("ul")
        for item in items:
            li = soup.new_tag("li")
            li.string = str(item)
            ul.append(li)
        return ul

    def _add_product_overview(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the product overview section from ``product_info``."""
        product = data.get("product_info")
        if not isinstance(product, dict):
            return

        name = product.get("name")
        overview = product.get("overview")
        if not (name or overview):
            return

        section = soup.new_tag("section", attrs={"class": "product-overview"})

        if name:
            title_tag = soup.new_tag("h2")
            title_tag.string = f"🛍️ {name}"
            section.append(title_tag)

        if overview:
            overview_p = soup.new_tag("p")
            overview_p.string = overview
            section.append(overview_p)

        target_audience = product.get("target_audience")
        if target_audience:
            aud_p = soup.new_tag("p")
            aud_strong = soup.new_tag("strong")
            aud_strong.string = "Public cible : "
            aud_p.append(aud_strong)
            aud_p.append(soup.new_string(target_audience))
            section.append(aud_p)

        specs = self._bullet_list(soup, product.get("key_specifications"), "product-specs")
        if specs is not None:
            specs_title = soup.new_tag("h3")
            specs_title.string = "📋 Spécifications"
            section.append(specs_title)
            section.append(specs)

        issues = self._bullet_list(soup, product.get("common_issues"), "common-issues")
        if issues is not None:
            issues_title = soup.new_tag("h3")
            issues_title.string = "⚠️ Problèmes fréquents"
            section.append(issues_title)
            section.append(issues)

        container.append(section)

    def _add_executive_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the executive summary section."""
        summary = data.get("executive_summary")
        if not summary:
            return

        section = soup.new_tag("section", attrs={"class": "executive-summary"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "📝 Résumé"
        section.append(title_tag)
        summary_p = soup.new_tag("p")
        summary_p.string = summary
        section.append(summary_p)
        container.append(section)

    def _add_prices(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add price comparison tables for Switzerland and France."""
        switzerland = data.get("switzerland_prices") or []
        france = data.get("france_prices") or []
        if not (switzerland or france):
            return

        section = soup.new_tag("section", attrs={"class": "price-comparison"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "💰 Comparaison des Prix"
        section.append(title_tag)

        self._add_price_table(soup, section, "🇨🇭 Suisse", switzerland)
        self._add_price_table(soup, section, "🇫🇷 France", france)

        container.append(section)

    def _add_price_table(self, soup: BeautifulSoup, parent, label: str, prices: list) -> None:
        """Add a single labelled price table (one row per PriceInfo)."""
        if not prices:
            return

        label_tag = soup.new_tag("h4")
        label_tag.string = label
        parent.append(label_tag)

        table = soup.new_tag("table", attrs={"class": "price-table"})

        thead = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        for col in ("Vendeur", "Prix", "Livraison", "Total", "Notes"):
            th = soup.new_tag("th")
            th.string = col
            header_row.append(th)
        thead.append(header_row)
        table.append(thead)

        tbody = soup.new_tag("tbody")
        for price_item in prices:
            if not isinstance(price_item, dict):
                continue
            row = soup.new_tag("tr")

            # Retailer cell, linked when a URL is available.
            retailer_td = soup.new_tag("td")
            retailer = price_item.get("retailer") or ""
            url = price_item.get("url")
            # Only hyperlink safe http(s) schemes; a javascript:/data: URL from
            # crew output would be a clickable XSS vector (HTML-escaping does not
            # neutralise the scheme). Otherwise show the retailer as plain text.
            if isinstance(url, str) and url.strip().lower().startswith(("http://", "https://")):
                link = soup.new_tag("a", attrs={"href": url.strip(), "target": "_blank", "rel": "noopener"})
                link.string = retailer
                retailer_td.append(link)
            else:
                retailer_td.string = retailer
            row.append(retailer_td)

            for key in ("price", "shipping_cost", "total_cost", "notes"):
                cell = soup.new_tag("td")
                cell.string = str(price_item.get(key) or "")
                row.append(cell)

            tbody.append(row)
        table.append(tbody)
        parent.append(table)

    def _add_pros_cons(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the product's pros and cons (from ``product_info``)."""
        product = data.get("product_info")
        if not isinstance(product, dict):
            return

        pros = product.get("pros") or []
        cons = product.get("cons") or []
        if not (pros or cons):
            return

        section = soup.new_tag("section", attrs={"class": "pros-cons"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "✅ Avantages et ❌ Inconvénients"
        section.append(title_tag)

        pros_cons_div = soup.new_tag("div", attrs={"class": "pros-cons-container"})

        pros_list = self._bullet_list(soup, pros)
        if pros_list is not None:
            pros_div = soup.new_tag("div", attrs={"class": "pros"})
            pros_title = soup.new_tag("h4")
            pros_title.string = "✅ Avantages"
            pros_div.append(pros_title)
            pros_div.append(pros_list)
            pros_cons_div.append(pros_div)

        cons_list = self._bullet_list(soup, cons)
        if cons_list is not None:
            cons_div = soup.new_tag("div", attrs={"class": "cons"})
            cons_title = soup.new_tag("h4")
            cons_title.string = "❌ Inconvénients"
            cons_div.append(cons_title)
            cons_div.append(cons_list)
            pros_cons_div.append(cons_div)

        section.append(pros_cons_div)
        container.append(section)

    def _add_competitors(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add competing products as the alternatives section."""
        competitors = data.get("competitors") or []
        if not competitors:
            return

        section = soup.new_tag("section", attrs={"class": "alternatives"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "🔄 Alternatives"
        section.append(title_tag)

        for comp in competitors:
            if not isinstance(comp, dict):
                continue
            card = soup.new_tag("div", attrs={"class": "alternative"})

            name = comp.get("name")
            price_range = comp.get("price_range")
            if name:
                heading = soup.new_tag("h4")
                heading.string = f"{name} ({price_range})" if price_range else name
                card.append(heading)

            features = self._bullet_list(soup, comp.get("key_features"))
            if features is not None:
                card.append(features)

            target_audience = comp.get("target_audience")
            if target_audience:
                aud_p = soup.new_tag("p")
                aud_strong = soup.new_tag("strong")
                aud_strong.string = "Public cible : "
                aud_p.append(aud_strong)
                aud_p.append(soup.new_string(target_audience))
                card.append(aud_p)

            section.append(card)

        container.append(section)

    def _add_best_deals(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the best-deals list."""
        deals = self._bullet_list(soup, data.get("best_deals"), "best-deals-list")
        if deals is None:
            return

        section = soup.new_tag("section", attrs={"class": "best-deals"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "🏆 Meilleures Offres"
        section.append(title_tag)
        section.append(deals)
        container.append(section)

    def _add_recommendations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the final recommendation section."""
        recommendation = data.get("final_recommendations")
        if not recommendation:
            return

        section = soup.new_tag("section", attrs={"class": "recommendations"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "🌟 Recommandation Finale"
        section.append(title_tag)

        content_div = soup.new_tag("div", attrs={"class": "recommendation-content"})
        rec_p = soup.new_tag("p")
        rec_p.string = recommendation
        content_div.append(rec_p)
        section.append(content_div)
        container.append(section)

    def _add_user_context(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add the user-preferences context footnote."""
        context = data.get("user_preferences_context")
        if not context:
            return

        section = soup.new_tag("section", attrs={"class": "user-context"})
        title_tag = soup.new_tag("h3")
        title_tag.string = "👤 Contexte pris en compte"
        section.append(title_tag)
        context_p = soup.new_tag("p")
        context_p.string = context
        section.append(context_p)
        container.append(section)
