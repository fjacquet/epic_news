"""Pydantic models for structuring deep research report data."""


from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """Individual research source information."""

    title: str = Field(..., description="Title of the source")
    url: str | None = Field(None, description="URL of the source")
    source_type: str = Field(..., description="Type: web, wikipedia, news, etc.")
    summary: str = Field(..., description="Key information from this source")
    relevance_score: int = Field(..., description="Relevance score 1-10", ge=1, le=10)


class ResearchSection(BaseModel):
    """Thematic section of research."""

    section_title: str = Field(..., description="Title of the research section")
    content: str = Field(..., description="Detailed content for this section")
    sources: list[ResearchSource] = Field(..., description="Sources supporting this section")


class DeepResearchReport(BaseModel):
    """Comprehensive research report model."""

    title: str = Field(..., description="Main title of the research report")
    topic: str = Field(..., description="Research topic")
    executive_summary: str = Field(..., description="High-level summary of findings")
    key_findings: list[str] = Field(..., description="List of key discoveries")
    research_sections: list[ResearchSection] = Field(..., description="Detailed research sections")
    methodology: str = Field(..., description="Research methodology used")
    sources_count: int = Field(..., description="Total number of sources consulted")
    report_date: str | None = Field(None, description="Report generation date")
    confidence_level: str = Field(..., description="Overall confidence in findings: High, Medium, Low")
