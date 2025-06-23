"""A tool for searching Wikipedia."""

import json

import wikipedia
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WikipediaSearchToolInput(BaseModel):
    """Input model for the WikipediaSearchTool."""

    query: str = Field(..., description="The search query for Wikipedia.")
    limit: int = Field(default=5, description="The maximum number of results to return.")


class WikipediaSearchTool(BaseTool):
    """A tool to search for articles on Wikipedia."""

    name: str = "Wikipedia Search"
    description: str = "Searches Wikipedia for articles matching a query and returns a list of titles."
    args_schema: type[BaseModel] = WikipediaSearchToolInput

    def _run(self, query: str, limit: int = 5) -> str:
        """Run the Wikipedia search tool."""
        try:
            results = wikipedia.search(query, results=limit)
            return json.dumps(results)
        except Exception as e:
            return f"An error occurred while searching Wikipedia: {e}"
