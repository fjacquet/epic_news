"""Pydantic models for report generation tools."""
from typing import List, Optional

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """Schema for section objects."""
    heading: str = Field(..., description="Section heading/title")
    content: str = Field(..., description="Section content in HTML format")


class ReportImage(BaseModel):
    """Schema for image objects."""
    src: str = Field(..., description="Image source URL or data URI")
    alt: str = Field("", description="Alternative text for accessibility")
    caption: Optional[str] = Field(None, description="Optional image caption")


class RenderReportToolSchema(BaseModel):
    """Main schema for RenderReportTool inputs."""
    title: str = Field(..., description="Report title")
    sections: List[ReportSection] = Field(
        ..., description="List of sections with headings and content"
    )
    images: Optional[List[ReportImage]] = Field(
        None, description="Optional list of images with metadata"
    )
    citations: Optional[List[str]] = Field(
        None, description="Optional list of citation strings or HTML links"
    )
