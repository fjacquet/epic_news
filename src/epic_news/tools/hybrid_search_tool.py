"""
Hybrid Search Tool that combines Brave Search and SerperDevTool for maximum reliability.
"""

import json
from typing import Any, Optional

from crewai.tools import BaseTool
from crewai_tools import BraveSearchTool, SerperDevTool
from pydantic import BaseModel, Field

from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


class HybridSearchInput(BaseModel):
    """Input schema for Hybrid Search Tool."""

    search_query: str = Field(..., description="The search query to execute")
    country: Optional[str] = Field("", description="Country code for localized results")
    n_results: Optional[int] = Field(10, description="Number of results to return")
    prefer_brave: Optional[bool] = Field(True, description="Whether to prefer Brave Search over SerperDev")


class HybridSearchTool(BaseTool):
    """
    Hybrid search tool that combines Brave Search and SerperDevTool.
    Uses Brave Search first for better link reliability, falls back to SerperDev if needed.
    """

    name: str = "hybrid_search_tool"
    description: str = (
        "Hybrid search tool that combines Brave Search and SerperDevTool for maximum reliability. "
        "Uses Brave Search first for better link quality, falls back to SerperDev if needed. "
        "Ideal for news search with reliable, working links."
    )
    args_schema: type[BaseModel] = HybridSearchInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize tools in a method that doesn't conflict with Pydantic
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize search tools."""
        try:
            self._brave_tool = BraveSearchTool()
        except Exception as e:
            logger.warning(f"BraveSearchTool initialization failed: {e}")
            self._brave_tool = None

        # Initialize SerperDev tools directly to avoid circular import
        try:
            self._serper_tool = SerperDevTool(n_results=25, search_type="search")
            self._serper_news_tool = SerperDevTool(n_results=25, search_type="news")
        except ImportError:
            logger.warning("SerperDevTool not available")
            self._serper_tool = None
            self._serper_news_tool = None

    def _run(
        self, search_query: str, country: str = "", n_results: int = 10, prefer_brave: bool = True
    ) -> str:
        """
        Execute a hybrid search using Brave Search first, then SerperDev as fallback.

        Args:
            search_query: The search query to execute
            country: Country code for localized results
            n_results: Number of results to return
            prefer_brave: Whether to prefer Brave Search over SerperDev

        Returns:
            JSON string containing combined search results
        """
        results = {"query": search_query, "sources_used": [], "results": [], "success": False, "errors": []}

        # Ensure tools are initialized
        if not hasattr(self, "_brave_tool"):
            self._initialize_tools()

        # Try Brave Search first if preferred and available
        if prefer_brave and self._brave_tool:
            try:
                logger.info(f"Attempting Brave Search for: {search_query}")
                brave_result = self._brave_tool._run(search_query, country, n_results)
                brave_data = json.loads(brave_result)

                if brave_data.get("success") and not brave_data.get("fallback_needed"):
                    logger.info("Brave Search successful")
                    results["sources_used"].append("brave_search")
                    results["results"].extend(self._normalize_brave_results(brave_data.get("results", [])))
                    results["success"] = True
                else:
                    logger.warning(
                        f"Brave Search failed or needs fallback: {brave_data.get('error', 'Unknown error')}"
                    )
                    results["errors"].append(f"Brave Search: {brave_data.get('error', 'Failed')}")

            except Exception as e:
                logger.error(f"Brave Search exception: {str(e)}")
                results["errors"].append(f"Brave Search exception: {str(e)}")

        # Use SerperDev as fallback or primary if Brave failed/unavailable
        if not results["success"] and self._serper_tool:
            try:
                logger.info(f"Using SerperDev search for: {search_query}")
                serper_result = self._serper_tool._run(search_query)

                if serper_result:
                    logger.info("SerperDev search successful")
                    results["sources_used"].append("serper_dev")
                    results["results"].extend(self._normalize_serper_results(serper_result))
                    results["success"] = True
                else:
                    logger.warning("SerperDev returned empty results")
                    results["errors"].append("SerperDev: Empty results")

            except Exception as e:
                logger.error(f"SerperDev search exception: {str(e)}")
                results["errors"].append(f"SerperDev exception: {str(e)}")

        # If both failed, try news-specific search
        if not results["success"] and self._serper_news_tool:
            try:
                logger.info(f"Trying news-specific search for: {search_query}")
                news_result = self._serper_news_tool._run(search_query)

                if news_result:
                    logger.info("News search successful")
                    results["sources_used"].append("serper_news")
                    results["results"].extend(self._normalize_serper_results(news_result))
                    results["success"] = True
                else:
                    results["errors"].append("SerperNews: Empty results")

            except Exception as e:
                logger.error(f"News search exception: {str(e)}")
                results["errors"].append(f"News search exception: {str(e)}")

        # Log final results
        if results["success"]:
            logger.info(f"Hybrid search successful using: {', '.join(results['sources_used'])}")
        else:
            logger.error(f"All search methods failed for query: {search_query}")

        return json.dumps(results)

    def _normalize_brave_results(self, brave_results: Any) -> list[dict[str, Any]]:
        """Normalize Brave Search results to common format."""
        normalized = []

        try:
            if isinstance(brave_results, list):
                for item in brave_results:
                    if isinstance(item, dict):
                        normalized.append(
                            {
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("description", item.get("snippet", "")),
                                "source": "brave_search",
                            }
                        )
            elif isinstance(brave_results, dict):
                # Handle different Brave result formats
                web_results = brave_results.get("web", {}).get("results", [])
                for item in web_results:
                    normalized.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("description", ""),
                            "source": "brave_search",
                        }
                    )
        except Exception as e:
            logger.error(f"Error normalizing Brave results: {str(e)}")

        return normalized

    def _normalize_serper_results(self, serper_results: Any) -> list[dict[str, Any]]:
        """Normalize SerperDev results to common format."""
        normalized = []

        try:
            if isinstance(serper_results, str):
                serper_data = json.loads(serper_results)
            else:
                serper_data = serper_results

            # Handle organic results
            organic = serper_data.get("organic", [])
            for item in organic:
                normalized.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "serper_dev",
                    }
                )

            # Handle news results if available
            news = serper_data.get("news", [])
            for item in news:
                normalized.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", ""),
                        "source": "serper_news",
                    }
                )

        except Exception as e:
            logger.error(f"Error normalizing Serper results: {str(e)}")

        return normalized
