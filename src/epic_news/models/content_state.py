"""
Content state model for Epic News application.
This module defines the ContentState class which stores all state information
for the application during execution.
"""

import datetime
from typing import Any, Union

from pydantic import BaseModel, Field

from epic_news.models.crews.shopping_advice_report import ShoppingAdviceOutput
from epic_news.models.extracted_info import ExtractedInfo
from epic_news.utils.menu_generator import MenuGenerator
from epic_news.utils.string_utils import create_topic_slug


# Constants for crew categories
class CrewCategories:
    """Constants for available crew categories."""

    SALES_PROSPECTING = "SALES_PROSPECTING"
    COOKING = "COOKING"
    HOLIDAY_PLANNER = "HOLIDAY_PLANNER"
    LEAD_SCORING = "LEAD_SCORING"
    BOOK_SUMMARY = "BOOK_SUMMARY"
    LOCATION = "LOCATION"
    MARKETING_WRITERS = "MARKETING_WRITERS"
    MEETING_PREP = "MEETING_PREP"
    MENU = "MENU"
    COMPANY_NEWS = "COMPANY_NEWS"
    OPEN_SOURCE_INTELLIGENCE = "OPEN_SOURCE_INTELLIGENCE"
    POEM = "POEM"
    POST_ONLY = "POST_ONLY"
    RSS = "RSS"
    FINDAILY = "FINDAILY"
    NEWSDAILY = "NEWSDAILY"
    SAINT = "SAINT"
    SHOPPING = "SHOPPING"
    SHOPPING_ADVISOR = "SHOPPING_ADVISOR"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def to_dict(cls) -> dict[str, str]:
        """Convert crew categories to dictionary format."""
        return {
            name: getattr(cls, name) for name in dir(cls) if not name.startswith("_") and name != "to_dict"
        }


# Default values
DEFAULT_EMAIL = "fred.jacquet@gmail.com"
DEFAULT_PARTICIPANTS = [
    "John Doe <john.doe@pictet.com> - CEO",
    "Jane Smith <jane.smith@pictet.com> - CTO",
    "Bob Johnson <bob.johnson@pictet.com> - Sales Director",
]

# Template paths
MENU_REPORT_TEMPLATE = "templates/menu_report_template.html"


class ContentState(BaseModel):
    """
    Central state management for Epic News application.

    This class organizes all application state into logical groups:
    - Request Information: User input and extracted data
    - Crew Configuration: Selected crew and parameters
    - Crew Results: Output from various crew executions
    - Communication: Email and notification settings
    - Meeting Preparation: Specific parameters for meeting prep crews
    """

    # ============================================================================
    # REQUEST INFORMATION
    # ============================================================================
    user_request: str = "Get the RSS Weekly Report"
    extracted_info: Union[ExtractedInfo, None] = None
    attachment_file: str = ""
    current_year: str = str(datetime.datetime.now().year)
    topic_slug: str = ""

    # ============================================================================
    # CREW CONFIGURATION
    # ============================================================================
    selected_crew: str = ""
    categories: dict = Field(default_factory=CrewCategories.to_dict)
    output_file: str = ""
    output_dir: str = ""
    sentence_count: int = 5

    # ============================================================================
    # CREW RESULTS - Core Reports
    # ============================================================================
    final_report: Union[str, None] = None
    error_message: str = ""

    # Business Intelligence Reports
    company_profile: Union[Any, None] = None
    tech_stack: Union[Any, None] = None
    tech_stack_report: Union[Any, None] = None
    contact_info_report: Union[Any, None] = None
    lead_score_report: Union[Any, None] = None

    # Analysis Reports
    geospatial_analysis: Union[Any, None] = None
    osint_report: Union[Any, None] = None
    hr_intelligence_report: Union[Any, None] = None
    legal_analysis_report: Union[Any, None] = None
    web_presence_report: Union[Any, None] = None
    cross_reference_report: Union[Any, None] = None

    # Content Reports
    news_report: Union[Any, None] = None
    company_news_report: Union[Any, None] = None
    rss_weekly_report: Union[Any, None] = None
    fin_daily_report: Union[Any, None] = None
    news_daily_report: Union[Any, None] = None
    saint_daily_report: Union[Any, None] = None
    post_report: Union[Any, None] = None
    marketing_report: Union[Any, None] = None

    # Specialized Reports
    location_report: Union[Any, None] = None
    holiday_plan: Union[Any, None] = None
    recipe: Union[Any, None] = None
    menu_designer_report: Union[Any, None] = None
    book_summary: Union[Any, None] = None
    shopping_advice_report: Union[Any, None] = None
    shopping_advice_model: Union[ShoppingAdviceOutput, None] = None
    poem: Union[Any, None] = None
    meeting_prep_report: Union[Any, None] = None

    # NEW: Model-based state fields for refactored architecture
    financial_report_model: Union[Any, None] = None
    news_daily_model: Union[Any, None] = None
    saint_daily_model: Union[Any, None] = None

    # ============================================================================
    # COMMUNICATION SETTINGS
    # ============================================================================
    sendto: str = DEFAULT_EMAIL
    email_sent: bool = False

    # ============================================================================
    # MEETING PREPARATION PARAMETERS
    # ============================================================================
    our_product: str = ""
    participants: list = Field(default_factory=lambda: DEFAULT_PARTICIPANTS.copy())
    context: str = ""
    objective: str = ""
    prior_interactions: str = ""

    def to_crew_inputs(self) -> dict:
        """
        Prepares a flattened dictionary of state properties suitable for CrewAI task inputs.

        This method combines top-level state attributes with nested data from the
        'extracted_info' model, providing a simple, flat key-value structure.

        Returns:
            dict: Flattened dictionary with all necessary inputs for crew execution
        """
        # Start with a dump of the top-level model, excluding the nested part
        inputs = self.model_dump(exclude={"extracted_info"})

        # Flatten extracted_info if it exists
        if self.extracted_info:
            inputs.update(self._flatten_extracted_info())

        # Add computed fields
        inputs.update(self._add_computed_fields())

        # Add menu-specific mappings
        inputs.update(self._add_menu_mappings(inputs))

        # Ensure required placeholders always exist to prevent CrewAI KeyError
        for required_key in [
            "user_preferences_and_constraints",
            "context",
        ]:
            inputs.setdefault(required_key, "")

        # Return clean dictionary, removing None values but keeping required placeholders
        return {k: v for k, v in inputs.items() if v is not None}

    def _flatten_extracted_info(self) -> dict:
        """Flatten extracted_info into crew input format."""
        extracted_data = self.extracted_info.model_dump()

        # DEBUG: Log extracted_data to understand the mapping issue
        print("🔍 DEBUG _flatten_extracted_info:")
        print(f"  extracted_data keys: {list(extracted_data.keys())}")
        print(f"  main_subject_or_activity value: {extracted_data.get('main_subject_or_activity')}")

        # Mapping from Pydantic model field names to crew input keys
        field_mapping = {
            "main_subject_or_activity": "topic",
            "target_company": "company",
            "destination_location": "destination",
            "event_or_trip_duration": "duration",
            "traveler_details": "family",
            "origin_location": "origin",
            # Map to the new explicit key used in task templates
            "user_preferences_and_constraints": "user_preferences_and_constraints",
            "participants": "participants",
            "meeting_context": "context",
            "meeting_objective": "objective",
            "prior_interactions": "prior_interactions",
        }

        flattened: dict[str, Any] = {}
        for source_key, target_key in field_mapping.items():
            if source_key in extracted_data:
                value = extracted_data[source_key]
                print(f"  Mapping {source_key} -> {target_key}: {value}")
                # Always map the value, even if target_key already exists
                flattened[target_key] = value
            else:
                print(f"  Missing key: {source_key}")

        # Special handling: if topic is null but main_subject_or_activity has a value, use it
        if flattened.get("topic") is None and extracted_data.get("main_subject_or_activity"):
            flattened["topic"] = extracted_data["main_subject_or_activity"]
            print(f"  🔧 Fixed null topic with main_subject_or_activity: {flattened['topic']}")

        print(f"  Final flattened: {flattened}")
        return flattened

    def _add_computed_fields(self) -> dict:
        """Add computed fields like season and current date."""
        menu_generator = MenuGenerator()
        current_date = datetime.datetime.now()

        return {
            "season": menu_generator.calculate_season(),
            "current_date": current_date.strftime("%Y-%m-%d"),
        }

    def _add_menu_mappings(self, inputs: dict) -> dict:
        """Add menu-specific mappings with defaults."""
        # Add a generic 'target' field for crews that need it
        target = inputs.get("company") or inputs.get("topic")

        menu_mappings = {}
        if target:
            menu_mappings["target"] = target

        # Menu-specific mappings with defaults
        menu_mappings.update(
            {
                "constraints": inputs.get("user_preferences_and_constraints")
                or inputs.get("user_request", "none"),
                "preferences": inputs.get("user_preferences_and_constraints")
                or inputs.get("user_request", "none"),
                "user_context": inputs.get("topic") or inputs.get("user_request", "menu planning"),
            }
        )

        if "menu_slug" not in inputs:
            if "start_date" in inputs:
                menu_mappings["menu_slug"] = f"menu_{inputs['start_date']}"
            else:
                menu_mappings["menu_slug"] = f"menu_{create_topic_slug('weekly_menu')}"

        # Add template path for HTML generation
        menu_mappings["template_path"] = MENU_REPORT_TEMPLATE

        # Add topic_slug for recipes if needed
        if "topic_slug" not in inputs and "topic" in inputs:
            topic_slug = create_topic_slug(inputs["topic"])
            print(f"  🏷️  Generated topic_slug from topic '{inputs['topic']}': {topic_slug}")
            menu_mappings["topic_slug"] = topic_slug
        elif "topic_slug" not in inputs:
            topic_slug = create_topic_slug("recipe")
            print(f"  🏷️  Generated fallback topic_slug: {topic_slug}")
            menu_mappings["topic_slug"] = topic_slug
        else:
            print(f"  🏷️  topic_slug already exists: {inputs.get('topic_slug')}")

        return menu_mappings
