# Design: Migrate epic_news tools to the shared `crewai_custom_tools` package

**Date:** 2026-07-08
**Status:** Approved design (revised after 5-domain behavioral-parity audit) — ready for implementation planning
**Predecessor:** `docs/superpowers/plans/2026-07-04-validate-implementation.md` (the pre-refactor test safety net this refactor depends on)

## Goal

Stop maintaining ~40 duplicated tool implementations inside `src/epic_news/tools/`. Source every **pure API-wrapper tool** (web, finance, OSINT, enterprise) from the shared, independently-tested `crewai-custom-tools` package instead, deleting the in-repo copies. epic_news keeps only the glue (factories/selectors/infra) and the report-rendering tools that are coupled to its own models and federated HTML theme.

## Decisions (locked)

| # | Decision | Choice |
|---|---|---|
| 1 | End state | **Full rip-and-replace** of Group-1 tool implementations: delete the files, import classes directly from the package. |
| 2 | Reporting + data-centric tools (Group 2) | **Keep epic_news's versions.** Coupled to `epic_news.models` + the `utils/html` federated-theme pipeline (TemplateManager + ~20 renderers + `ui_theme`), which is epic_news product identity, not a generic tool. Out of scope for the package. |
| 3 | Dependency form | **Git-pinned tag:** `crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@<tag>`. Reproducible in Docker/CI. Bumped to the new tag (below) after the upstream fixes. |
| 4 | Sequencing | **Safety net first**, then **upstream fixes**, then epic_news migration. |
| 5 | Tier-C regressions | **Upstream-fix the package to a true superset, re-release, then migrate 100% of Group 1.** No permanent Group-1 tool left in epic_news. |

## The behavioral-parity audit (why this design is not a naive find-replace)

`crewai_custom_tools` v0.2.0 is a **simplifying rewrite** of epic_news's tools, not a faithful port. A 5-domain read-both-implementations audit classified all 41 Group-1 tools:

- **Tier A — true drop-in** (~14): identical `name`, `args_schema`, and inner data keys; only the harmless `{success,data,error}` envelope wraps the payload. Perplexity, Tavily, Geoapify, WikipediaSearch, RssFeedParser, Yahoo Ticker/News/CompanyInfo/History, CoinMarketCapInfo, Airtable (reader+writer), AccuWeather, HunterIO.
- **Tier B — swap + minor, agent-transparent reconciliation** (~24): a `name` rename, a dropped/renamed data key, or a cache removal — none of which break agent invocation (the agent calls the tool's live `name` from its runtime tool list and reads output as text). Accept and update the two prose prompts + delete the old tool tests. Includes: SerpApi (drops `page`), TechStack (`detailed_analysis→by_category`), GoogleFactCheck, WikipediaProcessing, OpmlParser, RSSFeedTool (per-article key renames), WikipediaArticle (drops unused `get_links`/`get_related_topics`), CMC List/News/Historical, ExchangeRate (string→JSON), Kraken ×2 (cache dropped), YahooETFHoldings (drops `shares`; actually a fix), GitHubSearch/OrgSearch, SerperEmailSearch (list→object), DelegatingEmailSearch, Todoist (name), Brave (arg renames `search_query→query`,`n_results→count`), AlphaVantage (name + curated output + cache).
- **Tier C — genuine regression / contract break** (3): handled per Decision 5 (upstream fix or drop). See below.

**YAGNI check on the borderline losses** — verified against actual epic_news usage, all UNUSED, so they need **no** upstream work: ScrapeNinja's 9 advanced params (never passed), HybridSearch's `country`/`n_results`/`prefer_brave` (never passed), AlphaVantage raw fields (no consumer reads `MarketCapitalization`/`EPS`/`PERatio`), WikipediaArticle `get_links`/`get_related_topics` (no prompt uses them), CMC `cover_image_url`/`percent_change_24h` (no renderer consumes them). Brave's arg renames matter only at the schema level and are agent-transparent.

### Tier C — resolution

| Tool | Finding | Resolution |
|---|---|---|
| **BatchArticleScraperTool** | Input contract changed (`rss_feeds`→`urls`), BUT used **only by its own test** — dead code in src. | **Drop** the tool + its test. No upstream, no wiring. |
| **SaveToRagTool** | Package class dropped `__init__(rag_tool=...)`; instantiates a bare default `RagTool()` in `_run` → writes to the wrong chromadb collection/embeddings → save→retrieve silently returns nothing. Used by `get_rag_tools()` → crews. | **Upstream:** add optional `rag_tool` constructor injection (`__init__(rag_tool=None)`, `_run` uses `self._rag_tool or RagTool()`). epic_news keeps its own `rag_config` + retrieval `RagTool` + `get_rag_tools(collection_suffix)`; only the class moves. |
| **UnifiedRssTool** | Package version dropped content-scraping, the saved `RssFeeds` JSON **output file**, invalid-source tracking, and the `output_file_path` arg. Invoked **programmatically** by `utils/rss_utils.py` as `._run(opml_file_path, days, output_file_path)` (from `main.py:111`); the real output is the written file. | **Upstream:** restore the `(opml_file_path, days, output_file_path)` `_run` signature + JSON-file writing + article content-scraping + invalid-source tracking (reusing the package's own scraper tools; keep it pure-Python-friendly per the package's Universal-Monolith ADR). |

## Out of scope

- The `HolidayPlannerCrew` OpenRouter `APIError` ("Unable to get json response") — an LLM/output-parsing issue with `mistral-small-2603`, unrelated to tools.
- Group 2 (reporting/data-centric) tools (Decision 2).
- Adopting the package's ~37 net-new tools (Fear/Greed, GDELT, Sherlock, …) — additive follow-up.
- Restoring the YAGNI-verified unused features listed above.

## Architecture

### Two workstreams

**Workstream 1 — `crewai_custom_tools` repo (blocking prerequisite).** Make the package a true superset for epic_news's needs, then release a new tag.
- W1.1 `SaveToRagTool`: optional `rag_tool` constructor injection.
- W1.2 `UnifiedRssTool`: restore output-file writing + `(opml, days, output_file_path)` signature + content-scraping + invalid-source tracking.
- W1.3 Version bump → **v0.3.0**, CHANGELOG, tag + push (its CI/Docker publishes on tag).

**Workstream 2 — `epic_news` repo (after v0.3.0).** The rip-and-replace.

### What stays in epic_news (the package does not own these)

- **Factory functions** (`get_*`) — most crews import factories, not raw classes; they also assemble official `crewai_tools` (`ScrapeWebsiteTool`, `YoutubeVideoSearchTool`, `WebsiteSearchTool`, `PDFSearchTool`, `GithubSearchTool`, `RagTool`) which the package does not provide. Factory bodies get rewritten to import Group-1 classes from the package while retaining the `crewai_tools` and config-selection pieces. Files: `web_tools.py`, `finance_tools.py`, `coinmarketcap_tool.py`, `location_tools.py`, `github_tools.py`, `rag_tools.py` (injects epic_news's configured `RagTool` into the package `SaveToRagTool`), and `email_search.py`'s `get_email_search_tools()`.
- **Config-driven selectors:** `scraper_factory.py` (`WEB_SCRAPER_PROVIDER`), `web_search_factory.py`, `fact_checking_factory.py`.
- **RAG config:** `rag_config.py` (`build_rag_tool_kwargs`, chromadb collection, `text-embedding-3-large`, `summarize`).
- **Group 2 reporting/data-centric tools** + the entire `utils/html/` rendering pipeline.
- **Infrastructure** still referenced after deletions: `_json_utils.py`, `cache_manager.py` (only where kept tools use it), `search_base.py`, `github_base.py`, `email_base.py` — removed only if a delete leaves them genuinely unused.

### Dependency integration

```toml
# epic_news/pyproject.toml
[project]
dependencies = [
  "crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.3.0",
]
```

Import form at all call sites is the **top-level** package only: `from crewai_custom_tools import PerplexitySearchTool`. A prefix-only rewrite that keeps epic_news's flat file stems will `ModuleNotFoundError` — the package's real modules are nested by domain.

## Migration phases

**Phase 0 — Safety net.** Execute and commit `2026-07-04-validate-implementation` to a green suite. (Scope its tool JSON-contract ratchet to epic_news-owned tools only — see Phase 4.)

**Phase 1 — Upstream fixes (Workstream 1).** Implement W1.1/W1.2 in `crewai_custom_tools` with tests; release v0.3.0. Smoke-verify from epic_news: `python -c "import crewai_custom_tools"` and that `SaveToRagTool(rag_tool=...)` and `UnifiedRssTool()._run(opml, days, out)` behave as epic_news expects.

**Phase 2 — Add dependency + repoint imports.** Pin `@v0.3.0`; `uv sync --all-extras && uv pip install -e .`. Rewrite Group-1 class imports at all call sites (src + tests) → `from crewai_custom_tools import X`. Apply `AlphaVantageCompanyOverviewTool → AlphaVantageOverviewTool` at imports **and** usages (incl. `finance_tools.get_stock_research_tools`). Update the two prose prompts referencing tool names (`shopping_advisor`, `deep_research` YAML). Remove `MyCustomTool`.

**Phase 3 — Rewrite factory bodies.** Point `web_tools.py`, `finance_tools.py`, `coinmarketcap_tool.py`, `location_tools.py`, `github_tools.py`, `rag_tools.py`, `email_search.py` factories at package classes; keep official `crewai_tools` + selector logic; keep factory signatures identical so crew call sites are untouched. `rag_tools.get_rag_tools` injects the configured `RagTool` into the package `SaveToRagTool`.

**Phase 4 — Delete orphans + reconcile.** Delete the ~40 replaced Group-1 tool files, the dead `batch_article_scraper_tool.py`, and the tool tests that assert epic_news-internal behavior/names (the package owns that testing now). Scope the JSON-contract ratchet to epic_news-owned tools. Prune now-unused infra. Run `uv run pytest -q`, `uv run mypy src/epic_news`, `uv run ruff check`.

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Upstream v0.3.0 fixes don't match epic_news's exact contract (UnifiedRss file/signature, SaveToRag injection) | Med | Phase 1 smoke-verify against `rss_utils.py` and `rag_tools.py` before proceeding; the two are the only programmatic tool-output consumers. |
| Module-layout mismatch breaks imports | High if naive | Rewrite to **top-level** `from crewai_custom_tools import X`; lint for deep `crewai_custom_tools.tools.*` imports. |
| The AlphaVantage rename missed at a usage site | Med | Grep the symbol + all `AlphaVantageCompanyOverviewTool(` calls; mypy catches the rest. |
| An agent-transparent Tier-B change (name/key) surprises a crew | Low | Characterization + mocked-e2e tests from the safety net; the two prose-prompt updates. |
| Cache removal (Kraken/AlphaVantage) raises live-API/rate-limit exposure | Low | Accept; these are read-mostly and rate limits are generous. Revisit if 429s appear. |

## Testing & verification

- Package (Workstream 1): the package's own pytest suite green for the two modified tools; new tests for `rag_tool` injection and UnifiedRss file output.
- epic_news: full `uv run pytest -q` green after Phases 2, 3, 4 (incremental, never big-bang red); `uv run mypy src/epic_news` clean; the mocked e2e flow test (`tests/flows/test_reception_flow_e2e.py`) still passes.
- Manual smoke: `crewai flow kickoff` on one crew per domain (a search crew, a finance crew, the RSS/news path) to confirm tools resolve and the RSS output file is still written.

## Rollback

Workstream 1 is a separate repo/release — epic_news pins the tag, so reverting the pin restores prior behavior. Each epic_news phase is an isolated commit; reverting the dependency line + phase commits restores the in-repo tools.
