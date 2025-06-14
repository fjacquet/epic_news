"""GitHub organization search tool implementation."""
from typing import Dict, Any
import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

from .github_base import GitHubBaseTool
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = logging.getLogger(__name__)
class GitHubOrgSearchInput(BaseModel):
    """Input schema for GitHub organization search."""
    org_name: str = Field(..., description="Name of the GitHub organization to search for")

class GitHubOrgSearchTool(BaseTool, GitHubBaseTool):
    serper_api_key: str | None = None
    """Tool for searching GitHub organizations."""
    name: str = "github_org_search"
    description: str = "Search for a GitHub organization and retrieve basic information"
    args_schema: type[BaseModel] = GitHubOrgSearchInput
    
    def __init__(self, **data):
        """Initialize with GitHub token from environment."""
        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
            
        # Initialize the base classes
        BaseTool.__init__(self, **data)
        GitHubBaseTool.__init__(self, api_key=github_token) # For GitHubBaseTool's own use of api_key
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
    def _run(self, org_name: str) -> str:
        """Search for a GitHub organization."""
        if not org_name:
            return json.dumps({"error": "Organization name cannot be empty"})
            
        # First try direct GitHub API if we have a token
        github_token_available = bool(os.getenv("GITHUB_TOKEN"))

        if github_token_available:
            logger.info(f"Attempting to search GitHub API for organization: {org_name}")
            return self._search_github_api(org_name)
        
        logger.info(f"GITHUB_TOKEN not found. Attempting fallback search with Serper for organization: {org_name}")
        if self.serper_api_key:
            return self._search_with_serper(org_name)
        
        logger.error("Configuration error: Neither GITHUB_TOKEN nor SERPER_API_KEY is set.")
        return json.dumps({"error": "Configuration error: Neither GITHUB_TOKEN nor SERPER_API_KEY is set."})
    
    def _search_github_api(self, org_name: str) -> str:
        """Search using GitHub API."""
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token: # Should not happen if _run logic is correct, but defensive
            logger.error("GITHUB_TOKEN not available for _search_github_api")
            return json.dumps({"error": "GitHub API token not available."})
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"https://api.github.com/orgs/{org_name}"
        
        response = self._make_request("GET", url, headers=headers)
        if not response:
            logger.error(f"Failed to fetch data from GitHub API for organization: {org_name}")
            return json.dumps({"error": f"Failed to fetch data from GitHub API for organization: {org_name}"})
            
        org_data = response.json()
        
        # Get organization repositories
        repos_url = org_data.get("repos_url")
        repos = []
        if repos_url:
            repos_response = self._make_request("GET", repos_url, headers=headers)
            if repos_response:
                try:
                    repos_data = repos_response.json()
                    if isinstance(repos_data, list):
                        repos = [{"name": r.get("name"), "url": r.get("html_url")} for r in repos_data]
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON from GitHub repos response for {org_name}. Response: {repos_response.text[:200]}")
                    # repos remains empty
        
        result = {
            "exists": True,
            "name": org_data.get("name"),
            "login": org_data.get("login"),
            "url": org_data.get("html_url"),
            "description": org_data.get("description"),
            "public_repos": org_data.get("public_repos", 0),
            "followers": org_data.get("followers", 0),
            "top_repos": repos[:5] if repos else []
        }
        return json.dumps(result)
    
    def _search_with_serper(self, org_name: str) -> str:
        """Search using Serper API as fallback."""
        if not self.serper_api_key:
            logger.error("SERPER_API_KEY not configured for fallback search.")
            return json.dumps({"error": "SERPER_API_KEY not configured for fallback search."})

        headers = {
            "X-API-KEY": self.serper_api_key, # Use dedicated Serper API key
            "Content-Type": "application/json"
        }
        query = f'site:github.com/orgs "{org_name}"'
        payload = {"q": query}
        
        response = self._make_request(
            "POST",
            "https://google.serper.dev/search",
            headers=headers,
            json=payload
        )
        
        if not response:
            logger.error(f"Failed to fetch data from Serper API for query: {query}")
            return json.dumps({"error": "Failed to fetch data from Serper API"})
            
        results = response.json().get("organic", [])
        
        for result in results:
            link = result.get("link", "")
            if f"github.com/{org_name.lower()}" in link.lower() or f"github.com/orgs/{org_name.lower()}" in link.lower():
                return json.dumps({
                    "exists": True,
                    "name": org_name,
                    "url": link,
                    "source": "serper"
                })
        
        logger.info(f"Organization {org_name} not found via Serper fallback.")
        return json.dumps({"exists": False, "name": org_name, "source": "serper"})

# For backward compatibility
SearchGithub = GitHubOrgSearchTool
