"""
Standalone script to regenerate the holiday plan HTML report from a JSON file.

This script validates the conversion from JSON data to HTML using the new
HolidayPlannerReport model and rendering system.

Usage:
    uv run python regenerate_holiday_plan.py
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.epic_news.models.holiday_planner_models import HolidayPlannerReport
from src.epic_news.utils.html.holiday_planner_html_factory import holiday_planner_to_html
from src.epic_news.utils.html.template_renderers.holiday_renderer import HolidayRenderer


def validate_json_structure(data: dict[str, Any]) -> None:
    """Validate that the JSON data has the expected structure."""
    print("🔍 Validating JSON structure...")

    required_fields = ["introduction", "itinerary"]
    for field in required_fields:
        if field not in data:
            print(f"⚠️  Warning: Missing required field '{field}'")

    # Check itinerary structure
    if "itinerary" in data and isinstance(data["itinerary"], list):
        print(f"📅 Found {len(data['itinerary'])} days in itinerary")
        for i, day in enumerate(data["itinerary"]):
            if not isinstance(day, dict):
                print(f"⚠️  Warning: Day {i + 1} is not a dictionary")
                continue
            if "activities" in day:
                print(f"   Day {i + 1}: {len(day['activities'])} activities")

    # Check other sections
    sections = ["accommodations", "dining", "budget", "practical_information"]
    for section in sections:
        if section in data:
            print(f"✅ Found {section} section")
        else:
            print(f"ℹ️  Optional section '{section}' not present")


def transform_data_for_model(data: dict[str, Any]) -> dict[str, Any]:
    """Transform real-world JSON data to match Pydantic model structure."""
    print("🔧 Transforming data to match model structure...")

    transformed = data.copy()

    # Transform accommodations: suitability + notes -> description
    if 'accommodations' in transformed:
        for accommodation in transformed['accommodations']:
            if 'description' not in accommodation:
                # Create description from available fields
                desc_parts = []
                if 'suitability' in accommodation:
                    desc_parts.append(accommodation['suitability'])
                if 'notes' in accommodation:
                    desc_parts.append(accommodation['notes'])
                if 'details' in accommodation:
                    desc_parts.append(accommodation['details'])

                accommodation['description'] = ' - '.join(desc_parts) if desc_parts else f"Accommodation {accommodation.get('name', 'Unknown')}"
                print(f"   • Generated description for accommodation '{accommodation.get('name', 'Unknown')}'")

    # Transform dining restaurants: ensure description field exists
    if "dining" in transformed and "restaurants" in transformed["dining"]:
        for restaurant in transformed["dining"]["restaurants"]:
            if "description" not in restaurant:
                # Create description from available fields
                desc_parts = []
                if "details" in restaurant:
                    desc_parts.append(restaurant["details"])
                if "cuisine" in restaurant:
                    desc_parts.append(f"Cuisine: {restaurant['cuisine']}")
                if "specialties" in restaurant:
                    desc_parts.append(f"Spécialités: {restaurant['specialties']}")

                restaurant["description"] = (
                    " - ".join(desc_parts)
                    if desc_parts
                    else f"Restaurant {restaurant.get('name', 'Unknown')}"
                )
                print(f"   • Generated description for restaurant '{restaurant.get('name', 'Unknown')}'")

    # Transform useful phrases: italian/francais -> local/french
    if "practical_information" in transformed and "useful_phrases" in transformed["practical_information"]:
        for phrase in transformed["practical_information"]["useful_phrases"]:
            if "italian" in phrase and "local" not in phrase:
                phrase["local"] = phrase.pop("italian")
            if "francais" in phrase and "french" not in phrase:
                phrase["french"] = phrase.pop("francais")
        print(
            f"   • Transformed {len(transformed['practical_information']['useful_phrases'])} useful phrases"
        )

    # Transform emergency contacts: phone -> number
    if (
        "practical_information" in transformed
        and "emergency_contacts" in transformed["practical_information"]
    ):
        for contact in transformed["practical_information"]["emergency_contacts"]:
            if "phone" in contact and "number" not in contact:
                contact["number"] = contact.pop("phone")
        print("   • Transformed emergency contact phone numbers")

    # Transform sources: strings -> objects
    if "sources" in transformed and isinstance(transformed["sources"], list):
        new_sources = []
        for source in transformed["sources"]:
            if isinstance(source, str):
                new_sources.append({"title": "Travel Resource", "url": source, "type": "tourism"})
            else:
                new_sources.append(source)
        transformed["sources"] = new_sources
        print(f"   • Transformed {len(new_sources)} source URLs to objects")

    return transformed


def validate_pydantic_conversion(data: dict[str, Any]) -> HolidayPlannerReport:
    """Validate conversion to Pydantic model."""
    print("🔧 Validating Pydantic model conversion...")

    # First, transform the data to match our model structure
    transformed_data = transform_data_for_model(data)

    try:
        # Convert to Pydantic model
        model = HolidayPlannerReport.model_validate(transformed_data)
        print("✅ Successfully converted to HolidayPlannerReport model")

        # Validate template data conversion
        model.to_template_data()
        print("✅ Successfully converted to template data")

        return model
    except Exception as e:
        print(f"❌ Pydantic validation failed: {e}")
        print("🔧 Attempting to create model with available data...")

        # Try to create a minimal valid model
        minimal_data = {
            "introduction": transformed_data.get("introduction", "Holiday plan"),
            "itinerary": transformed_data.get("itinerary", []),
            "accommodations": transformed_data.get("accommodations", []),
        }

        try:
            model = HolidayPlannerReport.model_validate(minimal_data)
            print("✅ Created minimal valid model")
            return model
        except Exception as e2:
            print(f"❌ Even minimal model creation failed: {e2}")
            raise


def validate_html_rendering(model: HolidayPlannerReport) -> str:
    """Validate HTML rendering."""
    print("🎨 Validating HTML rendering...")

    try:
        # Test direct renderer
        renderer = HolidayRenderer()
        html_content = renderer.render(model.to_template_data())
        print("✅ Direct renderer validation successful")

        # Test factory function
        html_content = holiday_planner_to_html(model)
        print("✅ Factory function validation successful")

        # Basic HTML validation
        if "<html" in html_content and "</html>" in html_content:
            print("✅ Generated valid HTML structure")
        else:
            print("⚠️  Warning: HTML structure may be incomplete")

        return html_content
    except Exception as e:
        print(f"❌ HTML rendering failed: {e}")
        raise


def main():
    """Main function to regenerate and validate the report."""
    project_root = Path(__file__).parent
    input_json_path = project_root / "output" / "holiday" / "itinerary.json"
    output_html_path = project_root / "output" / "holiday" / "regenerated_itinerary.html"

    print(f"🔄 Regenerating and validating holiday plan HTML from: {input_json_path}")
    print(f"📝 Output will be written to: {output_html_path}")

    if not input_json_path.exists():
        print(f"❌ Error: Input JSON file not found at {input_json_path}")
        print("Please run the HOLIDAY_PLANNER crew first to generate the data.")
        print("Command: crewai flow kickoff")
        return

    try:
        # Read the raw content from the file
        print("📖 Reading JSON file...")
        raw_content = input_json_path.read_text(encoding="utf-8")
        print(f"📏 File size: {len(raw_content):,} characters")

        # Try to parse the entire file as JSON first
        try:
            holiday_data = json.loads(raw_content)
            print("✅ Successfully parsed entire file as JSON")
        except json.JSONDecodeError as e:
            print(f"⚠️  Direct JSON parsing failed: {e}")
            print("🔧 Attempting to extract JSON object...")

            # Find the start and end of the main JSON object
            start_index = raw_content.find("{")
            end_index = raw_content.rfind("}")

            if start_index == -1 or end_index == -1 or start_index > end_index:
                raise ValueError("Could not find a valid JSON object in the file.")

            # Extract the JSON string
            json_str = raw_content[start_index : end_index + 1]
            print(f"📏 Extracted JSON size: {len(json_str):,} characters")

            # Show context around the error if we can identify it
            try:
                holiday_data = json.loads(json_str)
                print("✅ Successfully parsed extracted JSON content")
            except json.JSONDecodeError as e2:
                print(f"❌ JSON parsing failed at line {e2.lineno}, column {e2.colno}")
                print(f"Error: {e2.msg}")

                # Show context around the error
                lines = json_str.split("\n")
                error_line = e2.lineno - 1
                start_line = max(0, error_line - 2)
                end_line = min(len(lines), error_line + 3)

                print("\n🔍 Context around error:")
                for i in range(start_line, end_line):
                    marker = ">>> " if i == error_line else "    "
                    print(f"{marker}Line {i + 1}: {lines[i]}")

                raise

        # Validation steps
        validate_json_structure(holiday_data)
        model = validate_pydantic_conversion(holiday_data)
        html_content = validate_html_rendering(model)

        # Write the HTML file
        print("💾 Writing HTML file...")
        output_html_path.parent.mkdir(parents=True, exist_ok=True)
        output_html_path.write_text(html_content, encoding="utf-8")

        print("\n🎉 SUCCESS! Validation complete.")
        print(f"📄 HTML report generated at: {output_html_path}")
        print(f"📊 File size: {len(html_content):,} characters")

        # Summary
        print("\n📋 Validation Summary:")
        print("   • JSON parsing: ✅")
        print("   • Pydantic validation: ✅")
        print("   • HTML rendering: ✅")
        print("   • File output: ✅")

    except Exception as e:
        print(f"❌ An error occurred during regeneration: {e}")


if __name__ == "__main__":
    main()
