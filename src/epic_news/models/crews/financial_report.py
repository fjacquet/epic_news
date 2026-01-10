"""Pydantic models for structuring financial report data."""

from pydantic import BaseModel, Field


class AssetAnalysis(BaseModel):
    """Analysis of a specific asset class."""

    asset_class: str = Field(..., description="The asset class, e.g., 'Stocks', 'Crypto', 'ETFs'.")
    summary: str = Field(..., description="Summary of the portfolio analysis for this asset class.")
    details: list[str] = Field(default_factory=list, description="Detailed points of the analysis.")


class AssetSuggestion(BaseModel):
    """Suggestion for a specific asset class."""

    asset_class: str = Field(..., description="The asset class for the suggestion.")
    suggestion: str = Field(..., description="The investment suggestion or action to take.")
    rationale: str = Field(..., description="Rationale behind the suggestion.")


class FinancialReport(BaseModel):
    """Structured financial report data model."""

    title: str = Field(default="Daily Financial Report", description="The main title of the report.")
    executive_summary: str = Field(..., description="A high-level summary of the entire report.")
    analyses: list[AssetAnalysis] = Field(..., description="List of analyses for different asset classes.")
    suggestions: list[AssetSuggestion] = Field(..., description="List of investment suggestions.")
    report_date: str | None = Field(
        None, description="The date the report was generated, in YYYY-MM-DD format."
    )
