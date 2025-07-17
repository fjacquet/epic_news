"""Generic extractor module for unknown crew types.

This module provides a fallback extractor for crew types that don't have a specialized
extractor implementation.
"""

from typing import Any

from epic_news.utils.extractors.base_extractor import ContentExtractor


class GenericExtractor(ContentExtractor):
    """Generic extractor for unknown crew types."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract generic content data."""
        return {
            "content": state_data.get("final_report", ""),
            "topic": state_data.get("user_request", ""),
            "generation_date": state_data.get("current_date", ""),
        }
