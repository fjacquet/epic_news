"""
Pydantic model for HolidayPlannerCrew JSON output.
"""

from typing import Any, Union

from pydantic import BaseModel, Field


class Activity(BaseModel):
    """Model for a single activity within a day."""

    heure: Union[str, None] = Field(None, description="Time for the activity")
    description: str = Field(..., description="Description of the activity")
    notes_transport: Union[str, None] = Field(None, description="Transport notes")
    infos_resa: Union[str, None] = Field(None, description="Reservation information")
    plan_b: Union[str, None] = Field(None, description="Alternative plan")


class ItineraryDay(BaseModel):
    """A single day in the itinerary."""

    jour: str = Field(description="Day description (e.g., 'Jour 1 - Vendredi : Arrivée')")
    activites: list[Activity] = Field(default_factory=list, description="List of activities for the day")


class Accommodation(BaseModel):
    """Model for accommodation information."""

    nom: str = Field(..., description="Name of the accommodation")
    adresse: Union[str, None] = Field(None, description="Address of the accommodation")
    contact: Union[str, None] = Field(None, description="Contact information or booking link")
    prix: Union[str, None] = Field(None, description="Price information")
    pourquoi_recommande: Union[str, None] = Field(None, description="Why it's recommended")
    services: Union[list[str], None] = Field(None, description="Available services")


class DiningExperience(BaseModel):
    """Model for dining recommendations."""

    nom: str = Field(..., description="Name of the restaurant/dining experience")
    adresse: Union[str, None] = Field(None, description="Address of the restaurant")
    specialites: Union[str, None] = Field(None, description="Specialties")
    prix_moyen: Union[str, None] = Field(None, description="Average price")
    pourquoi_recommande: Union[str, None] = Field(None, description="Why this choice is recommended")
    contact: Union[str, None] = Field(None, description="Contact information")


class TotalEstimate(BaseModel):
    """Model for total budget estimate."""

    bas: Union[int, float, None] = Field(None, description="Low estimate")
    haut: Union[int, float, None] = Field(None, description="High estimate")
    monnaie: Union[str, None] = Field(None, description="Currency")
    remarque: Union[str, None] = Field(None, description="Additional remarks")


class BudgetCategory(BaseModel):
    """Budget category with amount and details."""

    montant: int = Field(description="Amount as integer")
    details: str = Field(description="Details about this budget category")


class TotalEstimateNew(BaseModel):
    """Model for total budget estimate in new format."""

    montant: int = Field(description="Total amount")
    devise: str = Field(description="Currency")
    notes: str = Field(description="Additional notes")


class Budget(BaseModel):
    """Model for budget breakdown."""

    transport: Union[BudgetCategory, None] = Field(None, description="Transport costs")
    hebergement: Union[BudgetCategory, None] = Field(None, description="Accommodation costs")
    restauration: Union[BudgetCategory, None] = Field(None, description="Restaurant costs")
    activites: Union[BudgetCategory, None] = Field(None, description="Activity costs")
    total_estime: Union[TotalEstimateNew, None] = Field(None, description="Total estimated cost")
    conseils_economies: list[str] = Field(default_factory=list, description="Money-saving tips")


class EmergencyContact(BaseModel):
    """Model for emergency contact."""

    service: str = Field(description="Service name")
    numero: str = Field(description="Phone number")


class UsefulPhrase(BaseModel):
    """Model for useful phrase translation."""

    francais: str = Field(description="French phrase")
    italien: str = Field(description="Italian translation")


class PracticalInfo(BaseModel):
    """Model for practical information."""

    conseils_voyage: list[str] = Field(default_factory=list, description="Travel tips")
    securite: list[str] = Field(default_factory=list, description="Safety information")
    contacts_urgence: list[Union[EmergencyContact, str]] = Field(
        default_factory=list, description="Emergency contacts"
    )
    phrases_utiles: list[Union[UsefulPhrase, str]] = Field(default_factory=list, description="Useful phrases")
    liste_bagages: Union[dict[str, list[str]], None] = Field(None, description="Packing list")


class MediaItem(BaseModel):
    """Model for media items."""

    url: str = Field(..., description="URL of the media")
    caption: Union[str, None] = Field(None, description="Caption for the media")
    type: Union[str, None] = Field(None, description="Type of media (image, video, etc.)")


class HolidayPlan(BaseModel):
    """
    Comprehensive model for holiday plan JSON output from HolidayPlannerCrew.

    This model matches the actual JSON structure from the crew output.
    """

    introduction: str = Field(..., description="Detailed introduction to the destination")
    itineraire: list[ItineraryDay] = Field(default_factory=list, description="Day-by-day itinerary")
    hebergement: list[Accommodation] = Field(default_factory=list, description="Recommended accommodations")
    restauration: list[DiningExperience] = Field(default_factory=list, description="Dining recommendations")
    budget: Budget = Field(default_factory=Budget, description="Budget breakdown")
    information_pratique: PracticalInfo = Field(
        default_factory=PracticalInfo, description="Practical travel information"
    )
    sources: list[str] = Field(default_factory=list, description="Source links and references")
    media: list[Union[MediaItem, str]] = Field(default_factory=list, description="Media links with captions")

    def to_template_data(self) -> dict[str, Any]:
        """
        Convert the holiday plan to template data format for HTML rendering.
        Preserves French keys to match renderer expectations.

        Returns:
            Dict containing all data formatted for template rendering with French keys.
        """
        return {
            "introduction": self.introduction,
            "itineraire": [day.model_dump() for day in self.itineraire],
            "hebergement": [acc.model_dump() for acc in self.hebergement],
            "restauration": [dining.model_dump() for dining in self.restauration],
            "budget": self.budget.model_dump() if self.budget else {},
            "information_pratique": self.information_pratique.model_dump(),
            "sources": self.sources,
            "media": self.media,
        }
