"""Pydantic models for the Cross Reference Report crew."""
from typing import Any

from pydantic import BaseModel, Field


class CrossReferenceReport(BaseModel):
    """Global intelligence report cross-referencing multiple data points."""
    target: str = Field(..., description="The target of the intelligence report.")
    executive_summary: str = Field(..., description="High-level summary of key findings.")
    detailed_findings: dict[str, Any] = Field(..., description="A structured dictionary containing synthesized intelligence from all sources.")
    confidence_assessment: str = Field(..., description="Assessment of the confidence level in the findings.")
    information_gaps: list[str] = Field(default_factory=list, description="Identified information gaps.")
