"""Pydantic models for structuring deep research report data."""

from pydantic import BaseModel, Field, model_validator


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
    sources: list[ResearchSource] = Field(default_factory=list, description="Sources supporting this section")


class DeepResearchReport(BaseModel):
    """Comprehensive research report model.

    This is the crew's ``output_pydantic`` contract, so the LLM must produce it in one
    shot. Fields the model reliably supplies stay required; three that a small model
    intermittently omitted are made resilient, because a single omission failed the
    whole (~9-minute) research run via ``output_pydantic`` validation:

    * ``sources_count`` is *computed* from the sections below, never trusted from the
      LLM -- counting is a deterministic job a model should not be asked to do.
    * ``methodology`` and ``confidence_level`` default rather than hard-fail; the
      renderer already treats both as optional.
    """

    title: str = Field(..., description="Main title of the research report")
    topic: str = Field(..., description="Research topic")
    executive_summary: str = Field(..., description="High-level summary of findings")
    key_findings: list[str] = Field(default_factory=list, description="List of key discoveries")
    research_sections: list[ResearchSection] = Field(
        default_factory=list, description="Detailed research sections"
    )
    methodology: str = Field("", description="Research methodology used")
    sources_count: int = Field(0, description="Total number of sources consulted (computed)")
    report_date: str | None = Field(None, description="Report generation date")
    confidence_level: str = Field("Medium", description="Overall confidence in findings: High, Medium, Low")

    @model_validator(mode="after")
    def _count_sources(self) -> "DeepResearchReport":
        """Derive ``sources_count`` from the sections instead of trusting the LLM.

        Falls back to any value supplied on the model only when no section carries a
        source, so a hand-built report with an explicit count is preserved.
        """
        counted = sum(len(section.sources) for section in self.research_sections)
        self.sources_count = counted or self.sources_count
        return self
