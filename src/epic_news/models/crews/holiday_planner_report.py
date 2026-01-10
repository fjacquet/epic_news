"""
Holiday Planner Models

Pydantic models for holiday planner data structures.
Based on the format_and_translate_guide task output structure.
"""

import json
from typing import Any

from pydantic import BaseModel, Field


class Activity(BaseModel):
    """Individual activity within a day's itinerary."""

    time: str = Field(..., description="Time range for the activity (e.g., '9:00-10:00')")
    description: str = Field(..., description="Detailed description of the activity")


class DayItinerary(BaseModel):
    """Single day in the travel itinerary."""

    day: int = Field(..., description="Day number")
    date: str = Field(..., description="Date of the day")
    activities: list[Activity] = Field(default_factory=list, description="List of activities for the day")


class Accommodation(BaseModel):
    """Accommodation recommendation."""

    name: str = Field(..., description="Name of the accommodation")
    address: str = Field(..., description="Full address")
    contact_booking: str | None = Field(None, description="Contact or booking information")
    price_range: str | None = Field(None, description="Price range or estimate")
    description: str = Field(..., description="Why this accommodation is suitable")
    amenities: list[str] | None = Field(default_factory=list, description="Available amenities")
    accessibility: str | None = Field(None, description="Accessibility information")


class Restaurant(BaseModel):
    """Restaurant or dining recommendation."""

    name: str = Field(..., description="Restaurant name")
    location: str = Field(..., description="Location or address")
    cuisine: str | None = Field(None, description="Type of cuisine")
    price_range: str | None = Field(None, description="Price range")
    description: str = Field(..., description="Description and specialties")
    dietary_options: list[str] | None = Field(default_factory=list, description="Dietary accommodations")
    contact: str | None = Field(None, description="Contact information")
    reservation_required: bool | None = Field(None, description="Whether reservation is required")


class DiningSection(BaseModel):
    """Dining recommendations section."""

    restaurants: list[Restaurant] = Field(default_factory=list, description="Restaurant recommendations")
    local_specialties: list[str] | None = Field(
        default_factory=list, description="Local food specialties to try"
    )
    dietary_notes: str | None = Field(None, description="General dietary accommodation notes")


class BudgetItem(BaseModel):
    """Individual budget item."""

    category: str = Field(..., description="Budget category (e.g., 'Transport', 'Accommodation')")
    item: str = Field(..., description="Specific item or service")
    cost: str | float | None = Field(..., description="Cost amount")
    currency: str = Field(default="CHF", description="Currency")
    notes: str | None = Field(None, description="Additional notes about the cost")


class BudgetSummary(BaseModel):
    """Complete budget breakdown."""

    items: list[BudgetItem] = Field(default_factory=list, description="Individual budget items")
    total_estimated: str | float | None = Field(None, description="Total estimated cost")
    currency: str = Field(default="CHF", description="Currency for totals")
    notes: str | None = Field(None, description="General budget notes")


class PackingChecklist(BaseModel):
    """Categorized packing checklist."""

    vetements: list[str] | None = Field(default_factory=list, description="Clothing items")
    documents: list[str] | None = Field(default_factory=list, description="Important documents")
    toiletries: list[str] | None = Field(default_factory=list, description="Toiletry items")
    electronics: list[str] | None = Field(default_factory=list, description="Electronic devices")
    medical: list[str] | None = Field(default_factory=list, description="Medical supplies")
    activities: list[str] | None = Field(default_factory=list, description="Activity-specific items")
    children: list[str] | None = Field(default_factory=list, description="Items for children")


class EmergencyContact(BaseModel):
    """Emergency contact information."""

    service: str = Field(..., description="Type of service (e.g., 'Police', 'Medical')")
    number: str = Field(..., description="Phone number")
    notes: str | None = Field(None, description="Additional information")


class UsefulPhrase(BaseModel):
    """Useful local phrase."""

    french: str = Field(..., description="French phrase")
    local: str = Field(..., description="Local language phrase")
    pronunciation: str | None = Field(None, description="Pronunciation guide")


class PracticalInformation(BaseModel):
    """Practical travel information."""

    packing_checklist: PackingChecklist | None = Field(None, description="Categorized packing list")
    safety_tips: list[str] | None = Field(
        default_factory=list, description="Safety tips and local customs"
    )
    emergency_contacts: list[EmergencyContact] | None = Field(
        default_factory=list, description="Emergency contact numbers"
    )
    useful_phrases: list[UsefulPhrase] | None = Field(
        default_factory=list, description="Useful local phrases"
    )
    local_customs: list[str] | None = Field(default_factory=list, description="Important local customs")
    transportation_tips: list[str] | None = Field(
        default_factory=list, description="Transportation advice"
    )


class MediaItem(BaseModel):
    """Media item (image or video)."""

    url: str = Field(..., description="URL to the media")
    caption: str | None = Field(None, description="Caption or description")
    type: str = Field(default="image", description="Type of media (image, video)")


class Source(BaseModel):
    """Information source."""

    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    type: str | None = Field(None, description="Type of source (booking, attraction, tourism)")


class HolidayPlannerReport(BaseModel):
    """Complete holiday planner report structure."""

    table_of_contents: list[str] | None = Field(default_factory=list, description="Table of contents")
    introduction: str = Field(..., description="Detailed introduction to the destination")
    itinerary: list[DayItinerary] = Field(default_factory=list, description="Day-by-day itinerary")
    accommodations: list[Accommodation] = Field(
        default_factory=list, description="Accommodation recommendations"
    )
    dining: DiningSection | None = Field(None, description="Dining recommendations")
    budget: BudgetSummary | None = Field(None, description="Budget breakdown and analysis")
    practical_information: PracticalInformation | None = Field(
        None, description="Practical travel information"
    )
    sources: list[Source] | None = Field(default_factory=list, description="Information sources")
    media: list[MediaItem] | None = Field(default_factory=list, description="Images and videos")

    def to_template_data(self) -> dict[str, Any]:
        """Convert to template-friendly data structure."""
        return {
            "table_of_contents": self.table_of_contents,
            "introduction": self.introduction,
            "itinerary": [day.model_dump() for day in self.itinerary],
            "accommodations": [acc.model_dump() for acc in self.accommodations],
            "dining": self.dining.model_dump() if self.dining else None,
            "budget": self.budget.model_dump() if self.budget else None,
            "practical_information": self.practical_information.model_dump()
            if self.practical_information
            else None,
            "sources": [source.model_dump() for source in self.sources] if self.sources else [],
            "media": [media.model_dump() for media in self.media] if self.media else [],
        }

    @classmethod
    def from_json_string(cls, json_str: str) -> "HolidayPlannerReport":
        """Create instance from JSON string with error handling."""
        try:
            data = json.loads(json_str)
            return cls.model_validate(data)
        except Exception as e:
            # Return minimal valid instance on parse error
            return cls(
                introduction=f"Error parsing holiday planner data: {str(e)}",
                itinerary=[],
                accommodations=[],
                dining=None,
                budget=None,
                practical_information=None,
            )
