"""crewai_tools' ScrapeWebsiteTool with a size cap and a JSON result.

The upstream tool returns the whole page text; one large page can fill the agent's
context window. ScrapeNinja already caps at 20k characters; this keeps the backup
scraper in line (SCRAPE_MAX_CHARS, default 12000).
"""

import os
from typing import Any

from crewai_tools import ScrapeWebsiteTool

from epic_news.tools._json_utils import ensure_json_str

DEFAULT_MAX_CHARS = 12_000


def _max_chars() -> int:
    try:
        return max(1, int(os.getenv("SCRAPE_MAX_CHARS", str(DEFAULT_MAX_CHARS))))
    except ValueError:
        return DEFAULT_MAX_CHARS


class CappedScrapeWebsiteTool(ScrapeWebsiteTool):
    """Read a web page, return at most SCRAPE_MAX_CHARS characters as JSON."""

    def _run(self, **kwargs: Any) -> str:
        url = kwargs.get("website_url", self.website_url)
        try:
            text = str(super()._run(**kwargs))
        except Exception as exc:  # noqa: BLE001 - surface scrape failures to the agent as data
            return ensure_json_str({"url": url, "error": str(exc)})
        limit = _max_chars()
        return ensure_json_str({"url": url, "content": text[:limit], "truncated": len(text) > limit})
