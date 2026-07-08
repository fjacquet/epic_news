import os
from typing import Literal, cast

from crewai.tools import BaseTool
from crewai_custom_tools import PerplexitySearchTool, SerpApiTool, TavilyTool


class WebSearchFactory:
    """Factory for creating web search tools."""

    @staticmethod
    def create(provider: Literal["perplexity", "serpapi", "tavily"]) -> BaseTool:
        """Create a web search tool based on the provider."""
        # crewai_custom_tools ships without a py.typed marker, so mypy sees its
        # exports as `Any`; cast() documents that these are BaseTool subclasses.
        if provider == "perplexity":
            if not os.getenv("PERPLEXITY_API_KEY"):
                return cast(BaseTool, TavilyTool())
            return cast(BaseTool, PerplexitySearchTool())
        if provider == "serpapi":
            return cast(BaseTool, SerpApiTool())
        if provider == "tavily":
            return cast(BaseTool, TavilyTool())
        raise ValueError(f"Unknown web search provider: {provider}")
