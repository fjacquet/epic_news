"""Pydantic models for the HR Intelligence crew."""

from typing import Any

from pydantic import BaseModel, Field


class HRIntelligenceReport(BaseModel):
    """Human Resources intelligence report."""

    company_name: str = Field(..., description="The name of the company.")
    leadership_assessment: dict[str, Any] = Field(..., description="Assessment of the leadership team.")
    employee_sentiment: dict[str, Any] = Field(..., description="Analysis of employee sentiment.")
    organizational_culture: dict[str, Any] = Field(
        ..., description="Assessment of the organizational culture."
    )
    talent_acquisition_strategy: dict[str, Any] = Field(
        ..., description="Analysis of talent acquisition strategy."
    )
    summary_and_recommendations: str = Field(..., description="Executive summary and recommendations.")
