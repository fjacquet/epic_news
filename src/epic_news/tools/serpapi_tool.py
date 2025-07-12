"""Web search tool implementation using SerpAPI."""

import json
import os

import requests
from crewai.tools import BaseTool
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel

from src.epic_news.models.web_search_models import SerpApiInput

# Load environment variables from .env file
load_dotenv()


class SerpApiTool(BaseTool):
    """Tool for performing web searches using SerpAPI."""

    name: str = "serpapi_search"
    description: str = "Perform a web search to find information on the internet"
    args_schema: type[BaseModel] = SerpApiInput
    api_key: str

    def __init__(self, **data):
        """Initialize with API key from environment."""
        if "api_key" not in data:
            api_key_from_env = os.getenv("SERPAPI_API_KEY")
            if not api_key_from_env:
                raise ValueError("SERPAPI_API_KEY environment variable not set")
            data["api_key"] = api_key_from_env
        super().__init__(**data)

    def _run(self, **kwargs) -> str:
        """
        Perform a web search using SerpAPI.

        Args:
            query: The search query
            num_results: Number of results to return (1-10)
            country: Country code for localized results (e.g., 'us', 'uk')
            language: Language code for results (e.g., 'en', 'fr')
            page: Pagination number

        Returns:
            JSON string containing search results or error message
        """
        query = kwargs.get("query", "")
        num_results = kwargs.get("num_results", 5)
        country = kwargs.get("country", "us")
        language = kwargs.get("language", "en")
        page = kwargs.get("page", 1)

        # Validate query
        if not query or not isinstance(query, str) or len(query.strip()) < 2:
            error_msg = "Search query must be a non-empty string with at least 2 characters"
            return json.dumps({"error": error_msg, "query": query})

        # Prepare API request
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "start": (page - 1) * num_results + 1,
            "hl": language,
            "gl": country,
            "safe": "active",
        }

        try:
            # For debugging - print the request details (without API key)
            debug_params = params.copy()
            if "api_key" in debug_params:
                debug_params["api_key"] = "***"

            # Log the request details for debugging
            logger.debug(f"Sending request to: {url}")  # Changed to logger.debug
            logger.debug(f"Parameters: {json.dumps(debug_params, indent=2)}")  # Changed to logger.debug

            # Make the API request with proper error handling
            try:
                response = requests.get(url, params=params, timeout=30)
                logger.debug(f"Response status: {response.status_code}")  # Changed to logger.debug
            except requests.exceptions.Timeout:
                return json.dumps(
                    {
                        "error": "Request timed out. The SerpAPI server took too long to respond.",
                        "query": query,
                        "suggestion": "Try again later or with a simpler query.",
                    }
                )
            except requests.exceptions.ConnectionError:
                return json.dumps(
                    {
                        "error": "Connection error. Could not connect to the SerpAPI server.",
                        "query": query,
                        "suggestion": "Check your internet connection or try again later.",
                    }
                )

            if response.status_code != 200:
                return json.dumps(
                    {
                        "error": f"API request failed with status {response.status_code}",
                        "query": query,
                        "response": response.text[:500],  # Include first 500 chars of response
                    }
                )

            data = response.json()

            # Check for API errors
            if "error" in data:
                return json.dumps(
                    {"error": f"API error: {data.get('error', 'Unknown error')}", "query": query}
                )

            # Extract organic results
            results = []
            items = data.get("organic_results", [])

            for item in items[:num_results]:
                result = {
                    "title": item.get("title", "No title available"),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "No description available"),
                    "source": "web_search",
                }
                results.append(result)

            if not results:
                return json.dumps(
                    {
                        "error": f"No results found for query: {query}",
                        "query": query,
                        "suggestion": "Try a different search query or check your API key's search quota",
                    }
                )

            return json.dumps({"query": query, "results": results, "count": len(results)}, indent=2)

        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"Error performing search: {str(e)}", "query": query})
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Error parsing API response: {str(e)}", "query": query})
        except Exception as e:
            return json.dumps(
                {"error": f"Unexpected error: {str(e)}", "query": query, "type": type(e).__name__}
            )



