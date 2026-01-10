from pydantic import BaseModel, Field


class ExtractedInfo(BaseModel):
    """A Pydantic model to store structured information extracted from a user's request."""

    main_subject_or_activity: str | None = Field(
        default=None,
        description="The main subject or activity mentioned in the user request (e.g., 'cooking', 'travel', 'company research').",
    )
    topic: str | None = Field(
        default=None,
        description="A general topic for the request, can be similar to the main subject.",
    )
    user_preferences_and_constraints: str | None = Field(
        default=None,
        description="Specific user needs, preferences, or constraints (e.g., 'vegetarian meals, window seat').",
    )
    context: str | None = Field(default=None, description="Additional context for the request.")
    objective: str | None = Field(default=None, description="The primary objective of the request.")
    target_company: str | None = Field(
        default=None,
        description="The name of the company that is the target of the request (e.g., 'Apple Inc.').",
    )
    company: str | None = Field(
        default=None,
        description="The name of the company that is the target of the request (e.g., 'Apple Inc.').",
    )
    our_product: str | None = Field(
        default=None,
        description="The product or service being offered or discussed, if any.",
    )
    destination_location: str | None = Field(
        default=None,
        description="The final destination of the travel or event (e.g., 'Paris, France').",
    )
    origin_location: str | None = Field(
        default=None, description="The starting point of the travel (e.g., 'New York, USA')."
    )
    traveler_details: str | None = Field(
        default=None,
        description="Details about the people involved (e.g., '2 adults, 1 child').",
    )
    event_or_trip_duration: str | None = Field(
        default=None, description="The duration of the event or trip (e.g., '3 days')."
    )
    participants: list[str] | None = Field(
        default=None, description="A list of participants for an event or meeting."
    )
