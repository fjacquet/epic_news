"""
Pydantic model for Saint Daily data.

This module defines the data structure for saint information used by
SaintDailyCrew and consumed by HtmlDesignerCrew for report generation.
"""

from pydantic import BaseModel, Field


class SaintData(BaseModel):
    """Pydantic model for saint daily report data."""

    saint_name: str = Field(..., description="Name of the saint")
    feast_date: str = Field(..., description="Date of the saint's feast day")
    biography: str = Field(..., description="Detailed biography of the saint")
    significance: str = Field(..., description="Significance and importance of the saint")
    miracles: str = Field(..., description="Miracles and notable events associated with the saint")
    swiss_connection: str = Field(..., description="Connection to Switzerland if applicable")
    prayer_reflection: str = Field(..., description="Prayer or spiritual reflection")
    sources: list[str] = Field(default_factory=list, description="List of sources and references")
    birth_year: str = Field(default="", description="Year of birth if known")
    death_year: str = Field(default="", description="Year of death if known")
    patron_of: str = Field(default="", description="What or whom the saint is patron of")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            # Ensure proper JSON serialization
        }

    def to_template_data(self) -> dict:
        """Convert to template-friendly dictionary format."""
        return {
            "saint_name": self.saint_name,
            "feast_date": self.feast_date,
            "biography": self.biography,
            "significance": self.significance,
            "miracles": self.miracles,
            "swiss_connection": self.swiss_connection,
            "prayer_reflection": self.prayer_reflection,
            "sources": self.sources,
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "patron_of": self.patron_of,
            "author": "Epic News AI",
        }

    @classmethod
    def from_json_string(cls, json_string: str) -> "SaintData":
        """Create SaintData instance from JSON string."""
        import json

        try:
            data = json.loads(json_string)
            return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Return default instance if parsing fails
            return cls(
                saint_name="Saint du Jour",
                feast_date="",
                biography="",
                significance="",
                miracles="",
                swiss_connection="",
                prayer_reflection="",
            )

    @classmethod
    def from_file(cls, file_path: str) -> "SaintData":
        """Create SaintData instance from JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            return cls.from_json_string(content)
        except (OSError, FileNotFoundError):
            # Return default instance if file not found
            return cls(
                saint_name="Saint du Jour",
                feast_date="",
                biography="",
                significance="",
                miracles="",
                swiss_connection="",
                prayer_reflection="",
            )
