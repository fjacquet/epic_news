"""Poem extractor module for POEM crew content.

This module provides the extractor for PoemCrew output to parse it into
a structured poem format.
"""

import json
from typing import Any

from epic_news.utils.extractors.base_extractor import ContentExtractor


class PoemExtractor(ContentExtractor):
    """Extractor for POEM crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract poem-specific data from PoemCrew output."""
        poem_obj = state_data.get("poem", {})
        poem_raw = poem_obj.get("raw", "{}")

        try:
            poem_data = json.loads(poem_raw)
        except (json.JSONDecodeError, TypeError):
            poem_data = {}

        return {
            "poem_title": poem_data.get("title", "Création Poétique"),
            "poem_content": poem_data.get("poem", ""),
            "theme": state_data.get("user_request", ""),
            "author": "Epic News AI",
        }
