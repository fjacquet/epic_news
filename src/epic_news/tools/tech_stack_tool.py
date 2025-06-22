"""Technology stack analysis tool implementation."""
import json
import os
import re
from typing import Any, ClassVar

from crewai.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from epic_news.utils.logger import get_logger  # Added project logger

from .search_base import BaseSearchTool

# Load environment variables from .env file
load_dotenv()

# Use project's logger
logger = get_logger(__name__)

class TechStackInput(BaseModel):
    """Input schema for tech stack analysis."""
    domain: str = Field(..., description="Domain name to analyze (e.g., 'example.com')")
    detailed: bool = Field(
        default=False,
        description="Whether to return detailed information about each technology"
    )

class TechStackTool(BaseTool, BaseSearchTool):
    """Tool for analyzing the technology stack of websites."""
    name: str = "tech_stack_analysis"
    description: str = "Analyze the technology stack used by a website"
    args_schema: type[BaseModel] = TechStackInput
    api_key: str = None

    # Common technology patterns to look for
    TECH_PATTERNS: ClassVar[dict[str, list[str]]] = {
        'frameworks': [
            'react', 'angular', 'vue', 'next.js', 'nuxt.js', 'gatsby', 'svelte',
            'django', 'flask', 'laravel', 'ruby on rails', 'express', 'spring', 'asp.net'
        ],
        'cms': [
            'wordpress', 'drupal', 'joomla', 'wix', 'squarespace', 'shopify', 'webflow',
            'ghost', 'contentful', 'strapi', 'sanity'
        ],
        'analytics': [
            'google analytics', 'google tag manager', 'matomo', 'hotjar', 'mixpanel',
            'amplitude', 'segment', 'heap'
        ],
        'hosting': [
            'aws', 'google cloud', 'azure', 'cloudflare', 'vercel', 'netlify', 'heroku',
            'digitalocean', 'linode', 'vultr'
        ]
    }

    def __init__(self, **data):
        """Initialize with API key from environment."""
        # Get API key from environment
        api_key = os.getenv("SERPER_API_KEY") # Changed to SERPER_API_KEY
        if not api_key:
            raise ValueError("SERPER_API_KEY environment variable not set") # Changed to SERPER_API_KEY

        # Store API key in data for BaseTool initialization
        data['api_key'] = api_key

        # Initialize BaseTool with the API key in data
        BaseTool.__init__(self, **data)

        # Initialize BaseSearchTool with the API key
        BaseSearchTool.__init__(self, api_key=api_key)

    def _run(self, domain: str, detailed: bool = False) -> str:
        """
        Analyze the technology stack of a website.
        
        Args:
            domain: The domain to analyze (e.g., 'example.com')
            detailed: Whether to return detailed information
            
        Returns:
            Dictionary containing the technology stack information
        """
        try:
            # Perform searches on technology analysis sites
            tech_data = self._search_tech_sites(domain)

            # Extract technologies from search results
            tech_stack = self._extract_technologies(tech_data)

            # If detailed analysis is requested, perform additional checks
            detailed_info = {}
            if detailed:
                detailed_info = self._get_detailed_analysis(domain, tech_stack)

            result = {
                "domain": domain,
                "technologies": list(tech_stack),
                "detailed_analysis": detailed_info if detailed else None
            }
            return json.dumps(result)

        except Exception as e:
            logger.error(f"Error in tech stack analysis: {e}")
            error_result = {
                "domain": domain,
                "error": f"An error occurred during analysis: {str(e)}"
            }
            return json.dumps(error_result)

    def _search_tech_sites(self, domain: str) -> list[dict[str, Any]]:
        """Search technology analysis sites for the given domain."""
        query = f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain}"
        results = self._search_serper(query)
        return results.get("organic", []) if results else []

    def _extract_technologies(self, search_results: list[dict[str, Any]]) -> set[str]:
        """Extract technologies from search results."""
        technologies = set()

        for result in search_results:
            # Check title and snippet for technology mentions
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()

            # Look for technologies in the text
            for category, patterns in self.TECH_PATTERNS.items():
                for pattern in patterns:
                    if re.search(rf'\b{pattern}\b', text):
                        technologies.add(pattern.replace('\\.', '.'))

        return technologies

    def _get_detailed_analysis(self, domain: str, technologies: set[str]) -> dict[str, Any]:
        """Perform detailed analysis of the technologies."""
        analysis = {}

        # Categorize technologies
        for category, patterns in self.TECH_PATTERNS.items():
            category_techs = []
            for tech in technologies:
                for pattern in patterns:
                    if re.search(rf'\b{pattern}\b', tech.lower()):
                        category_techs.append(tech)
                        break
            if category_techs:
                analysis[category] = category_techs

        return analysis

# For backward compatibility
SearchStack = TechStackTool
