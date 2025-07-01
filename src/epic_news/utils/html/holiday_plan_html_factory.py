"""
Factory function for converting HolidayPlan to HTML using the universal template system.
"""

from __future__ import annotations

from crewai import CrewOutput

from epic_news.models.holiday_plan import Budget, HolidayPlan, PracticalInfo
from epic_news.utils.html.template_manager import TemplateManager


def holiday_plan_to_html(crew_output: CrewOutput, html_file: str | None = None) -> str:
    """
    Convert a CrewOutput containing holiday plan JSON to a complete HTML document using the universal template system.

    Args:
        crew_output (CrewOutput): The CrewAI output containing holiday plan JSON data.
        html_file (str|None): Optional file path to write the HTML output.

    Returns:
        str: Complete HTML document as a string.
    """
    # Parse the crew output JSON into HolidayPlan model
    try:
        # Get the raw output from CrewOutput
        raw_output = crew_output.raw if hasattr(crew_output, "raw") else str(crew_output)
        print(f"🔍 DEBUG: Raw output type: {type(raw_output)}")
        print(f"🔍 DEBUG: Raw output preview: {str(raw_output)[:500]}...")

        # Parse JSON string into HolidayPlan model
        import json

        json_data = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        print(
            f"🔍 DEBUG: JSON data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}"
        )

        # Try to create HolidayPlan model
        holiday_plan = HolidayPlan(**json_data)
        print("✅ Successfully parsed HolidayPlan model")

    except Exception as e:
        print(f"❌ ERROR parsing HolidayPlan: {str(e)}")
        print(f"❌ ERROR type: {type(e).__name__}")

        # Instead of fallback, let's try to work with the raw JSON data directly
        try:
            import json

            json_data = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
            print("🔧 Using raw JSON data directly for rendering")

            # Use TemplateManager directly with raw JSON data
            template_manager = TemplateManager()
            html = template_manager.render_report("HOLIDAY_PLANNER", json_data)

            if html_file:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html)

            return html

        except Exception as e2:
            print(f"❌ ERROR with raw JSON fallback: {str(e2)}")
            # Final fallback: create a basic holiday plan with error info
            holiday_plan = HolidayPlan(
                introduction=f"Erreur lors du parsing des données du plan de vacances: {str(e)}. Erreur fallback: {str(e2)}",
                itinerary=[],
                accommodations=[],
                dining=[],
                budget=Budget(),
                practical_information=PracticalInfo(),
                sources=[],
                media=[],
            )

    # Prepare content_data as expected by TemplateManager
    content_data = holiday_plan.to_template_data()
    template_manager = TemplateManager()
    html = template_manager.render_report("HOLIDAY_PLANNER", content_data)

    if html_file:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

    return html
