"""
Factory function to convert a HolidayPlannerReport (or compatible dict) to HTML using TemplateManager.
Follows the deterministic pattern documented in docs/html_rendering_pattern.md.
"""

import os

from src.epic_news.models.holiday_planner_models import HolidayPlannerReport
from src.epic_news.utils.debug_utils import parse_crewai_output
from src.epic_news.utils.directory_utils import ensure_output_directory
from src.epic_news.utils.html.template_manager import TemplateManager


def holiday_planner_to_html(holiday_report, html_file=None):
    """
    Convert a HolidayPlannerReport to HTML using TemplateManager.

    Args:
        holiday_report: HolidayPlannerReport model, dict, or CrewOutput
        html_file: Optional path to write HTML file

    Returns:
        str: Generated HTML content
    """
    # Parse and validate the input data
    if hasattr(holiday_report, "raw"):
        # CrewOutput object
        parsed_data = parse_crewai_output(holiday_report, HolidayPlannerReport)
    elif isinstance(holiday_report, dict):
        # Normalize dict before validation
        def normalize_holiday_dict(data):
            transformed = dict(data)

            # 1. Introduction: dict with 'text' -> str
            if isinstance(transformed.get("introduction"), dict) and "text" in transformed["introduction"]:
                transformed["introduction"] = transformed["introduction"]["text"]

            # 2. Itinerary: ensure 'date' field exists in each day
            if "itinerary" in transformed and isinstance(transformed["itinerary"], list):
                for day_item in transformed["itinerary"]:
                    if isinstance(day_item, dict) and "date" not in day_item:
                        # Try to extract from day or title if possible
                        day_num = day_item.get("day", "")
                        title = day_item.get("title", "")
                        if title and isinstance(title, str) and ":" in title:
                            # Try to extract date from title like "Day 1: July 26"
                            date_part = title.split(":", 1)[1].strip()
                            day_item["date"] = date_part
                        else:
                            # Default date
                            day_item["date"] = f"Day {day_num}"

            # 3. Useful phrases: ensure 'local' and 'french' keys
            if isinstance(transformed.get("practical_information", {}), dict) and "useful_phrases" in transformed["practical_information"]:
                # Check if useful_phrases contains strings instead of objects
                new_phrases = []
                for phrase in transformed["practical_information"]["useful_phrases"]:
                    if isinstance(phrase, str):
                        # Convert string phrases to objects
                        parts = phrase.split('–') if '–' in phrase else phrase.split('-')
                        if len(parts) >= 2:
                            local_part = parts[0].strip()
                            french_part = parts[1].strip()
                            new_phrases.append({"local": local_part, "french": french_part})
                        else:
                            # Can't split, create default
                            new_phrases.append({"local": phrase, "french": phrase})
                    else:
                        # It's already an object, ensure required fields
                        if "local" not in phrase:
                            for lang_key in [
                                "italien",
                                "italian",
                                "espagnol",
                                "spanish",
                                "allemand",
                                "german",
                                "anglais",
                                "local",
                            ]:
                                if lang_key in phrase:
                                    phrase["local"] = phrase[lang_key]
                                    break
                            else:
                                phrase["local"] = "Phrase in local language"

                        if "french" not in phrase:
                            for fr_key in ["fr", "français", "francais", "french"]:
                                if fr_key in phrase:
                                    phrase["french"] = phrase[fr_key]
                                    break
                            else:
                                phrase["french"] = "Phrase in French"

                        new_phrases.append(phrase)

                # Replace the original phrases with normalized ones
                if new_phrases:
                    transformed["practical_information"]["useful_phrases"] = new_phrases

            # 4. Accommodations: ensure required fields
            if "accommodations" in transformed and isinstance(transformed["accommodations"], list):
                for accommodation in transformed["accommodations"]:
                    # Ensure description is present
                    if "description" not in accommodation:
                        accommodation["description"] = f"Accommodation {accommodation.get('name', 'Unknown')}"

                    # Ensure address is present
                    if "address" not in accommodation:
                        # Try to find address in other fields
                        if "location" in accommodation:
                            accommodation["address"] = accommodation["location"]
                        elif "adresse" in accommodation:
                            accommodation["address"] = accommodation["adresse"]
                        else:
                            # Default address
                            accommodation["address"] = f"Address for {accommodation.get('name', 'Unknown')}, Cinque Terre, Italy"

            # 5. Emergency contacts: ensure 'service' and 'number'
            if isinstance(transformed.get("practical_information", {}), dict) and "emergency_contacts" in transformed["practical_information"]:
                for contact in transformed["practical_information"]["emergency_contacts"]:
                    # Ensure service field exists
                    if "service" not in contact:
                        if "type" in contact:
                            contact["service"] = contact["type"]
                        else:
                            contact["service"] = "Emergency Service"

                    # Ensure number field exists
                    if "number" not in contact:
                        # Try to find number in alternative fields
                        for num_key in ["numéro", "numero", "phone", "telephone", "téléphone", "contact"]:
                            if num_key in contact:
                                contact["number"] = contact[num_key]
                                break
                        else:
                            # Default number if none found
                            contact["number"] = f"Contact number for {contact.get('service', 'Emergency Service')}"

            # 7. Sources: convert string sources to objects and ensure title field
            if "sources" in transformed and isinstance(transformed["sources"], list):
                new_sources = []
                for source in transformed["sources"]:
                    if isinstance(source, str):
                        new_sources.append({"title": "Travel Resource", "url": source, "type": "reference"})
                    else:
                        # Ensure title field exists
                        if "title" not in source:
                            if "name" in source:
                                source["title"] = source["name"]
                            else:
                                source["title"] = "Travel Resource"
                        new_sources.append(source)
                transformed["sources"] = new_sources

            return transformed

        normalized = normalize_holiday_dict(holiday_report)
        parsed_data = HolidayPlannerReport.model_validate(normalized)
    elif isinstance(holiday_report, HolidayPlannerReport):
        # Already a Pydantic model
        parsed_data = holiday_report
    else:
        raise ValueError(f"Unsupported holiday_report type: {type(holiday_report)}")

    # Generate HTML using TemplateManager
    template_manager = TemplateManager()
    html_content = template_manager.render_report(
        selected_crew="HOLIDAY_PLANNER", content_data=parsed_data.to_template_data()
    )

    # Write to file if requested
    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    return html_content
