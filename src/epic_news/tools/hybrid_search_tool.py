"""
Hybrid Search Tool that combines Perplexity, Brave Search, and SerperDevTool.

Search provider hierarchy:
1. PRIMARY: Perplexity - AI-powered synthesis with citations
2. FALLBACK 1: Brave - Quality web results
3. FALLBACK 2: Serper - Existing integration as last resort
"""

import json
from typing import Any

from crewai.tools import BaseTool
from crewai_tools import BraveSearchTool, SerperDevTool
from pydantic import BaseModel, Field

from epic_news.tools.perplexity_search_tool import PerplexitySearchTool
from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


class HybridSearchInput(BaseModel):
    """Input schema for Hybrid Search Tool."""

    search_query: str = Field(..., description="The search query to execute")
    country: str | None = Field("", description="Country code for localized results")
    n_results: int | None = Field(10, description="Number of results to return")
    prefer_brave: bool | None = Field(True, description="Whether to prefer Brave Search over SerperDev")


class HybridSearchTool(BaseTool):
    """
    Hybrid search tool with cascading fallback.

    Search provider hierarchy:
    1. PRIMARY: Perplexity - AI-powered synthesis with citations
    2. FALLBACK 1: Brave - Quality web results
    3. FALLBACK 2: Serper - Existing integration as last resort
    """

    name: str = "hybrid_search_tool"
    description: str = (
        "Hybrid search tool with cascading fallback for maximum reliability. "
        "Uses Perplexity AI first for synthesized answers, Brave for quality web results, "
        "and Serper as final fallback. Returns normalized search results."
    )
    args_schema: type[BaseModel] = HybridSearchInput

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Initialize tools in a method that doesn't conflict with Pydantic
        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize search tools with cascading fallback order."""
        # Perplexity as PRIMARY
        try:
            self._perplexity_tool: PerplexitySearchTool | None = PerplexitySearchTool()
            if not self._perplexity_tool.api_key:
                self._perplexity_tool = None
        except Exception as e:
            logger.warning("PerplexitySearchTool initialization failed: {}", str(e))
            self._perplexity_tool = None

        # Brave as FALLBACK 1
        try:
            self._brave_tool: BraveSearchTool | None = BraveSearchTool()
        except Exception as e:
            logger.warning("BraveSearchTool initialization failed: {}", str(e))
            self._brave_tool = None

        # Serper as FALLBACK 2
        try:
            self._serper_tool: SerperDevTool | None = SerperDevTool(n_results=25, search_type="search")
            self._serper_news_tool: SerperDevTool | None = SerperDevTool(n_results=25, search_type="news")
        except ImportError:
            logger.warning("SerperDevTool not available")
            self._serper_tool = None
            self._serper_news_tool = None

    def _run(
        self,
        search_query: str,
        country: str = "",
        n_results: int = 10,
        prefer_brave: bool = True,
    ) -> str:
        """
        Execute a hybrid search with cascading fallback.

        Search order:
        1. Perplexity (PRIMARY) - AI-powered synthesis
        2. Brave (FALLBACK 1) - Quality web results
        3. Serper (FALLBACK 2) - Standard search
        4. Serper News (FALLBACK 3) - News-specific search

        Args:
            search_query: The search query to execute
            country: Country code for localized results (unused, for API compat)
            n_results: Number of results to return (unused, for API compat)
            prefer_brave: Legacy parameter (ignored, Perplexity is always primary)

        Returns:
            JSON string containing combined search results
        """
        # Suppress unused parameter warnings
        _ = country, n_results, prefer_brave

        results: dict[str, Any] = {
            "query": search_query,
            "sources_used": [],
            "results": [],
            "success": False,
            "errors": [],
        }

        # Ensure tools are initialized
        if not hasattr(self, "_perplexity_tool"):
            self._initialize_tools()

        # 1. Try Perplexity first (PRIMARY)
        if self._perplexity_tool:
            try:
                logger.info("Attempting Perplexity Search for: {}", search_query)
                perplexity_result = self._perplexity_tool._run(search_query)
                perplexity_data = json.loads(perplexity_result)

                if perplexity_data.get("success") and not perplexity_data.get("fallback_needed"):
                    logger.info("Perplexity Search successful")
                    results["sources_used"].append("perplexity")
                    results["results"].extend(self._normalize_perplexity_results(perplexity_data))
                    results["success"] = True
                else:
                    logger.warning(
                        "Perplexity failed: {}",
                        perplexity_data.get("error", "Unknown"),
                    )
                    results["errors"].append(f"Perplexity: {perplexity_data.get('error', 'Failed')}")

            except Exception as e:
                logger.error("Perplexity exception: {}", str(e))
                results["errors"].append(f"Perplexity exception: {str(e)}")

        # 2. Try Brave as FALLBACK 1
        if not results["success"] and self._brave_tool:
            try:
                logger.info("Attempting Brave Search for: {}", search_query)
                brave_result = self._brave_tool._run(search_query)  # type: ignore[call-arg]
                brave_data = json.loads(brave_result)

                if brave_data.get("success") and not brave_data.get("fallback_needed"):
                    logger.info("Brave Search successful")
                    results["sources_used"].append("brave_search")
                    results["results"].extend(self._normalize_brave_results(brave_data.get("results", [])))
                    results["success"] = True
                else:
                    logger.warning("Brave Search failed: {}", brave_data.get("error", "Unknown"))
                    results["errors"].append(f"Brave Search: {brave_data.get('error', 'Failed')}")

            except Exception as e:
                logger.error("Brave Search exception: {}", str(e))
                results["errors"].append(f"Brave Search exception: {str(e)}")

        # 3. Try Serper as FALLBACK 2
        if not results["success"] and self._serper_tool:
            try:
                logger.info("Using SerperDev search for: {}", search_query)
                serper_result = self._serper_tool._run(search_query)  # type: ignore[call-arg]

                if serper_result:
                    logger.info("SerperDev search successful")
                    results["sources_used"].append("serper_dev")
                    results["results"].extend(self._normalize_serper_results(serper_result))
                    results["success"] = True
                else:
                    logger.warning("SerperDev returned empty results")
                    results["errors"].append("SerperDev: Empty results")

            except Exception as e:
                logger.error("SerperDev exception: {}", str(e))
                results["errors"].append(f"SerperDev exception: {str(e)}")

        # 4. Final fallback: Serper News
        if not results["success"] and self._serper_news_tool:
            try:
                logger.info("Trying news-specific search for: {}", search_query)
                news_result = self._serper_news_tool._run(search_query)  # type: ignore[call-arg]

                if news_result:
                    logger.info("News search successful")
                    results["sources_used"].append("serper_news")
                    results["results"].extend(self._normalize_serper_results(news_result))
                    results["success"] = True
                else:
                    results["errors"].append("SerperNews: Empty results")

            except Exception as e:
                logger.error("News search exception: {}", str(e))
                results["errors"].append(f"News search exception: {str(e)}")

        # Log final results
        if results["success"]:
            logger.info(
                "Hybrid search successful using: {}",
                ", ".join(results["sources_used"]),
            )
        else:
            logger.error("All search methods failed for query: {}", search_query)

        return json.dumps(results)

    def _normalize_brave_results(self, brave_results: Any) -> list[dict[str, Any]]:
        """Normalize Brave Search results to common format."""
        normalized: list[dict[str, Any]] = []

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
            logger.error("Error normalizing Brave results: {}", str(e))

        return normalized

    def _normalize_serper_results(self, serper_results: Any) -> list[dict[str, Any]]:
        """Normalize SerperDev results to common format."""
        normalized: list[dict[str, Any]] = []

        try:
            serper_data = json.loads(serper_results) if isinstance(serper_results, str) else serper_results

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
            logger.error("Error normalizing Serper results: {}", str(e))

        return normalized

    def _normalize_perplexity_results(self, perplexity_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize Perplexity results to common format."""
        normalized: list[dict[str, Any]] = []

        try:
            # Main answer as first result
            if answer := perplexity_data.get("answer"):
                normalized.append(
                    {
                        "title": "Perplexity AI Summary",
                        "url": "",
                        "snippet": answer[:500] + "..." if len(answer) > 500 else answer,
                        "full_answer": answer,
                        "source": "perplexity",
                    }
                )

            # Citations as additional results
            for i, citation in enumerate(perplexity_data.get("citations", [])):
                normalized.append(
                    {
                        "title": f"Citation {i + 1}",
                        "url": citation if isinstance(citation, str) else citation.get("url", ""),
                        "snippet": "",
                        "source": "perplexity_citation",
                    }
                )

        except Exception as e:
            logger.error("Error normalizing Perplexity results: {}", str(e))

        return normalized
