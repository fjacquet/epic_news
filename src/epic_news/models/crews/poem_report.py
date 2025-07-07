"""Pydantic models for poem generation output."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["PoemJSONOutput"]


class PoemJSONOutput(BaseModel):
    """Schema ensuring tasks return a single valid JSON object for a poem."""

    title: str = Field(..., description="The title of the poem.")
    poem: str = Field(..., description="The full text of the poem.")
