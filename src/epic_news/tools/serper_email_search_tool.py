"""Serper.dev email search tool implementation."""

import json
import os

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

from src.epic_news.models.email_search_models import SerperSearchInput

from .email_base import EmailSearchTool

# Load environment variables from .env file
load_dotenv()
SERPER_API_URL = "https://google.serper.dev/search"


class SerperEmailSearchTool(BaseTool):
    """Search for company emails using Serper API."""

    name: str = "serper_email_search"
    description: str = "Search the web for publicly available email addresses related to a company"
    args_schema: type[BaseModel] = SerperSearchInput
    searcher: EmailSearchTool = None

    def __init__(self, **data):
        """Initialize with API key from environment."""
        super().__init__(**data)
        if self.searcher is None:
            api_key = os.getenv("SERPER_API_KEY")
            if not api_key:
                raise ValueError("SERPER_API_KEY environment variable not set")
            self.searcher = EmailSearchTool(api_key)

    def _run(self, query: str) -> str:
        """Search for emails using Serper API."""
        headers = {"X-API-KEY": self.searcher.api_key, "Content-Type": "application/json"}

        # Clean up the query for better search results
        clean_query = query.strip().lower()
        search_query = f'"{clean_query}" "@{clean_query.replace(" ", "")}" email'

        payload = {"q": search_query}
        response = self.searcher._make_request("POST", SERPER_API_URL, headers=headers, json=payload)

        if not response:
            return json.dumps([{"error": "Failed to fetch data from Serper API"}])

        results = response.json().get("organic", [])
        emails_found = set()

        for result in results:
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            emails_found.update(self.searcher._extract_emails(f"{snippet} {link}"))

        result = [{"emails": sorted(emails_found)}] if emails_found else [{"message": "No emails found"}]
        return json.dumps(result)


# For backward compatibility
SearchMailSerper = SerperEmailSearchTool
