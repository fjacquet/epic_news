"""Perplexity AI-powered search tool."""

import json
import os
from typing import Any

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


class PerplexitySearchInput(BaseModel):
    """Input schema for Perplexity Search Tool."""

    query: str = Field(..., description="The search query")
    focus: str = Field("internet", description="Search focus: internet, academic, news, reddit")
    recency: str = Field("week", description="Recency filter: day, week, month")


class PerplexitySearchTool(BaseTool):
    """AI-powered web search with synthesis and citations."""

    name: str = "perplexity_search"
    description: str = (
        "AI-powered web search using Perplexity API. Returns synthesized answers "
        "with citations. Supports focus modes: internet, academic, news, reddit. "
        "Best for OSINT queries requiring analysis and synthesis."
    )
    args_schema: type[BaseModel] = PerplexitySearchInput
    api_key: str | None = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Perplexity search tool."""
        super().__init__(**kwargs)
        api_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.api_key = api_key if api_key else None
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not set")

    def _run(self, query: str, focus: str = "internet", recency: str = "week") -> str:
        """
        Execute Perplexity search.

        Args:
            query: The search query
            focus: Search focus (internet, academic, news, reddit)
            recency: Recency filter (day, week, month)

        Returns:
            JSON string with search results
        """
        if not self.api_key:
            return json.dumps({"error": "PERPLEXITY_API_KEY not configured", "success": False})

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}],
                    "search_recency_filter": recency,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            return json.dumps(
                {
                    "success": True,
                    "answer": data["choices"][0]["message"]["content"],
                    "citations": data.get("citations", []),
                    "source": "perplexity",
                }
            )

        except requests.exceptions.RequestException as e:
            logger.error("Perplexity API error: {}", str(e))
            return json.dumps({"error": str(e), "success": False, "fallback_needed": True})
