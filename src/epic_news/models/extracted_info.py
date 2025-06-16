from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    """A Pydantic model to store structured information extracted from a user's request."""

    main_subject_or_activity: Optional[str] = Field(
        default=None,
        description="The main subject or activity mentioned in the user request (e.g., 'cooking', 'travel', 'company research').",
    )
    topic: Optional[str] = Field(
        default=None,
        description="A general topic for the request, can be similar to the main subject.",
    )
    user_preferences_and_constraints: Optional[str] = Field(
        default=None,
        description="Specific user needs, preferences, or constraints (e.g., 'vegetarian meals, window seat').",
    )
    context: Optional[str] = Field(
        default=None, description="Additional context for the request."
    )
    objective: Optional[str] = Field(
        default=None, description="The primary objective of the request."
    )
    target_company: Optional[str] = Field(
        default=None,
        description="The name of the company that is the target of the request (e.g., 'Apple Inc.').",
    )
    company: Optional[str] = Field(
        default=None,
        description="The name of the company that is the target of the request (e.g., 'Apple Inc.').",
    )
    our_product: Optional[str] = Field(
        default=None,
        description="The product or service being offered or discussed, if any.",
    )
    destination_location: Optional[str] = Field(
        default=None,
        description="The final destination of the travel or event (e.g., 'Paris, France').",
    )
    origin_location: Optional[str] = Field(
        default=None, description="The starting point of the travel (e.g., 'New York, USA')."
    )
    traveler_details: Optional[str] = Field(
        default=None,
        description="Details about the people involved (e.g., '2 adults, 1 child').",
    )
    event_or_trip_duration: Optional[str] = Field(
        default=None, description="The duration of the event or trip (e.g., '3 days')."
    )
    participants: Optional[List[str]] = Field(
        default=None, description="A list of participants for an event or meeting."
    )
