"""Base classes and common functionality for email search tools."""
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from epic_news.utils.logger import get_logger  # Added project logger

# Use project's logger
logger = get_logger(__name__)

class EmailSearchTool:
    """Base class for email search tools with common functionality."""

    def __init__(self, api_key: str):
        """Initialize with API key and create a session."""
        self.api_key = api_key
        self.session = self._create_session()

    @staticmethod
    def _create_session() -> requests.Session:
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

    @staticmethod
    def _extract_emails(text: str) -> set[str]:
        """Extract email addresses from text using regex."""
        email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.+]+"
        return set(re.findall(email_regex, text))

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response | None:
        """Make an HTTP request with error handling."""
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
