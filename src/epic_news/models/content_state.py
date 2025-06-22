"""
Content state model for Epic News application.
This module defines the ContentState class which stores all state information
for the application during execution.
"""

import datetime
from typing import Any

from pydantic import BaseModel, Field

from epic_news.models.extracted_info import ExtractedInfo


class ContentState(BaseModel):
    # Basic request information
    user_request: str = "Get the RSS Weekly Report"
    extracted_info: ExtractedInfo | None = None
    selected_crew: str = ""  # Default crew type
    attachment_file: str = ""  # Attachment file for specific crew types
    current_year: str = str(datetime.datetime.now().year)  # Current year
    categories:  dict = Field(default_factory=lambda: {
        "SALES_PROSPECTING": "SALES_PROSPECTING",
        "COOKING": "COOKING",
        "HOLIDAY_PLANNER": "HOLIDAY_PLANNER",
        "LEAD_SCORING": "LEAD_SCORING",
        "LIBRARY": "LIBRARY",
        "LOCATION": "LOCATION",
        "MEETING_PREP": "MEETING_PREP",
        "NEWSCOMPANY": "NEWSCOMPANY",
        "OPEN_SOURCE_INTELLIGENCE": "OPEN_SOURCE_INTELLIGENCE",
        "POEM": "POEM",
        "SHOPPING": "SHOPPING",
        "UNKNOWN": "UNKNOWN",
        "MARKETING_WRITERS": "MARKETING_WRITERS",
        "POST_ONLY": "POST_ONLY",
        "RSS": "RSS",
        "FINDAILY": "FINDAILY",
        "NEWSDAILY": "NEWSDAILY",
    })
    # Output file path
    output_file: str = ""

    # Crew results
    company_profile: Any | None = None
    tech_stack: Any | None = None # Stores direct output from TechStackCrew
    geospatial_analysis: Any | None = None
    post_report: Any | None = None
    poem: Any | None = None
    news_report: Any | None = None
    rss_weekly_report: Any | None = None
    location_report: Any | None = None
    recipe: Any | None = None
    book_summary: Any | None = None
    shopping_advice_report: Any | None = None
    meeting_prep_report: Any | None = None
    final_report: str | None = None  # Stores the final consolidated report or error message
    contact_info_report: Any | None = None # Renamed from contacts_report
    holiday_plan: Any | None = None
    marketing_report: Any | None = None
    osint_report: Any | None = None # Potentially for a consolidated OSINT report
    tech_stack_report: Any | None = None # Potentially for a formatted tech stack report
    hr_intelligence_report: Any | None = None
    legal_analysis_report: Any | None = None
    web_presence_report: Any | None = None
    cross_reference_report: Any | None = None
    lead_score_report: Any | None = None # Added from the duplicated block
    fin_daily_report: Any | None = None  # Stores the FinDaily crew report
    news_daily_report: Any | None = None  # Stores the NewsDaily crew report

    # Email settings
    sendto: str = "fred.jacquet@gmail.com"
    email_sent: bool = False
    error_message: str = ""

    # Additional parameters
    sentence_count: int = 5

    # Company and product parameters (used by both ContactFinder and MeetingPrep)
    our_product: str = ""

    # Meeting prep specific parameters
    participants: list = [
        "John Doe <john.doe@pictet.com> - CEO",
        "Jane Smith <jane.smith@pictet.com> - CTO",
        "Bob Johnson <bob.johnson@pictet.com> - Sales Director"
    ]
    context: str = ""
    objective: str = ""
    prior_interactions: str = ""



    def to_crew_inputs(self) -> dict:
        """
        Prepares a flattened dictionary of state properties suitable for CrewAI task inputs.
        This method combines top-level state attributes with nested data from the
        'extracted_info' model, providing a simple, flat key-value structure.
        """
        # Start with a dump of the top-level model, excluding the nested part.
        inputs = self.model_dump(exclude={"extracted_info"})

        # If extracted_info exists, flatten its contents into the inputs dictionary.
        if self.extracted_info:
            extracted_data = self.extracted_info.model_dump()
            # Map from the Pydantic model field names to the keys crews expect.
            mapping = {
                "main_subject_or_activity": "topic",
                "target_company": "company",
                "destination_location": "destination",
                "event_or_trip_duration": "duration",
                "traveler_details": "family",
                "origin_location": "origin",
                "user_preferences_and_constraints": "special_needs",
                "participants": "participants",
                "meeting_context": "context",
                "meeting_objective": "objective",
                "prior_interactions": "prior_interactions",
            }
            for source_key, target_key in mapping.items():
                if source_key in extracted_data:
                    inputs[target_key] = extracted_data[source_key]

        # Add a generic 'target' field for crews that need it.
        if inputs.get("company"):
            inputs["target"] = inputs["company"]
        elif inputs.get("topic"):
            inputs["target"] = inputs["topic"]

        # Return a clean dictionary, removing any keys that have None values.
        return {k: v for k, v in inputs.items() if v is not None}
