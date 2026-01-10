import json
import os

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

try:
    # Firecrawl SDK (declared in pyproject.toml as firecrawl-py)
    from firecrawl import FirecrawlApp, ScrapeOptions
except Exception as _e:  # pragma: no cover
    FirecrawlApp = None
    ScrapeOptions = None

from epic_news.models.web_search_models import ScrapeNinjaInput

# Load environment variables from .env file
load_dotenv()


class FirecrawlTool(BaseTool):
    """
    A tool for scraping website content using the Firecrawl API.

    Matches the ScrapeNinjaTool interface so it can be swapped via the factory
    using the WEB_SCRAPER_PROVIDER env var.
    """

    name: str = "FirecrawlScraper"
    description: str = "Scrapes website content using the Firecrawl API"
    # We reuse the same args_schema to keep a uniform interface across scrapers
    args_schema: type[BaseModel] = ScrapeNinjaInput
    api_key: str | None = None

    def __init__(self, **data):
        """Initialize with API key from environment."""
        super().__init__(**data)
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set")
        if FirecrawlApp is None:
            raise ImportError(
                "firecrawl SDK not available. Ensure 'firecrawl-py' is installed in your environment."
            )

    def _run(self, **kwargs) -> str:
        """Scrape a website using Firecrawl API and return a JSON string."""
        url = kwargs.get("url")
        if not url:
            return json.dumps({"error": "Missing required argument: url"})

        try:
            app = FirecrawlApp(api_key=self.api_key)
            # Request HTML content. Firecrawl can also return markdown, etc.
            data = app.scrape_url(url, formats=["html"])  # returns a dict
            # Always return a JSON string per project standard (PR-001)
            return json.dumps(data)
        except Exception as e:  # Broad by design to keep tool robust for agents
            return json.dumps({"error": f"Error scraping {url}: {str(e)}"})
