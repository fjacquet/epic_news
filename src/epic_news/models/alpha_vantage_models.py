"""Pydantic models for Alpha Vantage tools."""

from pydantic import BaseModel, Field


class CompanyOverviewInput(BaseModel):
    """Input schema for the AlphaVantageCompanyOverviewTool."""

    ticker: str = Field(..., description="The stock ticker symbol to get information for.")
