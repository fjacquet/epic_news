"""Pydantic models for email search tools."""

from pydantic import BaseModel, Field


class HunterIOInput(BaseModel):
    """Input schema for HunterIO tool."""

    domain: str = Field(..., description="Domain name to search for emails")


class SerperSearchInput(BaseModel):
    """Input schema for Serper search tool."""

    query: str = Field(..., description="Company name or search query to find emails")


class DelegatingEmailSearchInput(BaseModel):
    """Input schema for the delegating email search tool."""

    provider: str = Field(..., description="Email search provider: 'hunter' or 'serper'")
    query: str = Field(
        ...,
        description="Domain name for 'hunter' (e.g., 'example.com'), or company name/general query for 'serper' (e.g., 'Example Inc')",
    )
