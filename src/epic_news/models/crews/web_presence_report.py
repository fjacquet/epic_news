"""Pydantic models for the Web Presence crew."""

from typing import Optional

from pydantic import BaseModel, Field


class WebsiteAnalysis(BaseModel):
    domain: str
    structure: str
    content_quality: str
    seo: str
    recommendations: list[str]


class SocialMediaPresence(BaseModel):
    platform: str
    url: str
    followers: int
    engagement_rate: Optional[float] = None
    notes: str


class TechnicalInfrastructure(BaseModel):
    hosting_provider: Optional[str] = None
    dns_provider: Optional[str] = None
    cdn_provider: Optional[str] = None
    ssl_issuer: Optional[str] = None


class DataLeak(BaseModel):
    source: str
    date: str
    description: str
    risk_level: str


class CompetitiveAnalysis(BaseModel):
    competitor_name: str
    website: str
    strengths: list[str]
    weaknesses: list[str]


class WebPresenceReport(BaseModel):
    """Comprehensive web presence report for a company."""

    company_name: str = Field(..., description="The name of the company.")
    executive_summary: str
    website_analysis: WebsiteAnalysis
    social_media_footprint: list[SocialMediaPresence]
    technical_infrastructure: TechnicalInfrastructure
    data_leak_analysis: list[DataLeak]
    competitive_analysis: list[CompetitiveAnalysis]
