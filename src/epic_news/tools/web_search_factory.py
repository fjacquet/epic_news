import os
from typing import Literal

from crewai.tools import BaseTool

from epic_news.tools.perplexity_search_tool import PerplexitySearchTool
from epic_news.tools.serpapi_tool import SerpApiTool
from epic_news.tools.tavily_tool import TavilyTool


class WebSearchFactory:
    """Factory for creating web search tools."""

    @staticmethod
    def create(provider: Literal["perplexity", "serpapi", "tavily"]) -> BaseTool:
        """Create a web search tool based on the provider."""
        if provider == "perplexity":
            if not os.getenv("PERPLEXITY_API_KEY"):
                return TavilyTool()
            return PerplexitySearchTool()
        if provider == "serpapi":
            return SerpApiTool()
        if provider == "tavily":
            return TavilyTool()
        raise ValueError(f"Unknown web search provider: {provider}")
