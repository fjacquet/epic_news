"""Compatibility shim for legacy content extractor imports.

This module preserves backwards compatibility for tests and code that import
`epic_news.utils.content_extractors` by re-exporting the new extractor factory
and specific extractor/models under the legacy module path.

It delegates to `epic_news.utils.extractors.factory.ContentExtractorFactory`
while normalizing crew type names (e.g. "RSS_WEEKLY" -> "RSSWEEKLY").
"""

from __future__ import annotations

from typing import Any

from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.utils.extractors.factory import ContentExtractorFactory as _NewFactory
from epic_news.utils.extractors.rss_weekly import RssWeeklyExtractor

__all__ = [
    "ContentExtractorFactory",
    "RssWeeklyExtractor",
    "RssWeeklyReport",
]


def _normalize_crew_type(crew_type: str) -> str:
    """Normalize crew type to match keys used by the new factory.

    Examples:
    - "RSS_WEEKLY" -> "RSSWEEKLY"
    - "DEEP_RESEARCH" -> "DEEPRESEARCH"
    """
    return crew_type.upper().replace("_", "").replace("-", "")


class ContentExtractorFactory:
    """Legacy-compatible facade over the new extractor factory.

    Provides the same API used in older tests/modules but delegates the work to
    the modern factory, ensuring crew type normalization for lookups.
    """

    @classmethod
    def get_extractor(cls, crew_type: str):
        normalized = _normalize_crew_type(crew_type)
        return _NewFactory.get_extractor(normalized)

    @classmethod
    def extract_content(cls, state_data: dict[str, Any], crew_type: str) -> dict[str, Any]:
        normalized = _normalize_crew_type(crew_type)
        return _NewFactory.extract_content(state_data, normalized)
