import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel
from tavily import TavilyClient

from src.epic_news.models.tavily_models import TavilyToolInput


class TavilyTool(BaseTool):
    name: str = "tavily_search"
    description: str = (
        "A tool for performing web searches using the Tavily API. "
        "It returns a concise summary of search results for a given query."
    )
    args_schema: Type[BaseModel] = TavilyToolInput

    def _run(self, query: str) -> str:
        """Run the Tavily search tool with the specified query."""
        try:
            api_key = os.getenv('TAVILY_API_KEY')
            if not api_key:
                raise ValueError("TAVILY_API_KEY environment variable not set.")

            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, search_depth="basic")
            return response['results']
        except Exception as e:
            return f"Error performing search with Tavily: {e}"
