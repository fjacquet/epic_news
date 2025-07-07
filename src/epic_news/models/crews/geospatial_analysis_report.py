"""Pydantic models for the Geospatial Analysis crew."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class GeospatialAnalysisReport(BaseModel):
    """Geospatial analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    physical_locations: List[Dict[str, Any]] = Field(..., description="Mapping of physical locations.")
    risk_assessment: List[Dict[str, Any]] = Field(..., description="Geospatial risk assessment.")
    supply_chain_map: List[Dict[str, Any]] = Field(..., description="Geospatial mapping of the supply chain.")
    mergers_and_acquisitions_insights: List[Dict[str, Any]] = Field(..., description="Geospatial intelligence for M&A.")
