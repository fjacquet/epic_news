"""Pydantic models for web search tools."""

from typing import Union

from pydantic import BaseModel, Field


class SerpApiInput(BaseModel):
    """Input schema for web search with advanced options."""

    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, description="Number of results to return", ge=1, le=10)
    country: Union[str, None] = Field(
        None, description="Country code for localized results (e.g., 'us', 'uk', 'fr')"
    )
    language: Union[str, None] = Field(None, description="Language code for results (e.g., 'en', 'fr', 'de')")
    page: Union[int, None] = Field(1, description="Pagination number", ge=1)


class ScrapeNinjaInput(BaseModel):
    """Input schema for the ScrapeNinjaTool."""

    url: str = Field(..., description="The URL to scrape.")
    headers: Union[list[str], None] = Field(
        None, description="List of custom headers to send with the request."
    )
    retry_num: Union[int, None] = Field(None, description="Number of retries for the request.")
    geo: Union[str, None] = Field(
        None, description="Geographical location for the request (e.g., 'de', 'us')."
    )
    proxy: Union[str, None] = Field(None, description="Proxy to use for the request.")
    follow_redirects: Union[int, None] = Field(None, description="Whether to follow redirects (0 or 1).")
    timeout: Union[int, None] = Field(None, description="Request timeout in seconds.")
    text_not_expected: Union[list[str], None] = Field(
        None, description="List of strings that should not appear in the response."
    )
    status_not_expected: Union[list[int], None] = Field(
        None, description="List of HTTP status codes that should not be returned."
    )
    extractor: Union[str, None] = Field(
        None, description="JavaScript function to extract data from the page."
    )
