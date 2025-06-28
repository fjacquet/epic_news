"""Pydantic models for HTML-based output validation."""

from pydantic import BaseModel, Field


class ReportHTMLOutput(BaseModel):
    """Model for HTML output format validation."""

    html_content: str = Field(..., description="Complete HTML content of the report")
    title: str = Field(..., description="Title of the HTML report")
    description: str = Field("", description="Optional description or metadata about the report")
    css_classes: list[str] = Field(
        default_factory=list, description="CSS classes applied to the main container"
    )

    @property
    def content(self) -> str:
        """Return the HTML content for compatibility with output handling."""
        return self.html_content
