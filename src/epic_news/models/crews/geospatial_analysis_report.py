"""Pydantic models for the Geospatial Analysis crew."""
from typing import Any

from pydantic import BaseModel, Field


class GeospatialAnalysisReport(BaseModel):
    """Geospatial analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    physical_locations: list[dict[str, Any]] = Field(..., description="Mapping of physical locations.")
    risk_assessment: list[dict[str, Any]] = Field(..., description="Geospatial risk assessment.")
    supply_chain_map: list[dict[str, Any]] = Field(..., description="Geospatial mapping of the supply chain.")
    mergers_and_acquisitions_insights: list[dict[str, Any]] = Field(..., description="Geospatial intelligence for M&A.")
