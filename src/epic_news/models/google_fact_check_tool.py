from typing import Union

from pydantic import BaseModel, Field


class GoogleFactCheckInput(BaseModel):
    """Input model for the GoogleFactCheckTool."""

    query: str = Field(..., description="The query to search for fact-checked claims.")
    review_publisher_site_filter: str | None = Field(
        default=None, description="The review publisher site to filter results by, e.g. nytimes.com."
    )
    language_code: str | None = Field(
        default=None, description='The BCP-47 language code, such as "en-US" or "sr-Latn".'
    )
    max_age_days: int | None = Field(
        default=None, description="The maximum age of the returned search results, in days."
    )
    page_size: int = Field(default=10, description="The pagination size.")
    page_token: str | None = Field(default=None, description="The pagination token.")
