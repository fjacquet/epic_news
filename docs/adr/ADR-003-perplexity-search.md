# ADR-003: Migration from SerperDev to Perplexity Search

## Status

Accepted

## Context

The project used `SerperDevTool` from `crewai_tools` as its primary web search provider. SerperDev wraps Google Search API and returns raw link lists that agents must then scrape and synthesize. Perplexity provides AI-synthesized answers with citations, reducing agent workload and improving result quality.

## Decision

- Replace `SerperDevTool` with custom `PerplexitySearchTool` (`epic_news.tools.perplexity_search_tool`) as the primary search provider
- Update `web_tools.py` factory functions (`get_search_tools()`, `get_news_tools()`) to return `PerplexitySearchTool`
- Add `"perplexity"` as first option in `WebSearchFactory` with cascading fallback (Perplexity → Brave → Serper)
- Keep `SERPER_API_KEY` as optional fallback in `.env`

## Consequences

- Better search quality: Perplexity returns synthesized answers, not just links
- Reduced token usage: agents spend fewer iterations scraping and summarizing raw results
- Requires `PERPLEXITY_API_KEY` in `.env` (small per-query cost)
- SerperDev remains available as fallback via `HybridSearchTool` cascading chain
- All crews using web search benefit without individual changes
