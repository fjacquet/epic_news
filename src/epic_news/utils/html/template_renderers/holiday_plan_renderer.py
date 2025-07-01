"""
Holiday Plan Renderer

Renders holiday plan data to structured HTML using BeautifulSoup.
Handles itinerary, accommodations, dining, budget, and practical information.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class HolidayPlanRenderer(BaseRenderer):
    """Renders holiday plan content with travel-specific formatting."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render holiday plan data to HTML.

        Args:
            data: Dictionary containing holiday plan data

        Returns:
            HTML string for holiday plan content
        """
        try:
            # Create main container with proper HTML structure
            soup = BeautifulSoup("", "html.parser")
            container = soup.new_tag("div")
            container["class"] = "holiday-plan-report"
            soup.append(container)

            # Add introduction
            print("🔍 DEBUG: Adding introduction...")
            self._add_introduction(soup, container, data)

            # Add itinerary
            print("🔍 DEBUG: Adding itinerary...")
            self._add_itinerary(soup, container, data)

            # Add accommodations
            print("🔍 DEBUG: Adding accommodations...")
            self._add_accommodations(soup, container, data)

            # Add dining recommendations
            print("🔍 DEBUG: Adding dining...")
            self._add_dining(soup, container, data)

            # Add budget breakdown
            print("🔍 DEBUG: Adding budget...")
            self._add_budget(soup, container, data)

            # Add practical information
            print("🔍 DEBUG: Adding practical info...")
            self._add_practical_info(soup, container, data)

            # Add sources and media
            print("🔍 DEBUG: Adding sources and media...")
            self._add_sources_and_media(soup, container, data)

            # Add styles
            print("🔍 DEBUG: Adding styles...")
            self._add_styles(soup)

            return str(soup)

        except Exception as e:
            print(f"❌ ERROR in HolidayPlanRenderer.render: {e}")
            import traceback

            traceback.print_exc()
            raise

    def _add_introduction(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add destination introduction."""
        if introduction := data.get("introduction"):
            section = soup.new_tag("section")
            section["class"] = "introduction-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "🌍 Introduction à la Destination"
            section.append(header)

            # Introduction content
            intro_div = soup.new_tag("div")
            intro_div["class"] = "introduction-content"
            intro_div.string = introduction
            section.append(intro_div)

            container.append(section)

    def _add_itinerary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add day-by-day itinerary."""
        # Use French key 'itineraire' instead of English 'itinerary'
        if itinerary := data.get("itineraire", []):
            section = soup.new_tag("section")
            section["class"] = "itinerary-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "📅 Itinéraire Détaillé"
            section.append(header)

            # Itinerary days
            for day_data in itinerary:
                day_div = soup.new_tag("div")
                day_div["class"] = "itinerary-day"

                # Day header - jour is a string like "Jour 1 - Vendredi : Arrivée & Découverte de Monterosso"
                day_header = soup.new_tag("h3")
                jour = day_data.get("jour", "Jour")
                day_header.string = f"📍 {jour}"
                day_div.append(day_header)

                # Activities
                if activites := day_data.get("activites", []):
                    activities_div = soup.new_tag("div")
                    activities_div["class"] = "activities-list"
                    for activity in activites:
                        activity_div = soup.new_tag("div")
                        activity_div["class"] = "activity-item"

                        # Time
                        if heure := activity.get("heure"):
                            time_span = soup.new_tag("span")
                            time_span["class"] = "activity-time"
                            time_span.string = f"⏰ {heure}"
                            activity_div.append(time_span)

                        # Description
                        if description := activity.get("description"):
                            desc_p = soup.new_tag("p")
                            desc_p["class"] = "activity-description"
                            desc_p.string = description
                            activity_div.append(desc_p)

                        # Travel notes
                        if notes_de_voyage := activity.get("notes_de_voyage"):
                            notes_p = soup.new_tag("p")
                            notes_p["class"] = "travel-notes"
                            notes_p.string = f"📝 {notes_de_voyage}"
                            activity_div.append(notes_p)

                        # Reservation info
                        if reservation := activity.get("reservation"):
                            res_p = soup.new_tag("p")
                            res_p["class"] = "reservation-info"
                            res_p.string = f"📞 {reservation}"
                            activity_div.append(res_p)

                        # Tips/Conseils
                        if conseils := activity.get("conseils"):
                            tips_p = soup.new_tag("p")
                            tips_p["class"] = "activity-tips"
                            tips_p.string = f"💡 {conseils}"
                            activity_div.append(tips_p)

                        # Accessibility
                        if accessibilite := activity.get("accessibilite"):
                            access_p = soup.new_tag("p")
                            access_p["class"] = "accessibility-info"
                            access_p.string = f"♿ {accessibilite}"
                            activity_div.append(access_p)

                        # Additional activity details
                        if notes_transport := activity.get("notes_transport"):
                            transport_p = soup.new_tag("p")
                            transport_p["class"] = "transport-notes"
                            transport_p.string = f"🚆 Transport: {notes_transport}"
                            activity_div.append(transport_p)

                        if infos_resa := activity.get("infos_resa"):
                            resa_p = soup.new_tag("p")
                            resa_p["class"] = "reservation-info"
                            resa_p.string = f"🎫 Réservation: {infos_resa}"
                            activity_div.append(resa_p)

                        if plan_b := activity.get("plan_b"):
                            planb_p = soup.new_tag("p")
                            planb_p["class"] = "plan-b"
                            planb_p.string = f"🔄 Plan B: {plan_b}"
                            activity_div.append(planb_p)

                        activities_div.append(activity_div)
                    day_div.append(activities_div)

                section.append(day_div)

            container.append(section)

    def _add_accommodations(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add accommodation recommendations."""
        # Use French key 'hebergement' instead of English 'accommodations'
        if accommodations := data.get("hebergement", []):
            section = soup.new_tag("section")
            section["class"] = "accommodations-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "🏨 Hébergements Recommandés"
            section.append(header)

            # Accommodations list
            for acc in accommodations:
                acc_div = soup.new_tag("div")
                acc_div["class"] = "accommodation-item"

                # Accommodation name
                name_h3 = soup.new_tag("h3")
                name_h3.string = f"🏠 {acc.get('nom', 'Hébergement')}"
                acc_div.append(name_h3)

                # Details
                if adresse := acc.get("adresse"):
                    addr_p = soup.new_tag("p")
                    addr_p["class"] = "address"
                    addr_p.string = f"📍 Adresse: {adresse}"
                    acc_div.append(addr_p)

                if contact := acc.get("contact"):
                    contact_p = soup.new_tag("p")
                    contact_p["class"] = "contact"
                    contact_p.string = f"📞 Contact: {contact}"
                    acc_div.append(contact_p)

                if prix := acc.get("prix"):
                    price_p = soup.new_tag("p")
                    price_p["class"] = "price-range"
                    price_p.string = f"💰 Prix: {prix}"
                    acc_div.append(price_p)

                if pourquoi := acc.get("pourquoi_recommande"):
                    why_p = soup.new_tag("p")
                    why_p["class"] = "recommendation-reason"
                    why_p.string = f"✨ Pourquoi: {pourquoi}"
                    acc_div.append(why_p)

                section.append(acc_div)

            container.append(section)

    def _add_dining(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add dining recommendations."""
        # Use French key 'restauration' instead of English 'dining'
        if dining := data.get("restauration", []):
            section = soup.new_tag("section")
            section["class"] = "dining-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "🍽️ Expériences Culinaires"
            section.append(header)

            # Dining recommendations
            for restaurant in dining:
                rest_div = soup.new_tag("div")
                rest_div["class"] = "dining-item"

                # Restaurant name
                name_h3 = soup.new_tag("h3")
                name_h3.string = f"🍴 {restaurant.get('nom', 'Restaurant')}"
                rest_div.append(name_h3)

                # Details
                if adresse := restaurant.get("adresse"):
                    addr_p = soup.new_tag("p")
                    addr_p["class"] = "address"
                    addr_p.string = f"📍 Adresse: {adresse}"
                    rest_div.append(addr_p)

                if specialites := restaurant.get("specialites"):
                    spec_p = soup.new_tag("p")
                    spec_p["class"] = "specialties"
                    spec_p.string = f"🥘 Spécialités: {specialites}"
                    rest_div.append(spec_p)

                if prix_moyen := restaurant.get("prix_moyen"):
                    price_p = soup.new_tag("p")
                    price_p["class"] = "average-price"
                    price_p.string = f"💰 Prix moyen: {prix_moyen}"
                    rest_div.append(price_p)

                if contact := restaurant.get("contact"):
                    contact_p = soup.new_tag("p")
                    contact_p["class"] = "contact"
                    contact_p.string = f"📞 Contact: {contact}"
                    rest_div.append(contact_p)

                if pourquoi_recommande := restaurant.get("pourquoi_recommande"):
                    just_p = soup.new_tag("p")
                    just_p["class"] = "justification"
                    just_p.string = f"💡 Recommandation: {pourquoi_recommande}"
                    rest_div.append(just_p)

                section.append(rest_div)

            container.append(section)

    def _add_budget(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add budget breakdown."""
        if budget := data.get("budget"):
            section = soup.new_tag("section")
            section["class"] = "budget-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "💰 Analyse Budgétaire"
            section.append(header)

            # Budget categories
            budget_categories = [
                ("transport", "🚆 Transport"),
                ("hebergement", "🏨 Hébergement"),
                ("repas", "🍽️ Repas"),
                ("activites", "🎭 Activités"),
            ]

            for category_key, category_title in budget_categories:
                if category_data := budget.get(category_key):
                    cat_div = soup.new_tag("div")
                    cat_div["class"] = "budget-category"

                    # Category title
                    cat_h3 = soup.new_tag("h3")
                    cat_h3.string = category_title
                    cat_div.append(cat_h3)

                    # Category items
                    if isinstance(category_data, dict):
                        for item_key, item_value in category_data.items():
                            if item_key != "total":
                                item_p = soup.new_tag("p")
                                item_p["class"] = "budget-item"
                                item_p.string = f"• {item_key.replace('_', ' ').title()}: {item_value}"
                                cat_div.append(item_p)

                    section.append(cat_div)

            # Total estimate - properly format the dict
            if total_estime := budget.get("total_estime"):
                total_div = soup.new_tag("div")
                total_div["class"] = "budget-total"
                total_h3 = soup.new_tag("h3")

                if isinstance(total_estime, dict):
                    montant = total_estime.get("montant", "N/A")
                    devise = total_estime.get("devise", "EUR")
                    notes = total_estime.get("notes", "")
                    total_text = f"{montant} {devise}"
                    if notes:
                        total_text += f" ({notes})"
                else:
                    total_text = str(total_estime)

                total_h3.string = f"💵 Total Estimé: {total_text}"
                total_div.append(total_h3)
                section.append(total_div)

            container.append(section)

    def _add_practical_info(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add practical travel information."""
        # Use French key 'information_pratique' instead of English 'practical_info'
        if practical_info := data.get("information_pratique"):
            section = soup.new_tag("section")
            section["class"] = "practical-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "📋 Informations Pratiques"
            section.append(header)

            # Emergency contacts
            if contacts_urgence := practical_info.get("contacts_urgence", []):
                contacts_div = soup.new_tag("div")
                contacts_div["class"] = "emergency-contacts"
                contacts_h3 = soup.new_tag("h3")
                contacts_h3.string = "🆘 Contacts d'Urgence"
                contacts_div.append(contacts_h3)
                contacts_ul = soup.new_tag("ul")
                for contact in contacts_urgence:
                    if isinstance(contact, dict):
                        # Handle dict format like {'urgence': 'Numéro d\'urgence...', 'numero': '112'}
                        for key, value in contact.items():
                            li = soup.new_tag("li")
                            li.string = f"{key.title()}: {value}"
                            contacts_ul.append(li)
                    else:
                        # Handle string format
                        li = soup.new_tag("li")
                        li.string = str(contact)
                        contacts_ul.append(li)
                        contacts_div.append(contacts_ul)
                section.append(contacts_div)
                # Useful phrases
            if phrases_utiles := practical_info.get("phrases_utiles", []):
                phrases_div = soup.new_tag("div")
                phrases_div["class"] = "useful-phrases"
                phrases_h3 = soup.new_tag("h3")
                phrases_h3.string = "🗣️ Phrases Utiles"

                phrases_div.append(phrases_h3)
                phrases_ul = soup.new_tag("ul")
                for phrase in phrases_utiles:
                    if isinstance(phrase, dict):
                        # Handle dict format like {'francais': 'Bonjour', 'italien': 'Buongiorno'}
                        li = soup.new_tag("li")
                        francais = phrase.get("francais", "")
                        italien = phrase.get("italien", "")
                        li.string = f"{francais} = {italien}"
                        phrases_ul.append(li)
                    else:
                        # Handle string format
                        li = soup.new_tag("li")
                        li.string = str(phrase)
                        phrases_ul.append(li)
                        phrases_div.append(phrases_ul)
                section.append(phrases_div)
                container.append(section)

    def _add_sources_and_media(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add sources and media references."""
        section = soup.new_tag("section")
        section["class"] = "references-section"

        # Section header
        header = soup.new_tag("h2")
        header.string = "📚 Sources et Références"
        section.append(header)

        # Sources
        if sources := data.get("sources", []):
            sources_div = soup.new_tag("div")
            sources_div["class"] = "sources"
            sources_h3 = soup.new_tag("h3")
            sources_h3.string = "🔗 Sources"
            sources_div.append(sources_h3)

            sources_ul = soup.new_tag("ul")
            for source in sources:
                li = soup.new_tag("li")
                if isinstance(source, str) and source.startswith("http"):
                    # Create clickable link
                    link = soup.new_tag("a", href=source, target="_blank")
                    link.string = source
                    li.append(link)
                else:
                    li.string = str(source)
                sources_ul.append(li)

            sources_div.append(sources_ul)
            section.append(sources_div)

        # Media
        if media := data.get("media", []):
            media_div = soup.new_tag("div")
            media_div["class"] = "media"
            media_h3 = soup.new_tag("h3")
            media_h3.string = "🎬 Médias"
            media_div.append(media_h3)

            media_ul = soup.new_tag("ul")
            for item in media:
                li = soup.new_tag("li")
                if isinstance(item, dict):
                    # Handle dict format with url and caption
                    url = item.get("url", "")
                    caption = item.get("caption", "")

                    if url:
                        link = soup.new_tag("a", href=url, target="_blank", rel="noopener")
                        link.string = caption or url
                        li.append(link)

                        if caption:
                            caption_span = soup.new_tag("span")
                            caption_span["class"] = "media-caption"
                            caption_span.string = f" - {caption}"
                            li.append(caption_span)
                else:
                    # Handle string format
                    li.string = str(item)

                media_ul.append(li)

            media_div.append(media_ul)
            section.append(media_div)

        container.append(section)

        phrases_ul = soup.new_tag("ul")
        for phrase in phrases_utiles:
            li = soup.new_tag("li")
            li.string = phrase
            phrases_ul.append(li)
        phrases_div.append(phrases_ul)
        section.append(phrases_div)

        # Packing list
        if liste_bagages := practical.get("liste_bagages", {}):
            packing_div = soup.new_tag("div")
            packing_div["class"] = "packing-checklist"
            packing_h3 = soup.new_tag("h3")
            packing_h3.string = "🎒 Liste de Bagages"
            packing_div.append(packing_h3)

            if isinstance(liste_bagages, dict):
                for category, items in liste_bagages.items():
                    cat_div = soup.new_tag("div")
                    cat_div["class"] = "packing-category"
                    cat_h4 = soup.new_tag("h4")
                    cat_h4.string = category
                    cat_div.append(cat_h4)

                    if items and isinstance(items, list):
                        items_ul = soup.new_tag("ul")
                        for item in items:
                            li = soup.new_tag("li")
                            li.string = item
                            items_ul.append(li)
                        cat_div.append(items_ul)

                        packing_div.append(cat_div)

            section.append(packing_div)

        container.append(section)

    def _add_sources_and_media(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add sources and media links."""
        sources = data.get("sources", [])
        media = data.get("media", [])

        if sources or media:
            section = soup.new_tag("section")
            section["class"] = "references-section"

            # Section header
            header = soup.new_tag("h2")
            header.string = "📚 Sources et Références"
            section.append(header)

            # Sources
            if sources:
                sources_div = soup.new_tag("div")
                sources_div["class"] = "sources"
                sources_h3 = soup.new_tag("h3")
                sources_h3.string = "🔗 Sources"
                sources_div.append(sources_h3)

                sources_ul = soup.new_tag("ul")
                for source in sources:
                    li = soup.new_tag("li")
                    if source.startswith("http"):
                        a = soup.new_tag("a", href=source, target="_blank")
                        a.string = source
                        li.append(a)
                    else:
                        li.string = source
                    sources_ul.append(li)
                sources_div.append(sources_ul)
                section.append(sources_div)

            # Media
            if media:
                media_div = soup.new_tag("div")
                media_div["class"] = "media"
                media_h3 = soup.new_tag("h3")
                media_h3.string = "🎬 Médias"
                media_div.append(media_h3)

                media_ul = soup.new_tag("ul")
                for media_item in media:
                    li = soup.new_tag("li")

                    # Handle media items as dictionaries with url and caption
                    if isinstance(media_item, dict):
                        url = media_item.get("url", "")
                        caption = media_item.get("caption", "")

                        if url:
                            a = soup.new_tag("a", href=url, target="_blank", rel="noopener")
                            a.string = caption if caption else url
                            li.append(a)

                            # Add caption as additional text if different from link text
                            if caption and caption != url:
                                caption_span = soup.new_tag("span")
                                caption_span["class"] = "media-caption"
                                caption_span.string = f" - {caption}"
                                li.append(caption_span)
                        else:
                            li.string = caption if caption else str(media_item)

                    # Handle legacy string format
                    elif isinstance(media_item, str):
                        if media_item.startswith("http"):
                            a = soup.new_tag("a", href=media_item, target="_blank")
                            a.string = media_item
                            li.append(a)
                        else:
                            li.string = media_item
                    else:
                        li.string = str(media_item)

                    media_ul.append(li)
                media_div.append(media_ul)
                section.append(media_div)

            container.append(section)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for holiday plan formatting."""
        style = soup.new_tag("style")
        style.string = """
        .holiday-plan-report {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .holiday-plan-report h2 {
            color: #2c5aa0;
            border-bottom: 2px solid #e1e8ed;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .holiday-plan-report h3 {
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .holiday-plan-report h4 {
            color: #7f8c8d;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        .introduction-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2c5aa0;
            margin-bottom: 20px;
        }
        .itinerary-day {
            background: #ffffff;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .accommodation-item, .dining-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #28a745;
        }
        .budget-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .budget-table th, .budget-table td {
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }
        .budget-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .budget-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .packing-category {
            background: #e9ecef;
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .safety-tips, .emergency-contacts, .useful-phrases {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .activities-list, .budget-items ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .timing-info, .travel-notes, .booking-info {
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px 0;
            font-size: 0.9em;
        }
        .sources ul, .media ul {
            list-style-type: none;
            padding-left: 0;
        }
        .sources li, .media li {
            background: #f8f9fa;
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: 4px;
            border-left: 3px solid #007bff;
        }
        .sources a, .media a {
            color: #007bff;
            text-decoration: none;
        }
        .sources a:hover, .media a:hover {
            text-decoration: underline;
        }
        @media (max-width: 768px) {
            .holiday-plan-report {
                padding: 10px;
            }
                .budget-table {
                font-size: 0.9em;
            }
                .budget-table th, .budget-table td {
                padding: 8px;
            }
        }
        """
        # Add style tag to the beginning of the container since we don't have a head
        container = soup.find("div", class_="holiday-plan-report")
        if container:
            container.insert(0, style)
        else:
            # Fallback: add to the soup directly
            soup.append(style)
