"""Pydantic models for the Company Profiler crew."""

from typing import Any

from pydantic import BaseModel, Field


class CompanyCoreInfo(BaseModel):
    legal_name: str = Field(..., description="Full legal name of the company.")
    parent_company: str | None = Field(None, description="Parent company, if any.")
    subsidiaries: list[str] = Field(default_factory=list, description="List of subsidiary companies.")
    year_founded: int = Field(..., description="Year the company was founded.")
    headquarters_location: str = Field(..., description="Headquarters location.")
    industry_classification: str = Field(..., description="Primary industry.")
    business_activities: list[str] = Field(..., description="List of primary business activities.")
    employee_count: int | None = Field(None, description="Number of employees.")
    revenue: float | None = Field(None, description="Annual revenue.")
    market_cap: float | None = Field(None, description="Market capitalization if public.")
    corporate_structure: str = Field(..., description="Description of the corporate structure.")
    ownership_details: str = Field(..., description="Details about ownership.")
    mission_statement: str | None = Field(None, description="Company's mission statement.")
    core_values: list[str] = Field(default_factory=list, description="List of core values.")


class CompanyHistory(BaseModel):
    key_milestones: list[str] = Field(..., description="Key historical milestones.")
    founding_story: str = Field(..., description="The story of the company's founding.")
    strategic_shifts: list[str] = Field(default_factory=list, description="Major strategic shifts or pivots.")
    acquisitions_and_mergers: list[dict[str, Any]] = Field(
        default_factory=list, description="List of acquisitions and mergers."
    )
    leadership_changes: list[dict[str, Any]] = Field(
        default_factory=list, description="Significant leadership changes."
    )
    major_product_launches: list[str] = Field(default_factory=list, description="Major product launches.")
    challenges_or_controversies: list[str] = Field(
        default_factory=list, description="Significant challenges or controversies."
    )


class Financials(BaseModel):
    revenue_and_profit_trends: list[dict[str, Any]] = Field(
        ..., description="Revenue and profit trends over 3-5 years."
    )
    key_financial_ratios: dict[str, Any] = Field(..., description="Key financial ratios (values may be numbers or notes).")
    funding_rounds: list[dict[str, Any]] = Field(
        default_factory=list, description="Information on funding rounds."
    )
    major_investors: list[str] = Field(default_factory=list, description="List of major investors.")
    debt_structure: dict[str, Any] | str | None = Field(None, description="Description of the debt structure (may be text or structured data).")
    recent_financial_news: list[str] = Field(default_factory=list, description="Recent financial news.")


class MarketPosition(BaseModel):
    market_share: str | None = Field(None, description="Estimated market share.")
    competitive_landscape: str = Field(..., description="Description of the competitive landscape.")
    key_competitors: list[str] = Field(..., description="List of key competitors.")
    comparative_advantages: list[str] = Field(..., description="List of comparative advantages.")
    industry_trends: list[str] = Field(..., description="Industry trends affecting the company.")
    growth_opportunities: list[str] = Field(..., description="Growth opportunities.")
    challenges: list[str] = Field(..., description="Market challenges.")


class ProductsAndServices(BaseModel):
    core_product_lines: list[str] = Field(..., description="Core product or service lines.")
    recent_launches: list[str] = Field(default_factory=list, description="Recent product launches.")
    discontinued_offerings: list[str] = Field(default_factory=list, description="Discontinued products.")
    pricing_strategy: str | None = Field(None, description="Description of the pricing strategy.")
    customer_segments: list[str] = Field(..., description="Primary customer segments.")


class Management(BaseModel):
    key_executives: list[dict[str, Any]] = Field(
        ..., description="List of key executives and their backgrounds."
    )
    board_of_directors: list[str] = Field(..., description="List of board members.")
    management_style: str | None = Field(None, description="Description of the management style.")
    corporate_culture: str = Field(..., description="Description of the corporate culture.")


class LegalCompliance(BaseModel):
    regulatory_framework: str = Field(..., description="Governing regulatory framework.")
    compliance_history: list[str] = Field(..., description="History of compliance and violations.")
    ongoing_litigation: list[str] = Field(default_factory=list, description="Ongoing or past litigation.")
    regulatory_filings: list[str] = Field(default_factory=list, description="Recent regulatory filings.")


class CompanyProfileReport(BaseModel):
    """Comprehensive company profile report."""

    company_name: str = Field(..., description="The name of the company being profiled.")
    core_info: CompanyCoreInfo
    history: CompanyHistory
    financials: Financials
    market_position: MarketPosition
    products_and_services: ProductsAndServices
    management: Management
    legal_compliance: LegalCompliance
