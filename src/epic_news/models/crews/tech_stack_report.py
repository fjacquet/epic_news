"""Pydantic models for the Tech Stack crew."""

from typing import Optional

from pydantic import BaseModel, Field


class TechStackComponent(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class TechStackReport(BaseModel):
    """Comprehensive technology stack report for a company."""

    company_name: str = Field(..., description="The name of the company.")
    executive_summary: str
    technology_stack: list[TechStackComponent]
    strengths: list[str]
    weaknesses: list[str]
    open_source_contributions: list[str]
    talent_assessment: str
    recommendations: list[str]
