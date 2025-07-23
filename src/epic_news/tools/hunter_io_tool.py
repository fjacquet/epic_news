"""Hunter.io email search tool implementation."""

import json
import os

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from epic_news.models.email_search_models import HunterIOInput

from .email_base import EmailSearchTool

# Load environment variables from .env file
load_dotenv()
HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"


class HunterIOTool(BaseTool):
    """Search for company emails using Hunter.io API."""

    name: str = "hunter_io_search"
    description: str = "Find professional email addresses for a given domain using Hunter.io"
    args_schema: type[BaseModel] = HunterIOInput
    searcher: EmailSearchTool = Field(default=None, exclude=True)

    def __init__(self, searcher: EmailSearchTool = None, **data):
        """Initialize with API key from environment or a searcher instance."""
        super().__init__(**data)
        if searcher:
            self.searcher = searcher
        else:
            api_key = os.getenv("HUNTER_API_KEY")
            if not api_key:
                raise ValueError("HUNTER_API_KEY environment variable not set")
            self.searcher = EmailSearchTool(api_key=api_key)

    def _run(self, domain: str) -> str:
        """Search for emails using Hunter.io API."""
        params = {"domain": domain, "api_key": self.searcher.api_key}

        response = self.searcher._make_request("GET", HUNTER_API_URL, params=params)
        result = (
            response.json().get("data", {}) if response else {"error": "Failed to fetch data from Hunter.io"}
        )
        return json.dumps(result)


# For backward compatibility
SearchMailHunter = HunterIOTool
