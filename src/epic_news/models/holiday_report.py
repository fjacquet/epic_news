"""Small, bounded models for the fragment-based holiday report."""

from pydantic import BaseModel, Field


class ItineraryDay(BaseModel):
    date: str = Field(default="", description="Human date label for the day")
    label: str = Field(default="", description="Short title for the day")
    stops: list[str] = Field(default_factory=list, description="Key stops/locations")


class ItinerarySkeleton(BaseModel):
    days: list[ItineraryDay] = Field(default_factory=list)
