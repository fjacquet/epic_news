"""Base classes and common functionality for GitHub-related tools."""
import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubBaseTool:
    """Base class for GitHub tools with common functionality."""
    api_key: Optional[str] = None
    session: requests.Session = None

    def __init__(self, api_key: str = None, **data):
        """Initialize with API key and create a session."""
        # If api_key is not provided, try to get it from data
        if api_key is None and 'api_key' in data:
            api_key = data.pop('api_key')

        if api_key is None:
            raise ValueError("GitHub API key is required")

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

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
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
            logger.error(f"GitHub API request failed: {e}")
            return None

    def _extract_github_org_from_url(self, url: str) -> Optional[str]:
        """Extract organization name from GitHub URL."""
        import re
        pattern = r"github\.com/(?:orgs/)?([^/]+)/?"
        match = re.search(pattern, url.lower())
        return match.group(1) if match else None
