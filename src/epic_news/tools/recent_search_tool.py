"""Web search restricted to the last 12 months (Perplexity ``search_recency="year"``).

``HybridSearchTool`` exposes only ``query`` and applies no recency filter, so research
agents keep citing 2023-2024 sources. This tool is the "current facts" search; keep
``hybrid_search`` as the fallback for background and for when this one fails.
"""

import json

from crewai.tools import BaseTool
from crewai_custom_tools import PerplexitySearchTool
from pydantic import BaseModel, Field

from epic_news.tools._json_utils import ensure_json_str

_FALLBACK = "use hybrid_search instead"


class RecentSearchInput(BaseModel):
    query: str = Field(..., description="What to search for; include the topic and the geography.")


class RecentSearchTool(BaseTool):
    """Perplexity web search limited to results published in the last 12 months."""

    name: str = "recent_search"
    description: str = (
        "Web search returning only results from the last 12 months, with citations. "
        "Use it first for current facts, news and recent developments."
    )
    args_schema: type[BaseModel] = RecentSearchInput

    def _run(self, query: str) -> str:
        try:
            result = ensure_json_str(PerplexitySearchTool()._run(query, search_recency="year"))
        except ValueError as exc:  # no API key
            return ensure_json_str({"error": f"recent_search unavailable ({exc}); {_FALLBACK}"})
        except Exception as exc:  # noqa: BLE001 - surface search failures to the agent as data
            return ensure_json_str({"error": f"recent_search failed ({exc}); {_FALLBACK}"})
        try:
            payload = json.loads(result)
        except ValueError:
            payload = None
        if isinstance(payload, dict) and payload.get("error"):
            return ensure_json_str({"error": f"recent_search failed ({payload['error']}); {_FALLBACK}"})
        return result
