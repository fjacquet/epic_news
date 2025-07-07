"""Pydantic models for the Legal Analysis crew."""
from typing import Any

from pydantic import BaseModel, Field


class LegalAnalysisReport(BaseModel):
    """Legal analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    compliance_assessment: dict[str, Any] = Field(..., description="Assessment of legal compliance status.")
    ip_portfolio_analysis: dict[str, Any] = Field(..., description="Analysis of the intellectual property portfolio.")
    regulatory_risk_assessment: dict[str, Any] = Field(..., description="Assessment of regulatory risks.")
    litigation_history: list[dict[str, Any]] = Field(..., description="Analysis of litigation history.")
    ma_due_diligence: dict[str, Any] = Field(..., description="Legal due diligence for M&A activities.")
