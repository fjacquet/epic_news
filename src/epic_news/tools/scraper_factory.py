"""
Scraper Factory for epic_news

Provides a single entry point to obtain a web scraper tool instance based on
configuration. Defaults to ScrapeNinja.

Env var:
- WEB_SCRAPER_PROVIDER: 'scrapeninja' (default). Supports 'firecrawl'.
  'composio' and 'tavily' are not scraping providers in this codebase and will raise
  clear guidance errors.
"""

from __future__ import annotations

import os
from typing import Any

from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool


def get_scraper() -> Any:
    """
    Return a scraper tool instance based on the WEB_SCRAPER_PROVIDER env var.

    Defaults to ScrapeNinjaTool. Unsupported providers raise a clear error.
    """
    provider = os.getenv("WEB_SCRAPER_PROVIDER", "scrapeninja").strip().lower()

    if provider in ("", "scrapeninja", "scrape_ninja", "ninja"):
        return ScrapeNinjaTool()

    if provider == "firecrawl":
        # Lazy import to avoid requiring Firecrawl SDK when not used
        from epic_news.tools.firecrawl_tool import FirecrawlTool

        return FirecrawlTool()

    if provider == "composio":
        # No dedicated Composio scraping adapter exists in the project.
        # Composio is currently used for search/actions (e.g., company_news crew).
        raise NotImplementedError(
            "'composio' is not a scraping provider here. Use WEB_SCRAPER_PROVIDER=scrapeninja or firecrawl."
        )

    if provider == "tavily":
        # Tavily is a SEARCH provider, not a page scraper. See WebSearchFactory.
        raise ValueError(
            "'tavily' is a search provider, not a scraper. Use WebSearchFactory for search tools, "
            "or set WEB_SCRAPER_PROVIDER to 'scrapeninja' or 'firecrawl'."
        )

    raise ValueError(f"Unsupported WEB_SCRAPER_PROVIDER='{provider}'. Supported: 'scrapeninja', 'firecrawl'.")


__all__ = ["get_scraper"]
