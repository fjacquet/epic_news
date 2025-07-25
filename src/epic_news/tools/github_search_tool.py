"""GitHub search tool implementation."""

import json
import os

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel

from epic_news.models.github_models import GitHubSearchInput

from .github_base import GitHubBaseTool

# Load environment variables from .env file
load_dotenv()


class GitHubSearchTool(BaseTool, GitHubBaseTool):
    """Tool for searching GitHub."""

    name: str = "github_search"
    description: str = "Search GitHub for repositories, code, issues, or users"
    args_schema: type[BaseModel] = GitHubSearchInput
    headers: dict

    def __init__(self, **data):
        """Initialize with GitHub token from environment."""
        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        # Add headers to the data dict before calling super().__init__
        if "headers" not in data:
            data["headers"] = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

        # Initialize the base classes
        super().__init__(**data)
        GitHubBaseTool.__init__(self, api_key=github_token)

    def _run(self, query: str, search_type: str = "repositories", max_results: int = 5) -> str:
        """Search GitHub."""
        search_type = search_type.lower()
        if search_type not in ["repositories", "code", "issues", "users"]:
            return json.dumps(
                {"error": "Invalid search type. Must be one of: repositories, code, issues, users"}
            )

        url = f"https://api.github.com/search/{search_type}"
        params = {"q": query, "per_page": min(max_results, 10)}

        response = self._make_request("GET", url, headers=self.headers, params=params)

        if not response:
            return json.dumps({"error": f"Failed to search GitHub {search_type}"})

        results = response.json().get("items", [])

        # Format results based on search type
        if search_type == "repositories":
            formatted_results = [
                {
                    "name": r["full_name"],
                    "url": r["html_url"],
                    "description": r.get("description", ""),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                }
                for r in results
            ]
        elif search_type == "code":
            formatted_results = [
                {
                    "name": r["name"],
                    "path": r["path"],
                    "repository": r["repository"]["full_name"],
                    "url": r["html_url"],
                }
                for r in results
            ]
        elif search_type == "issues":
            formatted_results = [
                {
                    "title": r["title"],
                    "url": r["html_url"],
                    "state": r["state"],
                    "comments": r["comments"],
                    "created_at": r["created_at"],
                }
                for r in results
            ]
        else:  # users
            formatted_results = [
                {"login": r["login"], "url": r["html_url"], "type": r["type"], "score": r["score"]}
                for r in results
            ]

        return json.dumps(
            {
                "query": query,
                "search_type": search_type,
                "total_count": response.json().get("total_count", 0),
                "results": formatted_results,
            }
        )
