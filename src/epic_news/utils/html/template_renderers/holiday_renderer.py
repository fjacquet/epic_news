"""
Holiday Planner Renderer

Renders holiday planner data to structured HTML using BeautifulSoup.
Handles itinerary, accommodations, dining, budget, and practical information.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class HolidayRenderer(BaseRenderer):
    """Renders holiday planner data with structured formatting."""

    def __init__(self):
        """Initialize the holiday renderer."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render holiday planner data to HTML.

        Args:
            data: Dictionary containing holiday planner data

        Returns:
            HTML string for holiday content
        """
        # Create main container
        soup = self.create_soup("div", **{"class": "holiday-planner"})
        container = soup.find("div")

        # Handle error case
        if "error" in data:
            error_div = soup.new_tag("div", **{"class": "error"})  # type: ignore[arg-type]
            error_div.string = f"⚠️ {data['error']}"
            container.append(error_div)  # type: ignore[union-attr]
            return str(soup)

        # Add introduction
        self._add_introduction(soup, container, data)

        # Add table of contents
        self._add_table_of_contents(soup, container, data)

        # Add itinerary
        self._add_itinerary(soup, container, data)

        # Add accommodations
        self._add_accommodations(soup, container, data)

        # Add dining recommendations
        self._add_dining(soup, container, data)

        # Add budget summary
        self._add_budget(soup, container, data)

        # Add practical information
        self._add_practical_information(soup, container, data)

        # Add sources and media
        self._add_sources_and_media(soup, container, data)

        return str(soup)

    def _add_introduction(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add introduction section."""
        if not data.get("introduction"):
            return

        section = soup.new_tag("section", **{"class": "introduction"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "🌍 Introduction"
        section.append(title)

        intro_div = soup.new_tag("div", **{"class": "intro-content"})  # type: ignore[arg-type]
        intro_div.string = data["introduction"]
        section.append(intro_div)

        container.append(section)

    def _add_table_of_contents(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add table of contents section."""
        toc_items = data.get("table_of_contents", [])
        if not toc_items:
            return

        section = soup.new_tag("section", **{"class": "table-of-contents"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "📋 Table des Matières"
        section.append(title)

        toc_list = soup.new_tag("ul", **{"class": "toc-list"})  # type: ignore[arg-type]
        for item in toc_items:
            li = soup.new_tag("li")
            li.string = item
            toc_list.append(li)

        section.append(toc_list)
        container.append(section)

    def _add_itinerary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add day-by-day itinerary section."""
        itinerary = data.get("itinerary", [])
        if not itinerary:
            return

        section = soup.new_tag("section", **{"class": "itinerary"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "📅 Itinéraire Jour par Jour"
        section.append(title)

        for day_data in itinerary:
            day_div = soup.new_tag("div", **{"class": "day-itinerary"})  # type: ignore[arg-type]

            # Day header
            day_header = soup.new_tag("h3", **{"class": "day-header"})  # type: ignore[arg-type]
            day_header.string = (
                f"Jour {day_data.get('day', 'N/A')} - {day_data.get('date', 'Date non spécifiée')}"
            )
            day_div.append(day_header)

            # Activities
            activities = day_data.get("activities", [])
            if activities:
                activities_div = soup.new_tag("div", **{"class": "activities"})  # type: ignore[arg-type]

                for activity in activities:
                    activity_div = soup.new_tag("div", **{"class": "activity"})  # type: ignore[arg-type]

                    # Time
                    time_span = soup.new_tag("span", **{"class": "activity-time"})  # type: ignore[arg-type]
                    time_span.string = f"⏰ {activity.get('time', 'Heure non spécifiée')}"
                    activity_div.append(time_span)

                    # Description
                    desc_div = soup.new_tag("div", **{"class": "activity-description"})  # type: ignore[arg-type]
                    desc_div.string = activity.get("description", "Description non disponible")
                    activity_div.append(desc_div)

                    activities_div.append(activity_div)

                day_div.append(activities_div)

            section.append(day_div)

        container.append(section)

    def _add_accommodations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add accommodations section."""
        accommodations = data.get("accommodations", [])
        if not accommodations:
            return

        section = soup.new_tag("section", **{"class": "accommodations"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "🏨 Hébergements Recommandés"
        section.append(title)

        for acc in accommodations:
            acc_div = soup.new_tag("div", **{"class": "accommodation"})  # type: ignore[arg-type]

            # Name
            name_h3 = soup.new_tag("h3", **{"class": "accommodation-name"})  # type: ignore[arg-type]
            name_h3.string = acc.get("name", "Nom non spécifié")
            acc_div.append(name_h3)

            # Address
            if acc.get("address"):
                addr_div = soup.new_tag("div", **{"class": "accommodation-address"})  # type: ignore[arg-type]
                addr_div.string = f"📍 {acc['address']}"
                acc_div.append(addr_div)

            # Price range
            if acc.get("price_range"):
                price_div = soup.new_tag("div", **{"class": "accommodation-price"})  # type: ignore[arg-type]
                price_div.string = f"💰 {acc['price_range']}"
                acc_div.append(price_div)

            # Description
            if acc.get("description"):
                desc_div = soup.new_tag("div", **{"class": "accommodation-description"})  # type: ignore[arg-type]
                desc_div.string = acc["description"]
                acc_div.append(desc_div)

            # Amenities
            amenities = acc.get("amenities", [])
            if amenities:
                amenities_div = soup.new_tag("div", **{"class": "accommodation-amenities"})  # type: ignore[arg-type]
                amenities_title = soup.new_tag("strong")
                amenities_title.string = "Équipements: "
                amenities_div.append(amenities_title)
                amenities_div.append(", ".join(amenities))
                acc_div.append(amenities_div)

            # Contact/Booking
            if acc.get("contact_booking"):
                contact_div = soup.new_tag("div", **{"class": "accommodation-contact"})  # type: ignore[arg-type]
                contact_div.string = f"📞 {acc['contact_booking']}"
                acc_div.append(contact_div)

            section.append(acc_div)

        container.append(section)

    def _add_dining(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add dining recommendations section."""
        dining = data.get("dining")
        if not dining:
            return

        section = soup.new_tag("section", **{"class": "dining"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "🍽️ Restaurants et Restauration"
        section.append(title)

        # Restaurants
        restaurants = dining.get("restaurants", [])
        if restaurants:
            restaurants_div = soup.new_tag("div", **{"class": "restaurants"})  # type: ignore[arg-type]

            for restaurant in restaurants:
                rest_div = soup.new_tag("div", **{"class": "restaurant"})  # type: ignore[arg-type]

                # Name
                name_h3 = soup.new_tag("h3", **{"class": "restaurant-name"})  # type: ignore[arg-type]
                name_h3.string = restaurant.get("name", "Nom non spécifié")
                rest_div.append(name_h3)

                # Location
                if restaurant.get("location"):
                    loc_div = soup.new_tag("div", **{"class": "restaurant-location"})  # type: ignore[arg-type]
                    loc_div.string = f"📍 {restaurant['location']}"
                    rest_div.append(loc_div)

                # Cuisine and price
                details = []
                if restaurant.get("cuisine"):
                    details.append(f"Cuisine: {restaurant['cuisine']}")
                if restaurant.get("price_range"):
                    details.append(f"Prix: {restaurant['price_range']}")

                if details:
                    details_div = soup.new_tag("div", **{"class": "restaurant-details"})  # type: ignore[arg-type]
                    details_div.string = " | ".join(details)
                    rest_div.append(details_div)

                # Description
                if restaurant.get("description"):
                    desc_div = soup.new_tag("div", **{"class": "restaurant-description"})  # type: ignore[arg-type]
                    desc_div.string = restaurant["description"]
                    rest_div.append(desc_div)

                # Dietary options
                dietary = restaurant.get("dietary_options", [])
                if dietary:
                    dietary_div = soup.new_tag("div", **{"class": "restaurant-dietary"})  # type: ignore[arg-type]
                    dietary_title = soup.new_tag("strong")
                    dietary_title.string = "Options alimentaires: "
                    dietary_div.append(dietary_title)
                    dietary_div.append(", ".join(dietary))
                    rest_div.append(dietary_div)

                # Contact and reservation
                if restaurant.get("contact"):
                    contact_div = soup.new_tag("div", **{"class": "restaurant-contact"})  # type: ignore[arg-type]
                    contact_div.string = f"📞 {restaurant['contact']}"
                    rest_div.append(contact_div)

                if restaurant.get("reservation_required"):
                    res_div = soup.new_tag("div", **{"class": "restaurant-reservation"})  # type: ignore[arg-type]
                    res_div.string = "⚠️ Réservation recommandée"
                    rest_div.append(res_div)

                restaurants_div.append(rest_div)

            section.append(restaurants_div)

        # Local specialties
        specialties = dining.get("local_specialties", [])
        if specialties:
            spec_div = soup.new_tag("div", **{"class": "local-specialties"})  # type: ignore[arg-type]
            spec_title = soup.new_tag("h3")
            spec_title.string = "🥘 Spécialités Locales à Essayer"
            spec_div.append(spec_title)

            spec_list = soup.new_tag("ul")
            for specialty in specialties:
                li = soup.new_tag("li")
                li.string = specialty
                spec_list.append(li)
            spec_div.append(spec_list)
            section.append(spec_div)

        container.append(section)

    def _add_budget(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add budget summary section."""
        budget = data.get("budget")
        if not budget:
            return

        section = soup.new_tag("section", **{"class": "budget"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "💰 Résumé du Budget"
        section.append(title)

        # Budget items
        items = budget.get("items", [])
        if items:
            table = soup.new_tag("table", **{"class": "budget-table"})  # type: ignore[arg-type]

            # Header
            thead = soup.new_tag("thead")
            header_row = soup.new_tag("tr")

            headers = ["Catégorie", "Article", "Coût", "Notes"]
            for header in headers:
                th = soup.new_tag("th")
                th.string = header
                header_row.append(th)

            thead.append(header_row)
            table.append(thead)

            # Body
            tbody = soup.new_tag("tbody")
            for item in items:
                row = soup.new_tag("tr")

                # Category
                cat_td = soup.new_tag("td")
                cat_td.string = item.get("category", "N/A")
                row.append(cat_td)

                # Item
                item_td = soup.new_tag("td")
                item_td.string = item.get("item", "N/A")
                row.append(item_td)

                # Cost
                cost_td = soup.new_tag("td")
                cost = item.get("cost", "N/A")
                currency = item.get("currency", "CHF")
                cost_td.string = f"{cost} {currency}"
                row.append(cost_td)

                # Notes
                notes_td = soup.new_tag("td")
                notes_td.string = item.get("notes", "")
                row.append(notes_td)

                tbody.append(row)

            table.append(tbody)
            section.append(table)

        # Total
        if budget.get("total_estimated"):
            total_div = soup.new_tag("div", **{"class": "budget-total"})  # type: ignore[arg-type]
            total_div.string = f"💵 Total Estimé: {budget['total_estimated']} {budget.get('currency', 'CHF')}"
            section.append(total_div)

        # Notes
        if budget.get("notes"):
            notes_div = soup.new_tag("div", **{"class": "budget-notes"})  # type: ignore[arg-type]
            notes_div.string = f"📝 {budget['notes']}"
            section.append(notes_div)

        container.append(section)

    def _add_practical_information(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add practical information section."""
        practical = data.get("practical_information")
        if not practical:
            return

        section = soup.new_tag("section", **{"class": "practical-information"})  # type: ignore[arg-type]

        title = soup.new_tag("h2")
        title.string = "ℹ️ Informations Pratiques"
        section.append(title)

        # Packing checklist
        packing = practical.get("packing_checklist")
        if packing:
            packing_div = soup.new_tag("div", **{"class": "packing-checklist"})  # type: ignore[arg-type]
            packing_title = soup.new_tag("h3")
            packing_title.string = "🧳 Liste de Bagages"
            packing_div.append(packing_title)

            # Different packing categories
            categories = {
                "vetements": "👕 Vêtements",
                "documents": "📄 Documents",
                "toiletries": "🧴 Toilettes",
                "electronics": "🔌 Électronique",
                "medical": "💊 Médical",
                "activities": "🎯 Activités",
                "children": "👶 Enfants",
            }

            for key, emoji_title in categories.items():
                items = packing.get(key, [])
                if items:
                    cat_div = soup.new_tag("div", **{"class": f"packing-{key}"})  # type: ignore[arg-type]
                    cat_title = soup.new_tag("h4")
                    cat_title.string = emoji_title
                    cat_div.append(cat_title)

                    cat_list = soup.new_tag("ul")
                    for item in items:
                        li = soup.new_tag("li")
                        li.string = item
                        cat_list.append(li)
                    cat_div.append(cat_list)
                    packing_div.append(cat_div)

            section.append(packing_div)

        # Safety tips
        safety_tips = practical.get("safety_tips", [])
        if safety_tips:
            safety_div = soup.new_tag("div", **{"class": "safety-tips"})  # type: ignore[arg-type]
            safety_title = soup.new_tag("h3")
            safety_title.string = "🛡️ Conseils de Sécurité"
            safety_div.append(safety_title)

            safety_list = soup.new_tag("ul")
            for tip in safety_tips:
                li = soup.new_tag("li")
                li.string = tip
                safety_list.append(li)
            safety_div.append(safety_list)
            section.append(safety_div)

        # Emergency contacts
        emergency = practical.get("emergency_contacts", [])
        if emergency:
            emergency_div = soup.new_tag("div", **{"class": "emergency-contacts"})  # type: ignore[arg-type]
            emergency_title = soup.new_tag("h3")
            emergency_title.string = "🚨 Contacts d'Urgence"
            emergency_div.append(emergency_title)

            for contact in emergency:
                contact_div = soup.new_tag("div", **{"class": "emergency-contact"})  # type: ignore[arg-type]
                contact_div.string = f"{contact.get('service', 'Service')}: {contact.get('number', 'N/A')}"
                if contact.get("notes"):
                    contact_div.string += f" ({contact['notes']})"  # type: ignore[operator]
                emergency_div.append(contact_div)

            section.append(emergency_div)

        # Useful phrases
        phrases = practical.get("useful_phrases", [])
        if phrases:
            phrases_div = soup.new_tag("div", **{"class": "useful-phrases"})  # type: ignore[arg-type]
            phrases_title = soup.new_tag("h3")
            phrases_title.string = "💬 Phrases Utiles"
            phrases_div.append(phrases_title)

            for phrase in phrases:
                phrase_div = soup.new_tag("div", **{"class": "phrase"})  # type: ignore[arg-type]
                phrase_div.string = f"🇫🇷 {phrase.get('french', 'N/A')} → {phrase.get('local', 'N/A')}"
                if phrase.get("pronunciation"):
                    phrase_div.string += f" [{phrase['pronunciation']}]"  # type: ignore[operator]
                phrases_div.append(phrase_div)

            section.append(phrases_div)

        container.append(section)

    def _add_sources_and_media(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add sources and media section."""
        sources = data.get("sources", [])
        media = data.get("media", [])

        if not sources and not media:
            return

        section = soup.new_tag("section", **{"class": "sources-media"})  # type: ignore[arg-type]

        # Sources
        if sources:
            sources_div = soup.new_tag("div", **{"class": "sources"})  # type: ignore[arg-type]
            sources_title = soup.new_tag("h3")
            sources_title.string = "📚 Sources"
            sources_div.append(sources_title)

            sources_list = soup.new_tag("ul")
            for source in sources:
                li = soup.new_tag("li")
                if source.get("url"):
                    link = soup.new_tag("a", href=source["url"], target="_blank")
                    link.string = source.get("title", source["url"])
                    li.append(link)
                else:
                    li.string = source.get("title", "Source sans titre")
                sources_list.append(li)

            sources_div.append(sources_list)
            section.append(sources_div)

        # Media
        if media:
            media_div = soup.new_tag("div", **{"class": "media"})  # type: ignore[arg-type]
            media_title = soup.new_tag("h3")
            media_title.string = "🖼️ Médias"
            media_div.append(media_title)

            for media_item in media:
                item_div = soup.new_tag("div", **{"class": "media-item"})  # type: ignore[arg-type]

                if media_item.get("type") == "image" or not media_item.get("type"):
                    img = soup.new_tag(
                        "img", src=media_item.get("url", ""), alt=media_item.get("caption", "")
                    )
                    item_div.append(img)
                else:
                    link = soup.new_tag("a", href=media_item.get("url", ""), target="_blank")
                    link.string = media_item.get("caption", "Média")
                    item_div.append(link)

                if media_item.get("caption"):
                    caption_div = soup.new_tag("div", **{"class": "media-caption"})  # type: ignore[arg-type]
                    caption_div.string = media_item["caption"]
                    item_div.append(caption_div)

                media_div.append(item_div)

            section.append(media_div)

        container.append(section)
