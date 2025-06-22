"""Base classes and common functionality for search tools."""
import logging
from typing import Any, TypeVar

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseSearchTool:
    """Base class for search tools with common functionality."""
    api_key: str | None = None
    session: requests.Session | None = None

    def __init__(self, api_key: str, **data):
        """Initialize with API key and create a session."""
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,  # Maximum number of retries
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[500, 502, 503, 504],  # Retry on these status codes
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response | None:
        """Make an HTTP request with error handling."""
        try:
            response = self.session.request(
                method,
                url,
                timeout=10,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _search_serper(self, query: str) -> dict[str, Any] | None:
        """
        Perform a search using the Serper API.
        
        Args:
            query: The search query string
            
        Returns:
            Dict containing search results or error information
        """
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}

        logger.info(f"Performing search with query: {query}")
        response = self._make_request("POST", url, headers=headers, json=payload)

        if not response:
            logger.error("No response received from search API")
            return None

        try:
            data = response.json()
            logger.debug(f"Search API response: {data}")

            # Check for API errors
            if 'error' in data:
                logger.error(f"Search API error: {data.get('message', 'Unknown error')}")
                return None

            return data

        except ValueError as e:
            logger.error(f"Failed to parse search response: {e}")
            return None
