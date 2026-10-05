"""The deep-research report: the crew's output_pydantic contract and the DOCX input.

One schema (simplification S3). The before-validator accepts older key names; it never
invents content, so a field the crew did not write stays empty.
"""

from typing import Any

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
    * ``methodology`` and ``confidence_level`` default rather than hard-fail.
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

    @model_validator(mode="before")
    @classmethod
    def _accept_old_key_names(cls, data: Any) -> Any:
        """Rename keys older outputs used (section ``title``, top-level ``summary``).

        ``topic`` falls back to the report ``title``. Nothing else is filled in.
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "executive_summary" not in data and "summary" in data:
            data["executive_summary"] = data["summary"]
        if "topic" not in data and "title" in data:
            data["topic"] = data["title"]
        sections = data.get("research_sections")
        if isinstance(sections, list):
            data["research_sections"] = [
                {**s, "section_title": s["title"]}
                if isinstance(s, dict) and "section_title" not in s and "title" in s
                else s
                for s in sections
            ]
        return data

    @model_validator(mode="after")
    def _count_sources(self) -> "DeepResearchReport":
        """Derive ``sources_count`` from the sections instead of trusting the LLM.

        Falls back to any value supplied on the model only when no section carries a
        source, so a hand-built report with an explicit count is preserved.
        """
        counted = sum(len(section.sources) for section in self.research_sections)
        self.sources_count = counted or self.sources_count
        return self

    @property
    def unique_sources(self) -> list[ResearchSource]:
        """Sources cited across sections, first occurrence kept, keyed by URL (else title)."""
        seen: set[str] = set()
        unique: list[ResearchSource] = []
        for section in self.research_sections:
            for source in section.sources:
                key = source.url or source.title
                if key not in seen:
                    seen.add(key)
                    unique.append(source)
        return unique
