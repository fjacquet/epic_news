"""Factory functions for creating GitHub-related tools."""
import os
from typing import List

from crewai.tools import BaseTool
from dotenv import load_dotenv

from .github_search_tool import GitHubSearchTool

# Load environment variables from .env file
load_dotenv()

def get_github_tools() -> List[BaseTool]:
    """Initializes and returns a list of GitHub tools."""
    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Warning: GITHUB_TOKEN environment variable not set. GitHubSearchTool will not be available.")
        return []
    
    return [GitHubSearchTool()]
