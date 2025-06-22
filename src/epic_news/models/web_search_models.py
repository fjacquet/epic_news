from typing import List, Optional

from pydantic import BaseModel, Field


class SerpApiInput(BaseModel):
    """Input schema for web search with advanced options."""
    query: str = Field(..., description="Search query")
    num_results: int = Field(
        default=5,
        description="Number of results to return",
        ge=1,
        le=10
    )
    country: Optional[str] = Field(
        None,
        description="Country code for localized results (e.g., 'us', 'uk', 'fr')"
    )
    language: Optional[str] = Field(
        None,
        description="Language code for results (e.g., 'en', 'fr', 'de')"
    )
    page: Optional[int] = Field(
        1,
        description="Pagination number",
        ge=1
    )


class ScrapeNinjaInput(BaseModel):
    """Input schema for the ScrapeNinjaTool."""

    url: str = Field(..., description="The URL to scrape.")
    headers: Optional[List[str]] = Field(
        None, description="List of custom headers to send with the request."
    )
    retry_num: Optional[int] = Field(None, description="Number of retries for the request.")
    geo: Optional[str] = Field(
        None, description="Geographical location for the request (e.g., 'de', 'us')."
    )
    proxy: Optional[str] = Field(None, description="Proxy to use for the request.")
    follow_redirects: Optional[int] = Field(
        None, description="Whether to follow redirects (0 or 1)."
    )
    timeout: Optional[int] = Field(None, description="Request timeout in seconds.")
    text_not_expected: Optional[List[str]] = Field(
        None, description="List of strings that should not appear in the response."
    )
    status_not_expected: Optional[List[int]] = Field(
        None, description="List of HTTP status codes that should not be returned."
    )
    extractor: Optional[str] = Field(
        None, description="JavaScript function to extract data from the page."
    )
