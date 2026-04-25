"""
Shopping Renderer

Renders shopping advice data to structured HTML using BeautifulSoup.
Handles product information, price comparisons, and recommendations.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class ShoppingRenderer(BaseRenderer):
    """Renders shopping advice with structured formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any]) -> str:
        """
        Render shopping data to HTML.

        Args:
            data: Dictionary containing shopping data

        Returns:
            HTML string for shopping content
        """
        # Create main container
        soup = self.create_soup("div", class_="shopping-advice")
        container = soup.find("div")

        # Handle error case
        if "error" in data:
            error_div = soup.new_tag("div", class_="error")
            error_div.string = f"⚠️ {data['error']}"
            container.append(error_div)  # type: ignore[union-attr]
            return str(soup)

        # Add product overview
        self._add_product_overview(soup, container, data)

        # Add price comparison
        self._add_price_comparison(soup, container, data)

        # Add recommendations
        self._add_recommendations(soup, container, data)

        # Add alternatives if available
        self._add_alternatives(soup, container, data)

        # Add pros and cons if available
        self._add_pros_cons(soup, container, data)


        return str(soup)

    def _add_product_overview(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add product overview section."""
        product_name = data.get("product_name")
        product_overview = data.get("product_overview")

        if not (product_name and product_overview):
            return

        overview_section = soup.new_tag("section", class_="product-overview")

        # Title with product name
        title_tag = soup.new_tag("h2")
        title_tag.string = f"🛍️ {product_name}"
        overview_section.append(title_tag)

        # Overview content
        overview_p = soup.new_tag("p")
        overview_p.string = product_overview
        overview_section.append(overview_p)

        # Add product image if available
        product_image = data.get("product_image")
        if product_image:
            img_div = soup.new_tag("div", class_="product-image")
            img_tag = soup.new_tag("img", src=product_image, alt=product_name)
            img_tag["loading"] = "lazy"
            img_div.append(img_tag)
            overview_section.append(img_div)

        container.append(overview_section)

    def _add_price_comparison(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add price comparison section."""
        prices = data.get("price_comparison", [])
        if not prices:
            return

        price_section = soup.new_tag("section", class_="price-comparison")

        # Title
        price_title = soup.new_tag("h3")
        price_title.string = "💰 Comparaison des Prix"
        price_section.append(price_title)

        # Create table for price comparison
        table = soup.new_tag("table", class_="price-table")

        # Add table header
        thead = soup.new_tag("thead")
        tr = soup.new_tag("tr")

        th_vendor = soup.new_tag("th")
        th_vendor.string = "Vendeur"
        tr.append(th_vendor)

        th_price = soup.new_tag("th")
        th_price.string = "Prix"
        tr.append(th_price)

        th_availability = soup.new_tag("th")
        th_availability.string = "Disponibilité"
        tr.append(th_availability)

        thead.append(tr)
        table.append(thead)

        # Add table body
        tbody = soup.new_tag("tbody")

        for price_item in prices:
            vendor = price_item.get("vendor", "")
            price = price_item.get("price", "")
            availability = price_item.get("availability", "")

            tr = soup.new_tag("tr")

            td_vendor = soup.new_tag("td")
            td_vendor.string = vendor
            tr.append(td_vendor)

            td_price = soup.new_tag("td")
            td_price.string = price
            tr.append(td_price)

            td_availability = soup.new_tag("td")
            td_availability.string = availability
            tr.append(td_availability)

            tbody.append(tr)

        table.append(tbody)
        price_section.append(table)
        container.append(price_section)

    def _add_recommendations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add recommendations section."""
        recommendation = data.get("recommendation")
        rationale = data.get("recommendation_rationale")

        if not recommendation:
            return

        rec_section = soup.new_tag("section", class_="recommendations")

        rec_title = soup.new_tag("h3")
        rec_title.string = "🌟 Recommandation"
        rec_section.append(rec_title)

        rec_div = soup.new_tag("div", class_="recommendation-content")

        rec_p = soup.new_tag("p")
        rec_strong = soup.new_tag("strong")
        rec_strong.string = recommendation
        rec_p.append(rec_strong)
        rec_div.append(rec_p)

        if rationale:
            rationale_p = soup.new_tag("p")
            rationale_p.string = f"Raison: {rationale}"
            rec_div.append(rationale_p)

        rec_section.append(rec_div)
        container.append(rec_section)

    def _add_alternatives(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add alternative products section."""
        alternatives = data.get("alternatives", [])
        if not alternatives:
            return

        alt_section = soup.new_tag("section", class_="alternatives")

        alt_title = soup.new_tag("h3")
        alt_title.string = "🔄 Alternatives"
        alt_section.append(alt_title)

        alt_list = soup.new_tag("ul", class_="alternatives-list")

        for alt in alternatives:
            alt_name = alt.get("name", "")
            alt_reason = alt.get("reason", "")

            if alt_name:
                alt_item = soup.new_tag("li")
                alt_name_strong = soup.new_tag("strong")
                alt_name_strong.string = alt_name
                alt_item.append(alt_name_strong)

                if alt_reason:
                    alt_item.append(soup.new_string(f" - {alt_reason}"))

                alt_list.append(alt_item)

        alt_section.append(alt_list)
        container.append(alt_section)

    def _add_pros_cons(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add pros and cons section."""
        pros = data.get("pros", [])
        cons = data.get("cons", [])

        if not (pros or cons):
            return

        pros_cons_section = soup.new_tag("section", class_="pros-cons")

        pros_cons_title = soup.new_tag("h3")
        pros_cons_title.string = "✅ Avantages et ❌ Inconvénients"
        pros_cons_section.append(pros_cons_title)

        pros_cons_div = soup.new_tag("div", class_="pros-cons-container")

        # Add pros
        if pros:
            pros_div = soup.new_tag("div", class_="pros")
            pros_title = soup.new_tag("h4")
            pros_title.string = "✅ Avantages"
            pros_div.append(pros_title)

            pros_list = soup.new_tag("ul")
            for pro in pros:
                pro_item = soup.new_tag("li")
                pro_item.string = pro
                pros_list.append(pro_item)

            pros_div.append(pros_list)
            pros_cons_div.append(pros_div)

        # Add cons
        if cons:
            cons_div = soup.new_tag("div", class_="cons")
            cons_title = soup.new_tag("h4")
            cons_title.string = "❌ Inconvénients"
            cons_div.append(cons_title)

            cons_list = soup.new_tag("ul")
            for con in cons:
                con_item = soup.new_tag("li")
                con_item.string = con
                cons_list.append(con_item)

            cons_div.append(cons_list)
            pros_cons_div.append(cons_div)

        pros_cons_section.append(pros_cons_div)
        container.append(pros_cons_section)
