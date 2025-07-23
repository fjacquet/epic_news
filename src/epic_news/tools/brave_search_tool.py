"""
Brave Search Tool for enhanced news search with better link reliability.
"""

import json
import os
from typing import Optional

from crewai.tools import BaseTool
from crewai_tools import BraveSearchTool as CrewAIBraveSearchTool
from pydantic import BaseModel, Field

from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


class BraveSearchInput(BaseModel):
    """Input schema for Brave Search Tool."""

    search_query: str = Field(..., description="The search query to execute")
    country: Optional[str] = Field("", description="Country code for localized results (e.g., 'CH', 'FR')")
    n_results: Optional[int] = Field(10, description="Number of results to return")


class BraveSearchTool(BaseTool):
    """
    Enhanced search tool using Brave Search API for better link reliability.
    Brave Search often provides more reliable and up-to-date links compared to other search engines.
    """

    name: str = "brave_search_tool"
    description: str = (
        "Search the internet using Brave Search API. "
        "Provides reliable, up-to-date search results with working links. "
        "Particularly effective for news and current events."
    )
    args_schema: type[BaseModel] = BraveSearchInput

    def _run(self, search_query: str, country: str = "", n_results: int = 10) -> str:
        """
        Execute a search using Brave Search API.

        Args:
            search_query: The search query to execute
            country: Country code for localized results
            n_results: Number of results to return

        Returns:
            JSON string containing search results
        """
        try:
            # Check if Brave API key is available
            api_key = os.getenv("BRAVE_API_KEY")
            if not api_key:
                logger.warning("BRAVE_API_KEY not found, Brave Search unavailable")
                return json.dumps(
                    {"error": "Brave Search API key not configured", "results": [], "fallback_needed": True}
                )

            # Import BraveSearchTool from crewai_tools
            try:
                # Initialize the CrewAI Brave Search tool
                brave_tool = CrewAIBraveSearchTool(country=country, n_results=n_results, save_file=False)

                # Execute the search
                results = brave_tool.run(search_query=search_query)

                logger.info(f"Brave Search executed successfully for query: {search_query}")

                # Parse and return results
                if isinstance(results, str):
                    try:
                        parsed_results = json.loads(results)
                        return json.dumps(
                            {
                                "source": "brave_search",
                                "query": search_query,
                                "results": parsed_results,
                                "success": True,
                            }
                        )
                    except json.JSONDecodeError:
                        # If results are not JSON, wrap them
                        return json.dumps(
                            {
                                "source": "brave_search",
                                "query": search_query,
                                "results": results,
                                "success": True,
                            }
                        )
                else:
                    return json.dumps(
                        {"source": "brave_search", "query": search_query, "results": results, "success": True}
                    )

            except ImportError:
                logger.error("crewai_tools BraveSearchTool not available")
                return json.dumps(
                    {
                        "error": "BraveSearchTool not available in crewai_tools",
                        "results": [],
                        "fallback_needed": True,
                    }
                )

        except Exception as e:
            logger.error(f"Error in Brave Search: {str(e)}")
            return json.dumps(
                {"error": f"Brave Search failed: {str(e)}", "results": [], "fallback_needed": True}
            )
