"""Pydantic model for meeting preparation JSON output."""
from typing import Optional

from pydantic import BaseModel, Field


class Participant(BaseModel):
    """Model representing a meeting participant."""

    name: str = Field(..., description="Name of the participant.")
    role: str = Field(..., description="Role or function of the participant.")
    background: str = Field(..., description="Relevant background information about the participant.")


class CompanyProfile(BaseModel):
    """Model representing company profile information."""

    name: str = Field(..., description="Name of the company.")
    industry: str = Field(..., description="Industry or sector the company operates in.")
    key_products: list[str] = Field(
        default_factory=list, description="List of key products or services offered."
    )
    market_position: str = Field(..., description="Description of the company's market position.")


class TalkingPoint(BaseModel):
    """Model representing a talking point for the meeting."""

    topic: str = Field(..., description="Main topic to be discussed.")
    key_points: list[str] = Field(default_factory=list, description="Key points related to the topic.")
    questions: list[str] = Field(default_factory=list, description="Questions to ask related to the topic.")


class StrategicRecommendation(BaseModel):
    """Model representing a strategic recommendation."""

    area: str = Field(..., description="Area or domain for the recommendation.")
    suggestion: str = Field(..., description="Detailed suggestion or recommendation.")
    expected_outcome: str = Field(..., description="Expected outcome if the suggestion is implemented.")


class AdditionalResource(BaseModel):
    """Model representing an additional resource for the meeting."""

    title: str = Field(..., description="Title of the resource.")
    description: str = Field(..., description="Description of the resource.")
    link: Optional[str] = Field(None, description="URL or reference link to the resource.")


class MeetingPrepReport(BaseModel):
    """Main model for meeting preparation report."""

    title: str = Field(..., description="Title of the meeting briefing.")
    summary: str = Field(..., description="Brief overview of the meeting purpose.")
    company_profile: CompanyProfile = Field(..., description="Key information about the company.")
    participants: list[Participant] = Field(default_factory=list, description="List of meeting participants.")
    industry_overview: str = Field(..., description="Industry analysis and context.")
    talking_points: list[TalkingPoint] = Field(default_factory=list, description="Key topics for discussion.")
    strategic_recommendations: list[StrategicRecommendation] = Field(
        default_factory=list, description="Action items and strategic suggestions."
    )
    additional_resources: list[AdditionalResource] = Field(
        default_factory=list, description="Any reference materials or links."
    )

    def to_template_data(self) -> dict:
        """Convert to template-friendly dictionary format."""
        return {
            "title": self.title,
            "summary": self.summary,
            "company": self.company_profile.name,
            "industry": self.company_profile.industry,
            "key_products": self.company_profile.key_products,
            "market_position": self.company_profile.market_position,
            "participants": [
                {"name": participant.name, "role": participant.role, "background": participant.background}
                for participant in self.participants
            ],
            "industry_overview": self.industry_overview,
            "talking_points": [
                {"topic": point.topic, "key_points": point.key_points, "questions": point.questions}
                for point in self.talking_points
            ],
            "strategic_recommendations": [
                {"area": rec.area, "suggestion": rec.suggestion, "expected_outcome": rec.expected_outcome}
                for rec in self.strategic_recommendations
            ],
            "additional_resources": [
                {"title": res.title, "description": res.description, "link": res.link}
                for res in self.additional_resources
            ],
        }
