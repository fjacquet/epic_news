"""Pydantic model for NewsDaily crew output."""

from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class NewsItem(BaseModel):
    """Individual news item."""

    titre: str = Field(..., alias="title", description="News article title")
    source: Optional[str] = Field(None, description="News source")
    resume: Optional[str] = Field(None, alias="content", description="Article summary")
    lien: Optional[str] = Field(None, alias="link", description="Article URL")
    date: Optional[str] = Field(None, description="Article date")

    class Config:
        populate_by_name = True  # Allow both field name and alias

    # Provide English aliases for template compatibility
    @property
    def title(self) -> str:
        return self.titre

    @property
    def summary(self) -> str:
        return self.resume or "Résumé non disponible"

    @property
    def link(self) -> str:
        return self.lien or "#"


class NewsSection(BaseModel):
    """News section containing multiple news items."""

    items: list[NewsItem] = Field(default_factory=list, description="List of news items in this section")


class NewsDailyReport(BaseModel):
    """Complete NewsDaily report structure matching the crew's expected JSON output."""

    summary: Optional[str] = Field(None, description="Executive summary")
    suisse_romande: Union[list[NewsItem], str] = Field(
        default_factory=list, description="Suisse Romande news"
    )
    suisse: Union[list[NewsItem], str] = Field(default_factory=list, description="Switzerland news")
    france: Union[list[NewsItem], str] = Field(default_factory=list, description="France news")
    europe: Union[list[NewsItem], str] = Field(default_factory=list, description="Europe news")
    world: Union[list[NewsItem], str] = Field(default_factory=list, description="World news")
    wars: Union[list[NewsItem], str] = Field(default_factory=list, description="Conflict news")
    economy: Union[list[NewsItem], list[str], str] = Field(default_factory=list, description="Economic news")
    methodology: Union[str, dict] | None = Field(None, description="Collection methodology and statistics")

    @field_validator("methodology")
    @classmethod
    def validate_methodology(cls, v):
        if isinstance(v, dict):
            return v.get("description", str(v))
        return v

    @field_validator("suisse_romande", "suisse", "france", "europe", "world", "wars")
    @classmethod
    def validate_news_sections(cls, v):
        if isinstance(v, str):
            # If it's a string (like "Aucune actualité..."), return empty list
            return []

        # Convert list of strings to NewsItem objects
        if isinstance(v, list) and v and isinstance(v[0], str):
            news_items = []
            for item in v:
                if isinstance(item, str):
                    news_items.append(
                        NewsItem(titre=item[:100] + "..." if len(item) > 100 else item, source="Actualité")
                    )
                else:
                    news_items.append(item)
            return news_items
        return v

    @field_validator("economy")
    @classmethod
    def validate_economy_section(cls, v):
        if isinstance(v, str):
            return []
        if isinstance(v, list) and v and isinstance(v[0], str):
            # Convert list of strings to NewsItem objects
            news_items = []
            for item in v:
                if isinstance(item, str):
                    news_items.append(
                        NewsItem(
                            titre=item[:100] + "..." if len(item) > 100 else item, source="Analyse économique"
                        )
                    )
                else:
                    news_items.append(item)
            return news_items
        return v

    def to_template_data(self) -> dict:
        """Convert to template-compatible dictionary for HTML rendering."""
        return {
            "title": "Actualités du Jour",
            "summary": self.summary,
            "suisse_romande": self.suisse_romande,
            "suisse": self.suisse,
            "france": self.france,
            "europe": self.europe,
            "world": self.world,
            "wars": self.wars,
            "economy": self.economy,
            "methodology": self.methodology,
        }
