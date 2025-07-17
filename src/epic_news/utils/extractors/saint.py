"""Saint extractor module for SAINT crew content.

This module provides the extractor for SaintCrew output to parse it into
a structured SaintData model.
"""

from typing import Any

from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.utils.extractors.base_extractor import ContentExtractor


class SaintExtractor(ContentExtractor):
    """Extractor for SAINT crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract saint-specific data using Pydantic model."""

        saint_obj = state_data.get("saint_daily_report", {})
        saint_raw = saint_obj.get("raw", "{}")

        # Use Pydantic model to parse and validate the saint data
        saint_model = SaintData.from_json_string(saint_raw)
        return saint_model.to_template_data()
