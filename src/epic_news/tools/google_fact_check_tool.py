import os
from typing import Optional

import requests
from crewai.tools import BaseTool

from ..models.google_fact_check_tool import GoogleFactCheckInput


class GoogleFactCheckTool(BaseTool):
    """Tool to search for fact-checked claims using the Google Fact Check API."""

    name: str = "Google Fact Check"
    description: str = "Searches for fact-checked claims on a given query."
    args_schema: type[GoogleFactCheckInput] = GoogleFactCheckInput
    api_key: str | None = None

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is not set. Please set the GOOGLE_API_KEY environment variable.")

    def _run(self, **kwargs) -> str:
        """Run the tool."""
        inputs = self.args_schema(**kwargs)
        params = {
            "query": inputs.query,
            "languageCode": inputs.language_code,
            "reviewPublisherSiteFilter": inputs.review_publisher_site_filter,
            "maxAgeDays": inputs.max_age_days,
            "pageSize": inputs.page_size,
            "pageToken": inputs.page_token,
            "key": self.api_key,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = requests.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params=params,
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"Error: {e}"
