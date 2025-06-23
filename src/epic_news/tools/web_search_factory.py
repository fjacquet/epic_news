from typing import Literal

from crewai.tools import BaseTool

from src.epic_news.tools.serpapi_tool import SerpApiTool
from src.epic_news.tools.tavily_tool import TavilyTool


class WebSearchFactory:
    """Factory for creating web search tools."""

    @staticmethod
    def create(provider: Literal["serpapi", "tavily"]) -> BaseTool:
        """Create a web search tool based on the provider."""
        if provider == "serpapi":
            return SerpApiTool()
        if provider == "tavily":
            return TavilyTool()
        raise ValueError(f"Unknown web search provider: {provider}")
