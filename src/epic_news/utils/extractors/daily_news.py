"""Daily news extractor module for NEWS_DAILY crew content.

This module provides the extractor for NewsDailyCrew output to parse it into
a structured news report format.
"""

import json
from typing import Any

from loguru import logger

from epic_news.utils.extractors.base_extractor import ContentExtractor


class NewsDailyExtractor(ContentExtractor):
    """Extractor for daily news reports with structured content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract news daily report data using structured format."""
        logger.debug("🔍 DEBUG NEWS_DAILY extraction:")

        # Check for news_daily_model in state_data
        news_daily_report = state_data.get("news_daily_model")
        logger.debug(f"  news_daily_model type: {type(news_daily_report)}")

        if news_daily_report is None:
            # Try to find news daily report in raw data
            news_daily_data = state_data.get("news_daily_report", {})
            news_raw = news_daily_data.get("raw", "{}")
            logger.debug(f"  news_raw (first 200 chars): {str(news_raw)[:200]}...")

            try:
                # Try to parse as JSON
                news_data = json.loads(news_raw) if isinstance(news_raw, str) else news_raw

                logger.debug("  ✅ News data parsed from raw data")
                return news_data
            except Exception as e:
                logger.error(f"  ❌ Failed to parse news data from raw: {e}")
                return {"error": f"Failed to parse news report data: {e}"}
        elif isinstance(news_daily_report, dict):
            # Handle case where news_daily_report is already a dict
            logger.debug("  ✅ News data extracted from dict")
            return news_daily_report
        else:
            # Handle Pydantic model case
            try:
                if hasattr(news_daily_report, "model_dump"):
                    result = news_daily_report.model_dump()
                else:
                    result = dict(news_daily_report)
                logger.debug("  ✅ News data extracted from model")
                return result
            except Exception as e:
                logger.error(f"  ❌ Failed to extract news data: {e}")
                return {"error": f"Failed to extract news data: {e}"}
