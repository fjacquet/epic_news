"""Pydantic model for PESTEL analysis reports.

PESTEL = Political, Economic, Social, Technological, Environmental, Legal.
Each dimension holds a structured summary, key factors, impact analysis, and sources.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PestelDimension(BaseModel):
    """Structured output for one PESTEL dimension."""

    summary: str = Field(description="Executive summary of this dimension for the topic")
    key_factors: list[str] = Field(
        default_factory=list, description="Key factors identified in this dimension"
    )
    impact_analysis: str = Field(description="Strategic impact of these factors on the topic")
    sources: list[str] = Field(default_factory=list, description="Citation URLs or reference titles")


class PestelReport(BaseModel):
    """Complete PESTEL analysis for a given topic."""

    topic: str = Field(description="The subject of the PESTEL analysis")
    executive_summary: str = Field(description="High-level overview of the full analysis")
    political: PestelDimension
    economic: PestelDimension
    social: PestelDimension
    technological: PestelDimension
    environmental: PestelDimension
    legal: PestelDimension
    synthesis: str = Field(description="Cross-dimensional synthesis, strategic recommendations, and outlook")
    generated_at: str = Field(description="ISO date of report generation (YYYY-MM-DD)")
