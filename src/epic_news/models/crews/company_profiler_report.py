"""Pydantic models for the Company Profiler crew."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CompanyCoreInfo(BaseModel):
    legal_name: str = Field(..., description="Full legal name of the company.")
    parent_company: Optional[str] = Field(None, description="Parent company, if any.")
    subsidiaries: List[str] = Field(default_factory=list, description="List of subsidiary companies.")
    year_founded: int = Field(..., description="Year the company was founded.")
    headquarters_location: str = Field(..., description="Headquarters location.")
    industry_classification: str = Field(..., description="Primary industry.")
    business_activities: List[str] = Field(..., description="List of primary business activities.")
    employee_count: Optional[int] = Field(None, description="Number of employees.")
    revenue: Optional[float] = Field(None, description="Annual revenue.")
    market_cap: Optional[float] = Field(None, description="Market capitalization if public.")
    corporate_structure: str = Field(..., description="Description of the corporate structure.")
    ownership_details: str = Field(..., description="Details about ownership.")
    mission_statement: Optional[str] = Field(None, description="Company's mission statement.")
    core_values: List[str] = Field(default_factory=list, description="List of core values.")

class CompanyHistory(BaseModel):
    key_milestones: List[str] = Field(..., description="Key historical milestones.")
    founding_story: str = Field(..., description="The story of the company's founding.")
    strategic_shifts: List[str] = Field(default_factory=list, description="Major strategic shifts or pivots.")
    acquisitions_and_mergers: List[Dict[str, Any]] = Field(default_factory=list, description="List of acquisitions and mergers.")
    leadership_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Significant leadership changes.")
    major_product_launches: List[str] = Field(default_factory=list, description="Major product launches.")
    challenges_or_controversies: List[str] = Field(default_factory=list, description="Significant challenges or controversies.")

class Financials(BaseModel):
    revenue_and_profit_trends: List[Dict[str, Any]] = Field(..., description="Revenue and profit trends over 3-5 years.")
    key_financial_ratios: Dict[str, float] = Field(..., description="Key financial ratios.")
    funding_rounds: List[Dict[str, Any]] = Field(default_factory=list, description="Information on funding rounds.")
    major_investors: List[str] = Field(default_factory=list, description="List of major investors.")
    debt_structure: Optional[str] = Field(None, description="Description of the debt structure.")
    recent_financial_news: List[str] = Field(default_factory=list, description="Recent financial news.")

class MarketPosition(BaseModel):
    market_share: Optional[str] = Field(None, description="Estimated market share.")
    competitive_landscape: str = Field(..., description="Description of the competitive landscape.")
    key_competitors: List[str] = Field(..., description="List of key competitors.")
    comparative_advantages: List[str] = Field(..., description="List of comparative advantages.")
    industry_trends: List[str] = Field(..., description="Industry trends affecting the company.")
    growth_opportunities: List[str] = Field(..., description="Growth opportunities.")
    challenges: List[str] = Field(..., description="Market challenges.")

class ProductsAndServices(BaseModel):
    core_product_lines: List[str] = Field(..., description="Core product or service lines.")
    recent_launches: List[str] = Field(default_factory=list, description="Recent product launches.")
    discontinued_offerings: List[str] = Field(default_factory=list, description="Discontinued products.")
    pricing_strategy: Optional[str] = Field(None, description="Description of the pricing strategy.")
    customer_segments: List[str] = Field(..., description="Primary customer segments.")

class Management(BaseModel):
    key_executives: List[Dict[str, Any]] = Field(..., description="List of key executives and their backgrounds.")
    board_of_directors: List[str] = Field(..., description="List of board members.")
    management_style: Optional[str] = Field(None, description="Description of the management style.")
    corporate_culture: str = Field(..., description="Description of the corporate culture.")

class LegalCompliance(BaseModel):
    regulatory_framework: str = Field(..., description="Governing regulatory framework.")
    compliance_history: List[str] = Field(..., description="History of compliance and violations.")
    ongoing_litigation: List[str] = Field(default_factory=list, description="Ongoing or past litigation.")
    regulatory_filings: List[str] = Field(default_factory=list, description="Recent regulatory filings.")

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
