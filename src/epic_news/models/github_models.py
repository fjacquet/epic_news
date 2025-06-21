"""Pydantic models for GitHub tools."""
from pydantic import BaseModel, Field


class GitHubSearchInput(BaseModel):
    """Input schema for GitHub search."""
    query: str = Field(..., description="Search query for GitHub")
    search_type: str = Field(
        default="repositories",
        description="Type of search: 'repositories', 'code', 'issues', or 'users'"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return",
        ge=1,
        le=10
    )
