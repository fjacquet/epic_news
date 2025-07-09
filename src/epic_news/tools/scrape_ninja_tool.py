import json
import os

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

from src.epic_news.models.web_search_models import ScrapeNinjaInput

# Load environment variables from .env file
load_dotenv()


class ScrapeNinjaTool(BaseTool):
    """
    A tool for scraping website content using the ScrapeNinja API.

    This tool allows for advanced web scraping of HTML content. It can handle
    JavaScript-rendered pages and provides options for geo-targeting, custom
    headers, and more.

    Note: This tool is designed for scraping web pages (HTML) and does not
    support PDF content extraction.
    """

    name: str = "ScrapeNinja"
    description: str = "Scrapes website content using the ScrapeNinja API with advanced options"
    args_schema: type[BaseModel] = ScrapeNinjaInput
    api_key: str | None = None

    def __init__(self, **data):
        """Initialize with API key from environment."""
        # Initialize parent class first
        super().__init__(**data)

        # Get API key from environment
        self.api_key = os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable not set")

    def _run(self, **kwargs) -> str:
        """Scrape a website using ScrapeNinja API with advanced options"""
        api_url = "https://scrapeninja.p.rapidapi.com/scrape"

        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "scrapeninja.p.rapidapi.com",
        }

        payload = {
            "url": kwargs["url"],
            "retryNum": kwargs.get("retry_num", 1),
            "followRedirects": kwargs.get("follow_redirects", 1),
            "timeout": kwargs.get("timeout", 8),
        }

        # Add optional parameters if provided
        if "headers" in kwargs and kwargs["headers"]:
            payload["headers"] = kwargs["headers"]
        if "geo" in kwargs and kwargs["geo"]:
            payload["geo"] = kwargs["geo"]
        if "proxy" in kwargs and kwargs["proxy"]:
            payload["proxy"] = kwargs["proxy"]
        if "text_not_expected" in kwargs and kwargs["text_not_expected"]:
            payload["textNotExpected"] = kwargs["text_not_expected"]
        if "status_not_expected" in kwargs and kwargs["status_not_expected"]:
            payload["statusNotExpected"] = kwargs["status_not_expected"]
        if "extractor" in kwargs and kwargs["extractor"]:
            payload["extractor"] = kwargs["extractor"]

        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            content = response.text
            try:
                # Check if content is valid JSON, if so, return as is (it's already a string)
                json.loads(content)
                return content
            except json.JSONDecodeError:
                # If not JSON, wrap it in a JSON structure
                return json.dumps({"content": content})
        except Exception as e:
            return json.dumps({"error": f"Error scraping {kwargs['url']}: {str(e)}"})


def test_scrapeninja():
    """Test function with basic parameters"""
    tool = ScrapeNinjaTool()
    print("Testing basic ScrapeNinja functionality...")
    result = tool._run(url="https://www.free.fr/freebox/")
    print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")

    print(f"Result: {result}")


if __name__ == "__main__":
    test_scrapeninja()
