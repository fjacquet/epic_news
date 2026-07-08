# Design: Migrate epic_news tools to the shared `crewai_custom_tools` package

**Date:** 2026-07-08
**Status:** Approved design — ready for implementation planning
**Predecessor:** `docs/superpowers/plans/2026-07-04-validate-implementation.md` (the pre-refactor test safety net this refactor depends on)

## Goal

Stop maintaining ~50 duplicated tool implementations inside `src/epic_news/tools/`. Source every **pure API-wrapper tool** (web, finance, OSINT, enterprise) from the shared, independently-tested `crewai-custom-tools` package instead, deleting the in-repo copies. epic_news keeps only the glue and the report-rendering tools that are coupled to its own models and federated HTML theme.

This is the "structural refactor" the `2026-07-04-validate-implementation` plan was written to protect.

## Decisions (locked)

| # | Decision | Choice |
|---|---|---|
| 1 | End state | **Full rip-and-replace** of pure-wrapper tool implementations: delete the files, import classes directly from the package at call sites. |
| 2 | Reporting + data-centric tools (Group 2) | **Keep epic_news's versions.** They are coupled to `epic_news.models` and the `utils/html` federated-theme pipeline; the package's own renderers differ. Carve them OUT of the migration. |
| 3 | Dependency form | **Git-pinned tag from day one:** `crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.2.0`. Reproducible in Docker/CI. (`v0.2.0` is tagged and pushed; verified.) |
| 4 | Sequencing | **Run + commit the validate-implementation safety net first**, then migrate. Characterization tests catch swap regressions. |

## Out of scope

- The `HolidayPlannerCrew` OpenRouter `APIError` ("Unable to get json response") — that is an LLM/output-parsing issue with `mistral-small-2603` on the final report task, unrelated to which tools are wired in. Tracked separately.
- Replacing Group 2 (reporting/data-centric) tools (Decision 2).
- Publishing `crewai-custom-tools` to PyPI (the git-pin makes this unnecessary for now).
- Adopting any of the package's ~37 net-new tools (Fear/Greed, GDELT, Sherlock, etc.) — additive follow-up, not this migration.

## Architecture

### The two tool groups (the central distinction)

**Group 1 — pure API-wrapper tools → REPLACE (delete file, import from package).**
Their output is only ever consumed by an LLM agent as text; no epic_news Python code parses a Group-1 tool's return value (verified: the only `._run()` call sites in `src/` are inside `email_search.py`, which is itself replaced). Therefore the package's `{success, data, error}` envelope is a **prompt-level** change (agents see different text), **not a code break**.

Group-1 inventory (40 exact-name matches + 1 rename = 41 tools; the other 9 of the package's 49 exact-name matches are Group 2, kept):

- **Web/search:** `PerplexitySearchTool`, `ScrapeNinjaTool`, `FirecrawlTool`, `BatchArticleScraperTool`, `WikipediaSearchTool`, `WikipediaArticleTool`, `WikipediaProcessingTool`, `RssFeedParserTool`, `OpmlParserTool`, `RSSFeedTool`, `UnifiedRssTool`, `GoogleFactCheckTool`, `GeoapifyPlacesTool`, `TechStackTool`, `BraveSearchTool`, `TavilyTool`, `SerpApiTool`, `HybridSearchTool`
- **Finance:** `YahooFinanceTickerInfoTool`, `YahooFinanceNewsTool`, `YahooFinanceCompanyInfoTool`, `YahooFinanceETFHoldingsTool`, `YahooFinanceHistoryTool`, `CoinMarketCapInfoTool`, `CoinMarketCapListTool`, `CoinMarketCapNewsTool`, `CoinMarketCapHistoricalTool`, `KrakenTickerInfoTool`, `KrakenAssetListTool`, `ExchangeRateTool`, and the **rename** `AlphaVantageCompanyOverviewTool → AlphaVantageOverviewTool`
- **OSINT/email:** `GitHubSearchTool`, `GitHubOrgSearchTool`, `HunterIOTool`, `SerperEmailSearchTool`, `DelegatingEmailSearchTool`
- **Enterprise:** `TodoistTool`, `AirtableReaderTool`, `AirtableTool`, `AccuWeatherTool`, `SaveToRagTool`
- **Drop:** `MyCustomTool` (`custom_tool.py`) — CrewAI scaffold stub, no equivalent, delete.

**Group 2 — reporting & data-centric tools → KEEP in epic_news.**
Coupled to epic_news internals: `render_report_tool.py` binds `epic_news.models.report_models.RenderReportToolSchema`; `data_centric_tools.py` binds `epic_news.models.data_metrics` and `_json_utils`. The package ships rewritten versions with different schemas and its own Jinja renderers that are **not** epic_news's federated `utils/html/` + `ui_theme` pipeline. Kept files: `render_report_tool.py`, `html_to_pdf_tool.py`, `universal_report_tool.py`, `reporting_tool.py`, `html_generator_tool.py`, `data_centric_tools.py`, `report_tools.py`, `utility_tools.py` (deprecated shim).

### What else stays in epic_news (the package does not own these)

- **Factory functions** (`get_*`) — most crews import factories, not raw classes. They also assemble **official `crewai_tools`** (`ScrapeWebsiteTool`, `YoutubeVideoSearchTool`, `WebsiteSearchTool`, `PDFSearchTool`, `GithubSearchTool`, `RagTool`) which the package does not provide. Factory bodies get rewritten to import Group-1 classes *from the package* while retaining the `crewai_tools` and config-selection pieces. Files: `web_tools.py`, `finance_tools.py`, `coinmarketcap_tool.py`, `location_tools.py`, `github_tools.py`, `rag_tools.py`, plus the factory portion of `email_search.py`.
- **Config-driven selectors:** `scraper_factory.py` (`get_scraper()` via `WEB_SCRAPER_PROVIDER`), `web_search_factory.py` (`WebSearchFactory`), `fact_checking_factory.py` (`FactCheckingToolsFactory`).
- **Infrastructure:** `_json_utils.py`, `cache_manager.py`, `search_base.py`, `github_base.py`, `email_base.py` (retained where still referenced; removed only if a delete makes them unused).

### Dependency integration

```toml
# epic_news/pyproject.toml
[project]
dependencies = [
  # ...
  "crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.2.0",
]
```

Add via `uv add`, then `uv sync --all-extras && uv pip install -e .`. Import form at all call sites is the **top-level** package only: `from crewai_custom_tools import PerplexitySearchTool`. A prefix-only rewrite that keeps epic_news's flat file stems (e.g. `crewai_custom_tools.tools.perplexity_search_tool`) will `ModuleNotFoundError` — the package's real modules are nested by domain.

## Migration phases (sequenced to keep the suite green)

**Phase 0 — Safety net + dependency.** Execute and commit the `2026-07-04-validate-implementation` plan to a green suite. Add the git-pinned `crewai-custom-tools` dependency; smoke-test `python -c "import crewai_custom_tools"` and that a sample class instantiates.

**Phase 1 — Repoint Group-1 imports.** At every call site (src + tests), rewrite `from epic_news.tools.<file> import <Class>` → `from crewai_custom_tools import <Class>`. Apply the `AlphaVantageCompanyOverviewTool → AlphaVantageOverviewTool` rename at imports **and** usages (incl. `finance_tools.get_stock_research_tools`). Remove `MyCustomTool` references.

**Phase 2 — Rewrite factory bodies.** Point `web_tools.py`, `finance_tools.py`, `coinmarketcap_tool.py`, `location_tools.py`, `github_tools.py`, `rag_tools.py`, and `email_search.py`'s factory at package classes; keep official `crewai_tools` + selector logic. Keep public factory signatures identical so crew call sites are untouched.

**Phase 3 — Delete orphaned Group-1 files + tests.** Remove the ~45 replaced tool implementation files and any tests that tested epic_news-internal behavior of those implementations (the package owns that testing now). Prune now-unused infra modules only if genuinely unreferenced. Run `uv run pytest -q`, `uv run mypy src/epic_news`, `uv run ruff check`.

**Phase 4 — Contract + prompt reconciliation.** Scope the JSON-contract ratchet test (from validate-implementation Task 7) to **epic_news-owned** tools only (Group 2 + infra), not package tools. Scan agent `tasks.yaml`/`agents.yaml` descriptions for any that describe old tool output shape and update wording to the `{success, data, error}` envelope where an agent is instructed to read a tool's raw result.

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Module-layout mismatch breaks imports | High if naive | Rewrite to **top-level** `from crewai_custom_tools import X` only; lint for `crewai_custom_tools.tools.*` deep imports. |
| The one rename (`AlphaVantage…`) missed at a usage site | Medium | Grep both symbol and all `AlphaVantageCompanyOverviewTool(` calls; type-check catches the rest. |
| Envelope change confuses an agent that reads raw tool text | Low | Phase 4 prompt scan; characterization/e2e tests from the safety net catch behavioral drift. |
| A package tool's behavior differs from epic_news's despite name match | Low–Med | Trust exact-name matches but rely on Phase 0–3 test suite; spot-check high-traffic tools (Perplexity, scraper, Yahoo) against a live/mocked call. |
| Git-pin unavailable offline / in CI without network | Low | `uv.lock` pins the resolved commit; document the tag. |

## Testing & verification

- Full `uv run pytest -q` green after Phase 1, 2, and 3 (incremental, never a big-bang red).
- `uv run mypy src/epic_news` clean (catches missed renames / dangling imports).
- The mocked e2e flow test (`tests/flows/test_reception_flow_e2e.py`, from the safety net) must still pass — proves routing → parsing → HTML rendering → email gating unchanged.
- Manual smoke: `crewai flow kickoff` on one crew per domain (a search crew, a finance crew) to confirm tools resolve and run.

## Rollback

Each phase is an isolated commit. Reverting the dependency line + the phase commits restores the in-repo tools. The git-pin means no local-path state to clean up.
