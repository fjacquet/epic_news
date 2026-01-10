"""Pydantic models for report generation tools."""

from typing import Union

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """Schema for section objects."""

    heading: str = Field(..., description="Section heading/title")
    content: str = Field(..., description="Section content in HTML format")


class ReportImage(BaseModel):
    """Schema for image objects."""

    src: str = Field(..., description="Image source URL or data URI")
    alt: str = Field("", description="Alternative text for accessibility")
    caption: str | None = Field(None, description="Optional image caption")


class RenderReportToolSchema(BaseModel):
    """Main schema for RenderReportTool inputs."""

    title: str = Field(..., description="Report title")
    sections: list[ReportSection] = Field(..., description="List of sections with headings and content")
    images: list[ReportImage] | None = Field(None, description="Optional list of images with metadata")
    citations: list[str] | None = Field(
        None, description="Optional list of citation strings or HTML links"
    )
