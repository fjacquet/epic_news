"""Pydantic models for the Cross Reference Report crew."""

from typing import Any

from pydantic import BaseModel, Field

OSINT_AREAS = (
    "company_profile",
    "tech_stack",
    "web_presence",
    "hr_intelligence",
    "legal_analysis",
    "geospatial_analysis",
)


class CrossReferenceReport(BaseModel):
    """Global intelligence report cross-referencing multiple data points."""

    target: str = Field(..., description="The target of the intelligence report.")
    executive_summary: str = Field(..., description="High-level summary of key findings.")
    detailed_findings: dict[str, Any] = Field(
        ...,
        description=(
            "One entry per OSINT area (company_profile, tech_stack, web_presence, hr_intelligence, "
            "legal_analysis, geospatial_analysis), each a short findings summary."
        ),
        # The value stays a free dict (renderers/DOCX read it as one), but the JSON schema sent
        # to the LLM lists the areas: with a bare object schema the model answers {}.
        json_schema_extra={
            "properties": {area: {"type": "string"} for area in OSINT_AREAS},
            "required": list(OSINT_AREAS),
        },
    )
    confidence_assessment: str = Field(..., description="Assessment of the confidence level in the findings.")
    information_gaps: list[str] = Field(default_factory=list, description="Identified information gaps.")
