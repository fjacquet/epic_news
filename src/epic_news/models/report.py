"""Shared Pydantic models for report generation output."""
from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["ReportHTMLOutput"]


class ReportHTMLOutput(BaseModel):
    """Schema ensuring tasks return a single valid HTML document."""

    html: str = Field(..., description="Full HTML document string.")
