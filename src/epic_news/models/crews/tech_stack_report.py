"""Pydantic models for the Tech Stack crew."""
from pydantic import BaseModel, Field
from typing import List, Optional

class TechStackComponent(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class TechStackReport(BaseModel):
    """Comprehensive technology stack report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    executive_summary: str
    technology_stack: List[TechStackComponent]
    strengths: List[str]
    weaknesses: List[str]
    open_source_contributions: List[str]
    talent_assessment: str
    recommendations: List[str]
