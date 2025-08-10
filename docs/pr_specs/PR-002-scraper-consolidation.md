# PR-002: Web Scraping Consolidation – ScrapeNinja Default via Factory

## Summary

Consolidate website scraping to a single, configurable entry point. Default to `ScrapeNinjaTool` and deprecate direct Firecrawl usage. Provide a `ScraperFactory` to select provider via env var without coupling crews to a specific vendor. A Firecrawl adapter exists but is optional (requires `firecrawl-py` and `FIRECRAWL_API_KEY`).

## Motivation

- The repo uses ScrapeNinja broadly while some configs still reference Firecrawl (e.g., `FIRECRAWL_SEARCH`, holiday planner docs).
- A factory avoids hard-coded dependencies, keeps code DRY, and supports controlled provider switching.

## Scope

- Add `ScraperFactory` returning the scraper tool based on `WEB_SCRAPER_PROVIDER` env var (`scrapeninja` default, `firecrawl` optional).
- Replace direct imports/usages with the factory in tools and crews.
- Remove Composio Firecrawl action usage from `company_news_crew.py` and docs; recommend ScrapeNinja.

## Non-Goals

- Removing any third-party packages.
- Rewriting scraping logic beyond selection.

## Detailed Changes

- Add: `src/epic_news/tools/scraper_factory.py`
  - `def get_scraper()` reads env; returns `ScrapeNinjaTool()` by default; supports `FirecrawlTool()` when `WEB_SCRAPER_PROVIDER=firecrawl` and optional deps are installed.
- Modify usages:
  - `src/epic_news/tools/unified_rss_tool.py` and `src/epic_news/tools/batch_article_scraper_tool.py`: replace `ScrapeNinjaTool()` with `get_scraper()`.
  - `src/epic_news/tools/web_tools.py`: expose `get_scraper()` in `get_web_tools()` lineup.
  - `src/epic_news/crews/company_news/company_news_crew.py`: remove `"FIRECRAWL_SEARCH"` from actions; use `get_scraper()` where scraping is needed.
  - YAML notes in `crews/holiday_planner/config/agents.yaml`: update copy to reference ScrapeNinja as canonical scraper.

## Files Touched

- Add: `src/epic_news/tools/scraper_factory.py`
- Modify: `src/epic_news/tools/unified_rss_tool.py`
- Modify: `src/epic_news/tools/batch_article_scraper_tool.py`
- Modify: `src/epic_news/tools/web_tools.py`
- Modify: `src/epic_news/crews/company_news/company_news_crew.py`
- Docs: `docs/3_ARCHITECTURAL_PATTERNS.md` and `docs/2_TOOLS_HANDBOOK.md` sections about scraping; remove Firecrawl references in narratives.

## Compatibility & Migration

- Default behavior remains ScrapeNinja. If a user requires Firecrawl, install `firecrawl-py`, set `FIRECRAWL_API_KEY`, and set `WEB_SCRAPER_PROVIDER=firecrawl`.

## Configuration

- **Provider selection**: Controlled via `WEB_SCRAPER_PROVIDER` in `.env`. Supported values: `scrapeninja` (default), `firecrawl`.
- **Required API keys**:
  - `RAPIDAPI_KEY` for ScrapeNinja
  - `FIRECRAWL_API_KEY` for Firecrawl

Example `.env`:

```bash
# Scraper provider (default is scrapeninja)
WEB_SCRAPER_PROVIDER=scrapeninja

# API keys
RAPIDAPI_KEY=your-rapidapi-key
FIRECRAWL_API_KEY=your-firecrawl-key
```

Example usage:

```python
from epic_news.tools.scraper_factory import get_scraper

scraper = get_scraper()  # respects WEB_SCRAPER_PROVIDER
content_json = scraper.run({"url": "https://example.com"})
```

## Testing Strategy

- Unit test `get_scraper()` default and env override. See `tests/tools/test_scraper_factory.py`.
- Integration test with `unified_rss_tool.py` exercising fallback to scraper.
- Grep check that no direct `ScrapeNinjaTool()` instantiation remains outside the factory.

## Rollout Plan

- Land factory and replace usages.
- Validate FinDaily, CompanyNews, and WebPresence crews scrape successfully.

## Risks & Mitigations

- Risk: Missed direct instantiation. Mitigation: grep and CI check.
- Risk: Behavior differences across providers. Mitigation: keep consistent interface and document.

## Documentation

- Update `README.md` Advanced Usage to mention ScraperFactory and ScrapeNinja default.
- Update `docs/2_TOOLS_HANDBOOK.md` (Scraping section) and `docs/3_ARCHITECTURAL_PATTERNS.md` (tool factories, provider toggles).
