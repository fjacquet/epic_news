"""RSS Weekly extractor module for RSS_WEEKLY crew content.

This module provides the extractor for RssWeeklyCrew output to parse it into
a structured RssWeeklyReport model.
"""

import json
from typing import Any

from loguru import logger

from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.utils.extractors.base_extractor import ContentExtractor


class RssWeeklyExtractor(ContentExtractor):
    """Extractor for RSS_WEEKLY crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract RSS weekly report data using RssWeeklyReport Pydantic model."""
        try:
            # Get the RSS weekly crew output
            rss_weekly_output = state_data.get("rss_weekly_report", {})

            if hasattr(rss_weekly_output, "raw"):
                # Parse raw JSON output from crew
                try:
                    raw_data = json.loads(rss_weekly_output.raw)
                    rss_model = RssWeeklyReport.model_validate(raw_data)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"❌ Error parsing RSS weekly raw output: {e}")
                    # Create minimal model with error info
                    rss_model = RssWeeklyReport(  # type: ignore[call-arg]
                        title="Erreur de Parsing RSS Weekly",
                        summary=f"Erreur lors du parsing des données: {str(e)}",
                    )
            elif isinstance(rss_weekly_output, dict):
                # Direct dictionary data
                rss_model = RssWeeklyReport.model_validate(rss_weekly_output)
            else:
                # Fallback: create empty model
                rss_model = RssWeeklyReport(  # type: ignore[call-arg]
                    title="Résumé Hebdomadaire des Flux RSS", summary="Aucune donnée RSS disponible"
                )

            # Return the model as a dictionary for TemplateManager compatibility
            return rss_model.model_dump()

        except Exception as e:
            logger.error(f"❌ Error in RssWeeklyExtractor: {e}")
            # Return minimal error data
            return {
                "title": "Erreur RSS Weekly",
                "summary": f"Erreur lors de l'extraction: {str(e)}",
                "feeds": [],
                "total_feeds": 0,
                "total_articles": 0,
                "error": str(e),
            }
