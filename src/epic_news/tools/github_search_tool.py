"""GitHub search tool implementation."""
from typing import Dict, Any
import json
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os

from .github_base import GitHubBaseTool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class GitHubSearchInput(BaseModel):
    """Input schema for GitHub search."""
    query: str = Field(..., description="Search query for GitHub")
    search_type: str = Field(
        default="repositories",
        description="Type of search: 'repositories', 'code', 'issues', or 'users'"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return",
        ge=1,
        le=10
    )

class GitHubSearchTool(BaseTool, GitHubBaseTool):
    """Tool for searching GitHub."""
    name: str = "github_search"
    description: str = "Search GitHub for repositories, code, issues, or users"
    args_schema: type[BaseModel] = GitHubSearchInput
    headers: Dict[str, str] = None
    
    def __init__(self, **data):
        """Initialize with GitHub token from environment."""
        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
            
        # Initialize the base classes
        BaseTool.__init__(self, **data)
        GitHubBaseTool.__init__(self, api_key=github_token)
        
        # Set up headers
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _run(self, query: str, search_type: str = "repositories", max_results: int = 5) -> str:
        """Search GitHub."""
        search_type = search_type.lower()
        if search_type not in ["repositories", "code", "issues", "users"]:
            return json.dumps({"error": "Invalid search type. Must be one of: repositories, code, issues, users"})
        
        url = f"https://api.github.com/search/{search_type}"
        params = {"q": query, "per_page": min(max_results, 10)}
        
        response = self._make_request(
            "GET",
            url,
            headers=self.headers,
            params=params
        )
        
        if not response:
            return json.dumps({"error": f"Failed to search GitHub {search_type}"})
            
        results = response.json().get("items", [])
        
        # Format results based on search type
        if search_type == "repositories":
            formatted_results = [{
                "name": r["full_name"],
                "url": r["html_url"],
                "description": r.get("description", ""),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0)
            } for r in results]
        elif search_type == "code":
            formatted_results = [{
                "name": r["name"],
                "path": r["path"],
                "repository": r["repository"]["full_name"],
                "url": r["html_url"]
            } for r in results]
        elif search_type == "issues":
            formatted_results = [{
                "title": r["title"],
                "url": r["html_url"],
                "state": r["state"],
                "comments": r["comments"],
                "created_at": r["created_at"]
            } for r in results]
        else:  # users
            formatted_results = [{
                "login": r["login"],
                "url": r["html_url"],
                "type": r["type"],
                "score": r["score"]
            } for r in results]
        
        return json.dumps({"query": query, "search_type": search_type, "total_count": response.json().get("total_count", 0), "results": formatted_results})
