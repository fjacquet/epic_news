from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    """A Pydantic model to store structured information extracted from a user's request."""
    destination_location: Optional[str] = Field(
        default=None, 
        description="The final destination of the travel or event (e.g., 'Paris, France')."
    )
    origin_location: Optional[str] = Field(
        default=None, 
        description="The starting point of the travel (e.g., 'New York, USA')."
    )
    target_company_name: Optional[str] = Field(
        default=None, 
        description="The name of a company mentioned as the subject of the request (e.g., 'Apple Inc.')."
    )
    user_preferences_and_constraints: Optional[str] = Field(
        default=None, 
        description="Specific user needs, preferences, or constraints (e.g., 'vegetarian meals, window seat')."
    )
    traveler_details: Optional[str] = Field(
        default=None, 
        description="Details about the people involved (e.g., '2 adults, 1 child')."
    )
    event_or_trip_duration: Optional[str] = Field(
        default=None, 
        description="The duration of the event or trip (e.g., '3 days')."
    )
    main_subject_or_activity: Optional[str] = Field(
        default=None, 
        description="The primary topic or activity of the request (e.g., 'business conference', 'skiing holiday')."
    )
    budget_notes: Optional[str] = Field(
        default=None, 
        description="Any comments or constraints regarding the budget (e.g., 'looking for budget-friendly options')."
    )
    requested_dates_or_timeframe: Optional[str] = Field(
        default=None, 
        description="Specific dates or timeframes mentioned (e.g., 'the last week of July 2024')."
    )
    participants: Optional[List[str]] = Field(
        default=None,
        description="A list of strings, where each string represents a participant and their details (e.g., ['John Doe (CEO of Sicpa)', 'Jane Smith (our Head of Sales)'])."
    )
    meeting_context: Optional[str] = Field(
        default=None,
        description="The broader context or background for the meeting (e.g., 'Follow-up to Q3 review', 'Initial discussion about partnership')."
    )
    prior_interactions: Optional[str] = Field(
        default=None,
        description="Summary of any previous communications or interactions relevant to this meeting (e.g., 'Discussed pricing in last call', 'Met at conference in June')."
    )
    meeting_objective: Optional[str] = Field(
        default=None,
        description="The primary goal or desired outcome of the meeting (e.g., 'Secure a deal', 'Finalize project scope', 'Gather requirements')."
    )
