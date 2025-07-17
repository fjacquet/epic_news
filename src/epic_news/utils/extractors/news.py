"""News extractor module for NEWS crew content.

This module provides the extractor for NewsCrew output to parse it into
a structured news format.
"""

from typing import Any

from epic_news.utils.extractors.base_extractor import ContentExtractor


class NewsExtractor(ContentExtractor):
    """Extractor for news-related content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract news-specific data."""
        return {
            "articles": state_data.get("articles", []),
            "summary": state_data.get("summary", ""),
            "main_topic": state_data.get("main_topic", ""),
        }
