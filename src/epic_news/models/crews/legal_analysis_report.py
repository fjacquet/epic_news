"""Pydantic models for the Legal Analysis crew."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class LegalAnalysisReport(BaseModel):
    """Legal analysis report for a company."""
    company_name: str = Field(..., description="The name of the company.")
    compliance_assessment: Dict[str, Any] = Field(..., description="Assessment of legal compliance status.")
    ip_portfolio_analysis: Dict[str, Any] = Field(..., description="Analysis of the intellectual property portfolio.")
    regulatory_risk_assessment: Dict[str, Any] = Field(..., description="Assessment of regulatory risks.")
    litigation_history: List[Dict[str, Any]] = Field(..., description="Analysis of litigation history.")
    ma_due_diligence: Dict[str, Any] = Field(..., description="Legal due diligence for M&A activities.")
