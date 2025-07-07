"""Pydantic models for the HR Intelligence crew."""
from pydantic import BaseModel, Field
from typing import Dict, Any

class HRIntelligenceReport(BaseModel):
    """Human Resources intelligence report."""
    company_name: str = Field(..., description="The name of the company.")
    leadership_assessment: Dict[str, Any] = Field(..., description="Assessment of the leadership team.")
    employee_sentiment: Dict[str, Any] = Field(..., description="Analysis of employee sentiment.")
    organizational_culture: Dict[str, Any] = Field(..., description="Assessment of the organizational culture.")
    talent_acquisition_strategy: Dict[str, Any] = Field(..., description="Analysis of talent acquisition strategy.")
    summary_and_recommendations: str = Field(..., description="Executive summary and recommendations.")
