# epic_news Tools Migration to crewai_custom_tools — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete epic_news's ~37 duplicated Group-1 tool implementations and source them from the shared `crewai-custom-tools` package (v0.3.0), keeping only the epic_news factories/selectors, report-rendering (Group-2) tools, and RAG config as thin glue.

**Architecture:** This is Workstream 2 of the design in `docs/superpowers/specs/2026-07-08-tools-migration-crewai-custom-tools-design.md`; it depends on Workstream 1 having released `crewai-custom-tools` v0.3.0 (SaveToRag `rag_tool=` injection + UnifiedRss file-writing restored). Each migrated tool class is imported at the **top level** (`from crewai_custom_tools import X`); the epic_news factory functions (`get_*`) are rewritten to import those classes while retaining the official `crewai_tools` pieces and config-selection logic, so every crew call site keeps working unchanged. Migration proceeds domain-by-domain (web → finance → osint/enterprise), each domain repointing importers, rewriting that domain's factories, then deleting the orphaned tool files — every task ends on a green `uv run pytest -q`.

**Tech Stack:** Python 3.13, uv, CrewAI, pytest + pytest-env, mypy, ruff.

## Global Constraints

- Package manager: `uv` only. Before any pytest run in a fresh session: `uv sync --all-extras && uv pip install -e .` (plain `uv sync` prunes test extras and pytest falls back to a global 3.12 install → wrong pytest).
- Git: stage files explicitly by path; never `git add -A`. Do **not** stage `.serena/project.yml` or `src/epic_news/main.py` (personal sentinel spots). Do **not** stage `uv.lock` unless a step explicitly says so (only Task 1 does, because adding a dependency requires it).
- All imports at top of files (never inside functions/methods) — the one pre-existing exception (`scraper_factory.py`'s lazy Firecrawl import) is preserved deliberately; see Task 2.
- Use Loguru (`from loguru import logger`), never stdlib `logging`, in `src/`.
- Python 3.13 union syntax (`X | None`, `X | Y`).
- Import migrated classes **only** at the top level: `from crewai_custom_tools import X`. Deep imports (`from crewai_custom_tools.tools.web import X`) will `ModuleNotFoundError` — the package's real modules are nested. Lint/grep for any deep `crewai_custom_tools.` import before each commit.
- Run `uv run ruff check --fix <changed files> && uv run ruff format <changed files>` before each commit (pre-commit hooks enforce this anyway).
- Every commit message ends with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Depends on **crewai-custom-tools v0.3.0** (Workstream 1). Do not start Task 2 until Task 1's smoke import confirms the v0.3.0 contract.

### Sequencing rationale (read once)

The design's Phase 2/3/4 split ("repoint imports", "rewrite factories", "delete orphans") cannot be executed as three separate green commits, because a factory that still imports a deleted tool file breaks the suite. To keep **every task green**, each domain task (2, 3, 4) does all three for its domain in one commit: (a) repoint that domain's direct importers, (b) rewrite that domain's factory/selector bodies to import from the package, (c) `git rm` the now-orphaned tool files. Task 5 is a cross-cutting factory signature-parity + import-hygiene audit (no code rewrite left to do — it verifies). Task 6 removes dead code, deletes the migrated tools' tests, updates prose prompts, prunes orphaned infra, and rescopes the JSON ratchet. Task 7 is final verification + manual smoke.

### Authoritative call-site map (from recon — use this, don't re-derive)

Direct importers of migrated tool classes in `src` (everything else is factory-internal or has no importer):

| Importer | Line | Symbol | Domain / Task |
|---|---|---|---|
| `crews/company_profiler/company_profiler_crew.py` | 10 | `HybridSearchTool` | web / T2 |
| `crews/deep_research/deep_research.py` | 12 | `HybridSearchTool` | web / T2 |
| `crews/geospatial_analysis/geospatial_analysis_crew.py` | 9 | `HybridSearchTool` | web / T2 |
| `crews/hr_intelligence/hr_intelligence_crew.py` | 9 | `HybridSearchTool` | web / T2 |
| `crews/legal_analysis/legal_analysis_crew.py` | 9 | `HybridSearchTool` | web / T2 |
| `crews/pestel/pestel_crew.py` | 17 | `HybridSearchTool` | web / T2 |
| `crews/sales_prospecting/sales_prospecting_crew.py` | 9 | `HybridSearchTool` | web / T2 |
| `crews/tech_stack/tech_stack_crew.py` | 10 | `HybridSearchTool` | web / T2 |
| `crews/web_presence/web_presence_crew.py` | 9 | `HybridSearchTool` | web / T2 |
| `crews/saint_daily/saint_daily.py` | 12-14 | `WikipediaArticleTool`, `WikipediaProcessingTool`, `WikipediaSearchTool` | web / T2 |
| `utils/rss_utils.py` | 3 | `UnifiedRssTool` | web / T2 |
| `tools/web_search_factory.py` | 6-8 | `PerplexitySearchTool`, `SerpApiTool`, `TavilyTool` | web / T2 |
| `tools/scraper_factory.py` | 18, 34 | `ScrapeNinjaTool`, `FirecrawlTool` | web / T2 |
| `tools/fact_checking_factory.py` | 3 | `GoogleFactCheckTool` (relative import) | web / T2 |
| `tools/web_tools.py` | 16 | `PerplexitySearchTool` | web / T2 |
| `tools/location_tools.py` | 10 | `GeoapifyPlacesTool` | web / T2 |
| `crews/holiday_planner/holiday_planner_crew.py` | 7 | `ExchangeRateTool` | finance / T3 |
| `crews/fin_daily/fin_daily.py` | 8 | `KrakenAssetListTool`, `KrakenTickerInfoTool` | finance / T3 |
| `tools/finance_tools.py` | 10-16 | Yahoo×5, Kraken, `AlphaVantageCompanyOverviewTool` | finance / T3 |
| `tools/coinmarketcap_tool.py` | 10-15 | CMC ×4 (relative imports) | finance / T3 |
| `tools/github_tools.py` | 8 | `GitHubSearchTool` (relative import) | osint / T4 |
| `tools/email_search.py` | 12-13 | `HunterIOTool`, `SerperEmailSearchTool` (relative) + `DelegatingEmailSearchTool` class defined here | osint / T4 |
| `tools/rag_tools.py` | 12 | `SaveToRagTool` | enterprise / T4 |

**Delete-only (no `src` importer — nothing to repoint, just `git rm`):** `brave_search_tool.py`, `tech_stack_tool.py`, `rss_feed_tool.py`, `rss_feed_parser_tool.py`, `opml_parser_tool.py`, `todoist_tool.py`, `accuweather_tool.py`, `github_org_tool.py`. (These package tools exist and are importable, but no epic_news code currently wires them — the audit's YAGNI finding. Migrating them here = delete the dead in-repo copy.)

**models/ note:** the deleted tools reference input schemas in `src/epic_news/models/` (`alpha_vantage_models`, `finance_models`, `airtable_models`, `accuweather_models`, `todoist_models`, `email_search_models`, etc.). Leaving these untouched is intentional — deleting model files is out of scope and some may become unreferenced; a later cruft sweep can address them. Do **not** delete any `models/` file in this plan.

---

### Task 1: Phase 0 — green safety net + add the v0.3.0 dependency

Get the pre-refactor safety net committed to a green suite, then add and smoke-test the package dependency. This is the only task that stages `uv.lock`.

**Files:**
- Execute (if not already done): `docs/superpowers/plans/2026-07-04-validate-implementation.md` (its 7 tasks / 6 commits).
- Modify: `pyproject.toml` (add dependency), `uv.lock` (regenerated — staged here only).

**Interfaces:**
- Produces: a green `uv run pytest -q` baseline; `from crewai_custom_tools import X` importable; verified v0.3.0 contract for `SaveToRagTool(rag_tool=...)` and `UnifiedRssTool._run(opml, days, output_file_path)`.

- [ ] **Step 1: Ensure the safety net is executed and green.** If the `2026-07-04-validate-implementation` plan has not been run, execute it now per its own instructions (it is self-contained). Then:
  ```bash
  uv sync --all-extras && uv pip install -e .
  uv run pytest -q
  ```
  Expected: all pass (~205+ tests). If red, STOP — the migration must start from green.

- [ ] **Step 2: Add the dependency to `pyproject.toml`.** In the `[project].dependencies` list (the "Core runtime" block near the top), insert after the `crewai-tools[mcp]` line:
  - Find: `    "crewai-tools[mcp]>=1.15.1",`
  - Replace with:
    ```toml
    "crewai-tools[mcp]>=1.15.1",
    "crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.3.0",
    ```

- [ ] **Step 3: Resolve + install + smoke-import.**
  ```bash
  uv sync --all-extras && uv pip install -e .
  python -c "from crewai_custom_tools import (PerplexitySearchTool, BraveSearchTool, TavilyTool, SerpApiTool, HybridSearchTool, ScrapeNinjaTool, FirecrawlTool, TechStackTool, GeoapifyPlacesTool, GoogleFactCheckTool, WikipediaSearchTool, WikipediaArticleTool, WikipediaProcessingTool, RssFeedParserTool, OpmlParserTool, RSSFeedTool, UnifiedRssTool, YahooFinanceTickerInfoTool, YahooFinanceNewsTool, YahooFinanceCompanyInfoTool, YahooFinanceETFHoldingsTool, YahooFinanceHistoryTool, CoinMarketCapInfoTool, CoinMarketCapListTool, CoinMarketCapNewsTool, CoinMarketCapHistoricalTool, KrakenTickerInfoTool, KrakenAssetListTool, ExchangeRateTool, GitHubSearchTool, GitHubOrgSearchTool, HunterIOTool, SerperEmailSearchTool, DelegatingEmailSearchTool, TodoistTool, AirtableReaderTool, AirtableTool, AccuWeatherTool, SaveToRagTool, AlphaVantageOverviewTool); print('all imports OK')"
  ```
  Expected: prints `all imports OK`. If any symbol is missing, STOP — v0.3.0 is not the expected superset; report the missing name (do not proceed on a wrong tag).

- [ ] **Step 4: Verify the two Tier-C v0.3.0 contracts (spec Risk row).**
  ```bash
  python -c "import inspect; from crewai_custom_tools import SaveToRagTool, UnifiedRssTool; print('SaveToRag init:', inspect.signature(SaveToRagTool.__init__)); print('UnifiedRss _run:', inspect.signature(UnifiedRssTool._run))"
  ```
  Expected: `SaveToRag init` includes a `rag_tool` parameter (default `None`); `UnifiedRss _run` accepts `opml_file_path`, `days`, and `output_file_path`. If either is absent, STOP — Workstream 1 did not land the fix.

- [ ] **Step 5: Lint + commit (stage `pyproject.toml` and `uv.lock` only).**
  ```bash
  uv run ruff check --fix pyproject.toml || true
  git add pyproject.toml uv.lock
  git commit -m "build(deps): add crewai-custom-tools v0.3.0 (tools migration Workstream 2)" \
             -m "Pins the git-tagged shared tool package; imports smoke-tested top-level. SaveToRag rag_tool= injection and UnifiedRss output-file signature verified." \
             -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  ```

---

### Task 2: Web domain — repoint importers, rewrite web factories/selectors, delete web tool files

**Files:**
- Repoint (imports only): `crews/company_profiler/company_profiler_crew.py`, `crews/deep_research/deep_research.py`, `crews/geospatial_analysis/geospatial_analysis_crew.py`, `crews/hr_intelligence/hr_intelligence_crew.py`, `crews/legal_analysis/legal_analysis_crew.py`, `crews/pestel/pestel_crew.py`, `crews/sales_prospecting/sales_prospecting_crew.py`, `crews/tech_stack/tech_stack_crew.py`, `crews/web_presence/web_presence_crew.py`, `crews/saint_daily/saint_daily.py`, `utils/rss_utils.py`, `tools/web_search_factory.py`, `tools/fact_checking_factory.py`.
- Rewrite (import lines): `tools/scraper_factory.py`, `tools/web_tools.py`, `tools/location_tools.py`.
- Repoint (tests): `tests/tools/test_web_tools.py`, `tests/tools/test_location_tools.py`, `tests/tools/test_scraper_factory.py`.
- Delete (`git rm`): `tools/perplexity_search_tool.py`, `tools/brave_search_tool.py`, `tools/tavily_tool.py`, `tools/serpapi_tool.py`, `tools/hybrid_search_tool.py`, `tools/scrape_ninja_tool.py`, `tools/firecrawl_tool.py`, `tools/tech_stack_tool.py`, `tools/geoapify_places_tool.py`, `tools/google_fact_check_tool.py`, `tools/wikipedia_search_tool.py`, `tools/wikipedia_article_tool.py`, `tools/wikipedia_processing_tool.py`, `tools/rss_feed_parser_tool.py`, `tools/opml_parser_tool.py`, `tools/rss_feed_tool.py`, `tools/unified_rss_tool.py` (17 files).

**Interfaces:**
- All web factory/selector public signatures unchanged: `get_search_tools()`, `get_news_tools()`, `get_scrape_tools()`, `get_youtube_tools()`, `get_website_search_tools()`, `get_github_tools()`, `get_pdf_tools()`, `get_all_web_tools()` (web_tools); `get_location_tools()`; `get_scraper()`; `WebSearchFactory.create(provider)`; `FactCheckingToolsFactory.create(provider, **kwargs)`.

- [ ] **Step 1: Repoint the 9 `HybridSearchTool` crew imports.** In each of the 9 crew files, replace the line `from epic_news.tools.hybrid_search_tool import HybridSearchTool` with `from crewai_custom_tools import HybridSearchTool`. One-shot:
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  grep -rl "from epic_news.tools.hybrid_search_tool import HybridSearchTool" src/epic_news/crews \
    | xargs sed -i '' 's#from epic_news.tools.hybrid_search_tool import HybridSearchTool#from crewai_custom_tools import HybridSearchTool#'
  ```
  (ruff will re-sort the import into the correct block in Step 8.)

- [ ] **Step 2: Repoint `saint_daily.py` (3 Wikipedia imports → one line).** Replace lines 12-14:
  ```python
  from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool
  from epic_news.tools.wikipedia_processing_tool import WikipediaProcessingTool
  from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool
  ```
  with:
  ```python
  from crewai_custom_tools import WikipediaArticleTool, WikipediaProcessingTool, WikipediaSearchTool
  ```

- [ ] **Step 3: Repoint `utils/rss_utils.py`.** Replace `from epic_news.tools.unified_rss_tool import UnifiedRssTool` with `from crewai_custom_tools import UnifiedRssTool`. The programmatic call `UnifiedRssTool()._run(opml_file_path, days, output_file_path)` (rss_utils.py:22 and the `_run` call downstream) is unchanged — v0.3.0 restored that signature (verified in Task 1 Step 4).

- [ ] **Step 4: Repoint the two web selectors.**
  - `tools/web_search_factory.py` — replace lines 6-8:
    ```python
    from epic_news.tools.perplexity_search_tool import PerplexitySearchTool
    from epic_news.tools.serpapi_tool import SerpApiTool
    from epic_news.tools.tavily_tool import TavilyTool
    ```
    with:
    ```python
    from crewai_custom_tools import PerplexitySearchTool, SerpApiTool, TavilyTool
    ```
    Body (the `WebSearchFactory.create` if-chain) is unchanged.
  - `tools/fact_checking_factory.py` — replace line 3 `from .google_fact_check_tool import GoogleFactCheckTool` with `from crewai_custom_tools import GoogleFactCheckTool`. Body unchanged.

- [ ] **Step 5: Rewrite `tools/scraper_factory.py` (import lines only; keep Firecrawl lazy).**
  - Replace line 18 `from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool` with `from crewai_custom_tools import ScrapeNinjaTool`.
  - Replace the in-function lazy import (line 34) `from epic_news.tools.firecrawl_tool import FirecrawlTool` with `from crewai_custom_tools import FirecrawlTool`. Keep it lazy (inside the `firecrawl` branch) exactly as-is — this is a deliberate, pre-existing exception to the top-of-file rule (avoids importing the Firecrawl SDK unless selected) and the `get_scraper()` provider logic is unchanged.

- [ ] **Step 6: Rewrite `tools/web_tools.py` (import line only).** Replace line 16 `from epic_news.tools.perplexity_search_tool import PerplexitySearchTool` with `from crewai_custom_tools import PerplexitySearchTool`. Everything else stays: the `crewai_tools` imports (`GithubSearchTool`, `PDFSearchTool`, `ScrapeWebsiteTool`, `WebsiteSearchTool`, `YoutubeVideoSearchTool`), the lazy `from epic_news.tools.scraper_factory import get_scraper` inside `get_scrape_tools()`, and all 8 factory bodies are untouched.

- [ ] **Step 7: Rewrite `tools/location_tools.py` (import line only).** Replace line 10 `from epic_news.tools.geoapify_places_tool import GeoapifyPlacesTool` with `from crewai_custom_tools import GeoapifyPlacesTool`. `get_location_tools()` body unchanged.

- [ ] **Step 8: Repoint the 3 kept web tests.**
  - `tests/tools/test_web_tools.py` line 11 → `from crewai_custom_tools import PerplexitySearchTool`.
  - `tests/tools/test_location_tools.py` line 5 → `from crewai_custom_tools import GeoapifyPlacesTool`.
  - `tests/tools/test_scraper_factory.py` line 7 → `from crewai_custom_tools import ScrapeNinjaTool`. Then fix `test_get_scraper_firecrawl_with_stub` (lines 49-77): it currently injects a fake `sys.modules["epic_news.tools.firecrawl_tool"]`, which no longer matches the import path. Replace that test body with a direct patch of the symbol the factory now imports:
    ```python
    def test_get_scraper_firecrawl_with_stub(monkeypatch):
        """Patch FirecrawlTool where scraper_factory imports it (package top-level)."""

        class StubFirecrawlTool:
            def __init__(self, **kwargs):
                pass

        monkeypatch.setattr("crewai_custom_tools.FirecrawlTool", StubFirecrawlTool)
        monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "firecrawl")
        scraper = get_scraper()
        assert isinstance(scraper, StubFirecrawlTool)
    ```
    (Remove the now-unused `importlib`, `sys`, `types` imports at the top of the file.)

- [ ] **Step 9: Delete the 17 web tool files AND this domain's now-orphaned tests (13).** Deleting the tool files breaks the tests that import them, so remove both in this same commit to end green.
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  # Web-domain migrated-tool tests (import the files deleted below):
  git rm -f tests/tools/test_perplexity_search_tool.py \
         tests/tools/test_tavily_tool.py \
         tests/tools/test_serpapi_tool.py \
         tests/tools/test_scrape_ninja_tool.py \
         tests/tools/test_tech_stack_tool.py \
         tests/tools/test_geoapify_places_tool.py \
         tests/tools/test_google_fact_check_tool.py \
         tests/tools/test_wikipedia_article_tool.py \
         tests/tools/test_wikipedia_processing_tool.py \
         tests/tools/test_wikipedia_search_tool.py \
         tests/tools/test_rss_feed_parser_tool.py \
         tests/tools/test_opml_parser_tool.py \
         tests/tools/test_unified_rss_tool.py
  # The 17 web tool source files:
  git rm src/epic_news/tools/perplexity_search_tool.py \
         src/epic_news/tools/brave_search_tool.py \
         src/epic_news/tools/tavily_tool.py \
         src/epic_news/tools/serpapi_tool.py \
         src/epic_news/tools/hybrid_search_tool.py \
         src/epic_news/tools/scrape_ninja_tool.py \
         src/epic_news/tools/firecrawl_tool.py \
         src/epic_news/tools/tech_stack_tool.py \
         src/epic_news/tools/geoapify_places_tool.py \
         src/epic_news/tools/google_fact_check_tool.py \
         src/epic_news/tools/wikipedia_search_tool.py \
         src/epic_news/tools/wikipedia_article_tool.py \
         src/epic_news/tools/wikipedia_processing_tool.py \
         src/epic_news/tools/rss_feed_parser_tool.py \
         src/epic_news/tools/opml_parser_tool.py \
         src/epic_news/tools/rss_feed_tool.py \
         src/epic_news/tools/unified_rss_tool.py
  ```

- [ ] **Step 10: Guard, verify, commit.**
  ```bash
  # No lingering deep imports or references to deleted web modules:
  grep -rn "crewai_custom_tools\.tools" src tests && echo "DEEP IMPORT FOUND — fix" || echo "no deep imports OK"
  grep -rn -E "epic_news\.tools\.(perplexity_search_tool|brave_search_tool|tavily_tool|serpapi_tool|hybrid_search_tool|scrape_ninja_tool|firecrawl_tool|tech_stack_tool|geoapify_places_tool|google_fact_check_tool|wikipedia_search_tool|wikipedia_article_tool|wikipedia_processing_tool|rss_feed_parser_tool|opml_parser_tool|rss_feed_tool|unified_rss_tool)" src tests | grep -v __pycache__ && echo "STALE REF — fix" || echo "no stale refs OK"
  ```
  Then lint the changed files, run the suite + type check:
  ```bash
  uv run ruff check --fix src/epic_news/crews src/epic_news/utils/rss_utils.py src/epic_news/tools/web_tools.py src/epic_news/tools/location_tools.py src/epic_news/tools/scraper_factory.py src/epic_news/tools/web_search_factory.py src/epic_news/tools/fact_checking_factory.py tests/tools/test_web_tools.py tests/tools/test_location_tools.py tests/tools/test_scraper_factory.py
  uv run ruff format src/epic_news/crews src/epic_news/utils/rss_utils.py src/epic_news/tools tests/tools/test_web_tools.py tests/tools/test_location_tools.py tests/tools/test_scraper_factory.py
  uv run pytest -q
  uv run mypy src/epic_news
  ```
  Expected: **green** — the 13 web-domain migrated-tool tests were deleted in Step 9, so nothing imports the deleted modules. If pytest still errors on a `test_*_tool.py` import, a web test file was missed in Step 9 — `git rm` it and re-run. Then commit:
  ```bash
  git add src/epic_news/crews src/epic_news/utils/rss_utils.py src/epic_news/tools/web_tools.py src/epic_news/tools/location_tools.py src/epic_news/tools/scraper_factory.py src/epic_news/tools/web_search_factory.py src/epic_news/tools/fact_checking_factory.py tests/tools/test_web_tools.py tests/tools/test_location_tools.py tests/tools/test_scraper_factory.py
  # plus the git rm's from Step 9 (already staged by git rm) and any web-test deletions
  git commit -m "refactor(tools): source web-domain tools from crewai_custom_tools" \
             -m "Repoint 9 crews' HybridSearchTool, saint_daily Wikipedia tools, rss_utils UnifiedRss, and the web selectors/factories to the package; delete 17 in-repo web tool copies." \
             -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  ```

---

### Task 3: Finance domain — repoint importers, rewrite finance factories (incl. AlphaVantage rename), delete finance tool files

**Files:**
- Repoint (imports only): `crews/holiday_planner/holiday_planner_crew.py`, `crews/fin_daily/fin_daily.py`.
- Rewrite: `tools/finance_tools.py`, `tools/coinmarketcap_tool.py`.
- Repoint (tests): `tests/tools/test_finance_tools.py`, `tests/tools/test_coinmarketcap_tool.py`.
- Delete (`git rm`): `tools/yahoo_finance_ticker_info_tool.py`, `tools/yahoo_finance_news_tool.py`, `tools/yahoo_finance_company_info_tool.py`, `tools/yahoo_finance_etf_holdings_tool.py`, `tools/yahoo_finance_history_tool.py`, `tools/coinmarketcap_info_tool.py`, `tools/coinmarketcap_list_tool.py`, `tools/coinmarketcap_news_tool.py`, `tools/coinmarketcap_historical_tool.py`, `tools/kraken_api_tool.py`, `tools/exchange_rate_tool.py`, `tools/alpha_vantage_tool.py` (12 files).

**Interfaces:**
- Unchanged signatures: `get_yahoo_finance_tools()`, `get_stock_research_tools()`, `get_crypto_research_tools()`, `get_etf_research_tools()` (finance_tools); `get_coinmarketcap_tools()`.
- **The one rename:** `AlphaVantageCompanyOverviewTool` → package `AlphaVantageOverviewTool`, at the import and the `get_stock_research_tools()` usage.

- [ ] **Step 1: Repoint `holiday_planner_crew.py`.** Replace line 7 `from epic_news.tools.exchange_rate_tool import ExchangeRateTool` with `from crewai_custom_tools import ExchangeRateTool`. The five `ExchangeRateTool()` instantiations in the `@agent` methods are unchanged.

- [ ] **Step 2: Repoint `fin_daily.py`.** Replace line 8 `from epic_news.tools.kraken_api_tool import KrakenAssetListTool, KrakenTickerInfoTool` with `from crewai_custom_tools import KrakenAssetListTool, KrakenTickerInfoTool`.

- [ ] **Step 3: Rewrite `tools/finance_tools.py` imports + AlphaVantage usage.** Replace the import block (lines 8-16):
  ```python
  from crewai.tools import BaseTool

  from epic_news.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
  from epic_news.tools.kraken_api_tool import KrakenTickerInfoTool
  from epic_news.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
  from epic_news.tools.yahoo_finance_etf_holdings_tool import YahooFinanceETFHoldingsTool
  from epic_news.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
  from epic_news.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
  from epic_news.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool
  ```
  with:
  ```python
  from crewai.tools import BaseTool
  from crewai_custom_tools import (
      AlphaVantageOverviewTool,
      KrakenTickerInfoTool,
      YahooFinanceCompanyInfoTool,
      YahooFinanceETFHoldingsTool,
      YahooFinanceHistoryTool,
      YahooFinanceNewsTool,
      YahooFinanceTickerInfoTool,
  )
  ```
  Then in `get_stock_research_tools()` replace the line `AlphaVantageCompanyOverviewTool(),` with `AlphaVantageOverviewTool(),`. All four factory bodies (tool lists) are otherwise unchanged.

- [ ] **Step 4: Rewrite `tools/coinmarketcap_tool.py` imports.** Replace lines 8-15:
  ```python
  from crewai.tools import BaseTool

  from .coinmarketcap_historical_tool import CoinMarketCapHistoricalTool

  # Import tool classes from their new locations
  from .coinmarketcap_info_tool import CoinMarketCapInfoTool
  from .coinmarketcap_list_tool import CoinMarketCapListTool
  from .coinmarketcap_news_tool import CoinMarketCapNewsTool
  ```
  with:
  ```python
  from crewai.tools import BaseTool
  from crewai_custom_tools import (
      CoinMarketCapHistoricalTool,
      CoinMarketCapInfoTool,
      CoinMarketCapListTool,
      CoinMarketCapNewsTool,
  )
  ```
  `get_coinmarketcap_tools()` body (the 4-tool list) is unchanged.

- [ ] **Step 5: Repoint the 2 kept finance tests.**
  - `tests/tools/test_finance_tools.py`: replace line 3 `from epic_news.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool` with `from crewai_custom_tools import AlphaVantageOverviewTool`; replace lines 10-15 (the Kraken + Yahoo imports) with `from crewai_custom_tools import (KrakenTickerInfoTool, YahooFinanceCompanyInfoTool, YahooFinanceETFHoldingsTool, YahooFinanceHistoryTool, YahooFinanceNewsTool, YahooFinanceTickerInfoTool)`; and in `test_get_stock_research_tools` replace the assertion symbol `AlphaVantageCompanyOverviewTool` with `AlphaVantageOverviewTool` (line ~41). The four factory assertions on counts/instances stay valid.
  - `tests/tools/test_coinmarketcap_tool.py`: replace lines 3-6 (the 4 relative CMC class imports) with `from crewai_custom_tools import (CoinMarketCapHistoricalTool, CoinMarketCapInfoTool, CoinMarketCapListTool, CoinMarketCapNewsTool)`; keep line 7 `from epic_news.tools.coinmarketcap_tool import get_coinmarketcap_tools`. The `isinstance` assertions stay valid.

- [ ] **Step 6: Delete the 12 finance tool files AND this domain's now-orphaned tests (13).**
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  # Finance-domain migrated-tool tests:
  git rm -f tests/tools/test_alpha_vantage_tool.py \
         tests/tools/test_coinmarketcap_historical_tool.py \
         tests/tools/test_coinmarketcap_info_tool.py \
         tests/tools/test_coinmarketcap_list_tool.py \
         tests/tools/test_coinmarketcap_news_tool.py \
         tests/tools/test_exchange_rate_tool.py \
         tests/tools/test_kraken_api_tool.py \
         tests/tools/manual_kraken_test.py \
         tests/tools/test_yahoo_finance_company_info_tool.py \
         tests/tools/test_yahoo_finance_etf_holdings_tool.py \
         tests/tools/test_yahoo_finance_history_tool.py \
         tests/tools/test_yahoo_finance_news_tool.py \
         tests/tools/test_yahoo_finance_ticker_info_tool.py
  # The 12 finance tool source files:
  git rm src/epic_news/tools/yahoo_finance_ticker_info_tool.py \
         src/epic_news/tools/yahoo_finance_news_tool.py \
         src/epic_news/tools/yahoo_finance_company_info_tool.py \
         src/epic_news/tools/yahoo_finance_etf_holdings_tool.py \
         src/epic_news/tools/yahoo_finance_history_tool.py \
         src/epic_news/tools/coinmarketcap_info_tool.py \
         src/epic_news/tools/coinmarketcap_list_tool.py \
         src/epic_news/tools/coinmarketcap_news_tool.py \
         src/epic_news/tools/coinmarketcap_historical_tool.py \
         src/epic_news/tools/kraken_api_tool.py \
         src/epic_news/tools/exchange_rate_tool.py \
         src/epic_news/tools/alpha_vantage_tool.py
  ```

- [ ] **Step 7: Guard, verify, commit.** Confirm the rename landed everywhere and no stale refs remain:
  ```bash
  grep -rn "AlphaVantageCompanyOverviewTool" src tests | grep -v __pycache__ && echo "RENAME MISSED — fix" || echo "rename clean OK"
  grep -rn -E "epic_news\.tools\.(yahoo_finance_|coinmarketcap_(info|list|news|historical)_tool|kraken_api_tool|exchange_rate_tool|alpha_vantage_tool)" src tests | grep -v __pycache__ && echo "STALE REF — fix" || echo "no stale refs OK"
  ```
  The 13 finance migrated-tool tests were deleted in Step 6, so the suite stays green. Then:
  ```bash
  uv run ruff check --fix src/epic_news/crews/holiday_planner/holiday_planner_crew.py src/epic_news/crews/fin_daily/fin_daily.py src/epic_news/tools/finance_tools.py src/epic_news/tools/coinmarketcap_tool.py tests/tools/test_finance_tools.py tests/tools/test_coinmarketcap_tool.py
  uv run ruff format src/epic_news/crews/holiday_planner/holiday_planner_crew.py src/epic_news/crews/fin_daily/fin_daily.py src/epic_news/tools/finance_tools.py src/epic_news/tools/coinmarketcap_tool.py tests/tools/test_finance_tools.py tests/tools/test_coinmarketcap_tool.py
  uv run pytest -q
  uv run mypy src/epic_news
  git add src/epic_news/crews/holiday_planner/holiday_planner_crew.py src/epic_news/crews/fin_daily/fin_daily.py src/epic_news/tools/finance_tools.py src/epic_news/tools/coinmarketcap_tool.py tests/tools/test_finance_tools.py tests/tools/test_coinmarketcap_tool.py
  git commit -m "refactor(tools): source finance-domain tools from crewai_custom_tools" \
             -m "Yahoo x5, CoinMarketCap x4, Kraken, ExchangeRate, and AlphaVantage now come from the package; AlphaVantageCompanyOverviewTool renamed to AlphaVantageOverviewTool at import and usage. Deletes 12 in-repo finance tool copies." \
             -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  ```

---

### Task 4: OSINT + enterprise — rewrite github/email/rag factories, delete those tool files

No crew imports these classes directly (all wired via factories), so this task is entirely factory rewrites + deletes. The `DelegatingEmailSearchTool` class currently *lives* in `email_search.py`; its class moves to the package and the local file keeps only the `get_email_search_tools()` factory.

**Files:**
- Rewrite: `tools/github_tools.py`, `tools/email_search.py`, `tools/rag_tools.py`.
- Repoint (tests): `tests/tools/test_rag_tools.py`.
- Delete (`git rm`): `tools/github_search_tool.py`, `tools/github_org_tool.py`, `tools/hunter_io_tool.py`, `tools/serper_email_search_tool.py`, `tools/todoist_tool.py`, `tools/airtable_tool.py`, `tools/accuweather_tool.py`, `tools/save_to_rag_tool.py` (8 files).

**Interfaces:**
- Unchanged signatures: `get_github_tools() -> list[BaseTool]`, `get_email_search_tools() -> list[BaseTool]`, `get_rag_tools(collection_suffix: str | None = None) -> list[Tool]`.
- `get_rag_tools` still injects epic_news's configured retrieval `RagTool` into the package `SaveToRagTool` via `rag_tool=` (v0.3.0 supports this — verified Task 1 Step 4). epic_news KEEPS `rag_config.py` and the `crewai_tools.RagTool` retrieval instance.

- [ ] **Step 1: Rewrite `tools/github_tools.py` import line.** Replace line 8 `from .github_search_tool import GitHubSearchTool` with `from crewai_custom_tools import GitHubSearchTool`. The rest (os/dotenv/`load_dotenv()`, the `GITHUB_TOKEN` guard, `return [GitHubSearchTool()]`) is unchanged. Final file:
  ```python
  """Factory functions for creating GitHub-related tools."""

  import os

  from crewai.tools import BaseTool
  from crewai_custom_tools import GitHubSearchTool
  from dotenv import load_dotenv

  # Load environment variables from .env file
  load_dotenv()


  def get_github_tools() -> list[BaseTool]:
      """Initializes and returns a list of GitHub tools."""
      # Get GitHub token from environment
      github_token = os.getenv("GITHUB_TOKEN")
      if not github_token:
          print("Warning: GITHUB_TOKEN environment variable not set. GitHubSearchTool will not be available.")
          return []

      return [GitHubSearchTool()]
  ```

- [ ] **Step 2: Rewrite `tools/email_search.py` — drop the local class, keep the factory.** Replace the entire file with:
  ```python
  """Email search tool factory.

  The delegating tool implementation now lives in crewai_custom_tools; epic_news
  keeps only the factory so crew call sites (`get_email_search_tools`) are unchanged.
  """

  from crewai.tools import BaseTool
  from crewai_custom_tools import DelegatingEmailSearchTool


  def get_email_search_tools() -> list[BaseTool]:
      """Returns a list of email search tools."""
      return [DelegatingEmailSearchTool()]
  ```
  This removes the local `DelegatingEmailSearchTool` class and its `HunterIOTool`/`SerperEmailSearchTool` imports (the package tool routes to the package's own Hunter/Serper internally).

- [ ] **Step 3: Rewrite `tools/rag_tools.py` import line (body identical).** Replace line 12 `from epic_news.tools.save_to_rag_tool import SaveToRagTool` with `from crewai_custom_tools import SaveToRagTool`. Keep `from crewai_tools import RagTool` and `from epic_news.rag_config import build_rag_tool_kwargs`. The body is unchanged — critically, `save_to_rag_tool = SaveToRagTool(rag_tool=rag_tool)` (line 36) stays exactly as written; v0.3.0's `SaveToRagTool.__init__(rag_tool=None)` accepts it. Final relevant section:
  ```python
  from crewai.tools import BaseTool as Tool
  from crewai_tools import RagTool
  from crewai_custom_tools import SaveToRagTool

  from epic_news.rag_config import build_rag_tool_kwargs


  def get_rag_tools(collection_suffix: str | None = None) -> list[Tool]:
      rag_tool = RagTool(
          **build_rag_tool_kwargs(collection_suffix=collection_suffix),
          summarize=True,
          description=(
              "Use this tool to retrieve information from the epic_news knowledge base. "
              "Ask questions about financial data, market trends, or previously "
              "researched information."
          ),
      )
      save_to_rag_tool = SaveToRagTool(rag_tool=rag_tool)
      return [rag_tool, save_to_rag_tool]
  ```

- [ ] **Step 4: Repoint `tests/tools/test_rag_tools.py`.** Replace line 7 `from epic_news.tools.save_to_rag_tool import SaveToRagTool` with `from crewai_custom_tools import SaveToRagTool`. The test asserts `save_tool._rag_tool == retrieval_tool` (lines 44, 65) — this relies on the package storing the injected tool on a private `_rag_tool` attribute. **Verify** with `python -c "from crewai_custom_tools import SaveToRagTool; t=SaveToRagTool(rag_tool='X'); print(t._rag_tool)"` → should print `X`. If the package uses a different attribute name, update those two assertions to match (and note it); do not weaken the injection check — it is the whole point of the v0.3.0 fix.

- [ ] **Step 5: Delete the 8 osint/enterprise tool files AND this domain's now-orphaned tests (9).** (Keep `tests/tools/test_rag_tools.py` — it was repointed in Step 4 and tests the surviving factory.)
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  # OSINT/enterprise migrated-tool tests:
  git rm -f tests/tools/test_github_search_tool.py \
         tests/tools/test_github_org_tool.py \
         tests/tools/test_hunter_io_tool.py \
         tests/tools/test_serper_email_search_tool.py \
         tests/tools/test_email_search.py \
         tests/tools/test_todoist_tool.py \
         tests/tools/test_airtable_tool.py \
         tests/tools/test_accuweather_tool.py \
         tests/tools/test_save_to_rag_tool.py
  # The 8 osint/enterprise tool source files:
  git rm src/epic_news/tools/github_search_tool.py \
         src/epic_news/tools/github_org_tool.py \
         src/epic_news/tools/hunter_io_tool.py \
         src/epic_news/tools/serper_email_search_tool.py \
         src/epic_news/tools/todoist_tool.py \
         src/epic_news/tools/airtable_tool.py \
         src/epic_news/tools/accuweather_tool.py \
         src/epic_news/tools/save_to_rag_tool.py
  ```

- [ ] **Step 6: Guard, verify, commit.**
  ```bash
  grep -rn -E "epic_news\.tools\.(github_search_tool|github_org_tool|hunter_io_tool|serper_email_search_tool|todoist_tool|airtable_tool|accuweather_tool|save_to_rag_tool)" src tests | grep -v __pycache__ && echo "STALE REF — fix" || echo "no stale refs OK"
  ```
  The 9 osint/enterprise migrated-tool tests were deleted in Step 5, so the suite stays green. Then:
  ```bash
  uv run ruff check --fix src/epic_news/tools/github_tools.py src/epic_news/tools/email_search.py src/epic_news/tools/rag_tools.py tests/tools/test_rag_tools.py
  uv run ruff format src/epic_news/tools/github_tools.py src/epic_news/tools/email_search.py src/epic_news/tools/rag_tools.py tests/tools/test_rag_tools.py
  uv run pytest -q
  uv run mypy src/epic_news
  git add src/epic_news/tools/github_tools.py src/epic_news/tools/email_search.py src/epic_news/tools/rag_tools.py tests/tools/test_rag_tools.py
  git commit -m "refactor(tools): source osint/enterprise tools from crewai_custom_tools" \
             -m "GitHub, Hunter/Serper email (via DelegatingEmailSearchTool), Todoist, Airtable, AccuWeather, and SaveToRag now come from the package; get_rag_tools still injects the epic_news-configured RagTool. Deletes 8 in-repo tool copies." \
             -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  ```

---

### Task 5: Factory signature-parity + import-hygiene audit

No code rewrites remain (Tasks 2-4 did them co-located with deletions, to stay green). This task proves the migration is complete and crew call sites are untouched.

**Files:** none modified (verification only). If a check fails, fix in the owning file and fold into that domain's commit or a small follow-up commit.

**Interfaces:** confirms these public signatures are byte-for-byte unchanged (crews call them, so any change breaks callers):

| Factory / selector | Public API (must be unchanged) | Kept non-package pieces |
|---|---|---|
| `web_tools.py` | `get_search_tools`, `get_news_tools`, `get_scrape_tools`, `get_youtube_tools`, `get_website_search_tools`, `get_github_tools`, `get_pdf_tools`, `get_all_web_tools` | crewai_tools `ScrapeWebsiteTool`/`YoutubeVideoSearchTool`/`WebsiteSearchTool`/`PDFSearchTool`/`GithubSearchTool`; lazy `get_scraper()` |
| `location_tools.py` | `get_location_tools` | — |
| `finance_tools.py` | `get_yahoo_finance_tools`, `get_stock_research_tools`, `get_crypto_research_tools`, `get_etf_research_tools` | `crewai.tools.BaseTool` typing |
| `coinmarketcap_tool.py` | `get_coinmarketcap_tools` | `crewai.tools.BaseTool` typing |
| `github_tools.py` | `get_github_tools` | `GITHUB_TOKEN` guard, `load_dotenv` |
| `rag_tools.py` | `get_rag_tools(collection_suffix=None)` | `crewai_tools.RagTool`, `rag_config.build_rag_tool_kwargs`, `rag_tool=` injection |
| `email_search.py` | `get_email_search_tools` | — |
| `scraper_factory.py` | `get_scraper` | `WEB_SCRAPER_PROVIDER` selection, lazy Firecrawl |
| `web_search_factory.py` | `WebSearchFactory.create(provider)` | provider fallback logic |
| `fact_checking_factory.py` | `FactCheckingToolsFactory.create(provider, **kwargs)` | — |

- [ ] **Step 1: No deep-package imports anywhere.**
  ```bash
  grep -rn "from crewai_custom_tools\.\|import crewai_custom_tools\." src tests | grep -v __pycache__ && echo "DEEP IMPORT — fix to top-level" || echo "top-level imports only OK"
  ```

- [ ] **Step 2: No stale `epic_news.tools.<migrated>` references remain in `src`.**
  ```bash
  grep -rn -E "epic_news\.tools\.(perplexity_search_tool|brave_search_tool|tavily_tool|serpapi_tool|hybrid_search_tool|scrape_ninja_tool|firecrawl_tool|tech_stack_tool|geoapify_places_tool|google_fact_check_tool|wikipedia_(search|article|processing)_tool|rss_feed_parser_tool|opml_parser_tool|rss_feed_tool|unified_rss_tool|yahoo_finance_\w+_tool|coinmarketcap_(info|list|news|historical)_tool|kraken_api_tool|exchange_rate_tool|alpha_vantage_tool|github_(search|org)_tool|hunter_io_tool|serper_email_search_tool|todoist_tool|airtable_tool|accuweather_tool|save_to_rag_tool)" src | grep -v __pycache__ && echo "STALE — fix" || echo "src clean OK"
  ```

- [ ] **Step 3: Factories importable and signatures intact.**
  ```bash
  python -c "
  from epic_news.tools.web_tools import get_search_tools, get_all_web_tools
  from epic_news.tools.location_tools import get_location_tools
  from epic_news.tools.finance_tools import get_stock_research_tools, get_crypto_research_tools
  from epic_news.tools.coinmarketcap_tool import get_coinmarketcap_tools
  from epic_news.tools.github_tools import get_github_tools
  from epic_news.tools.rag_tools import get_rag_tools
  from epic_news.tools.email_search import get_email_search_tools
  from epic_news.tools.scraper_factory import get_scraper
  from epic_news.tools.web_search_factory import WebSearchFactory
  from epic_news.tools.fact_checking_factory import FactCheckingToolsFactory
  print('all factories import OK')
  print('stock tools:', [type(t).__name__ for t in get_stock_research_tools()])
  print('cmc tools:', [type(t).__name__ for t in get_coinmarketcap_tools()])
  print('email tools:', [type(t).__name__ for t in get_email_search_tools()])
  "
  ```
  Expected: prints class lists; `get_stock_research_tools` includes `AlphaVantageOverviewTool`. (This exercises the AlphaVantage rename end-to-end.)

- [ ] **Step 4: Full green gate.**
  ```bash
  uv run pytest -q   # with migrated-tool tests deleted (Task 6) — if not yet, expect the enumerated failures
  uv run mypy src/epic_news
  ```
  No commit needed if nothing changed. If a fix was required, commit it with the standard trailer.

---

### Task 6: Delete dead code + migrated tests, update prose prompts, rescope JSON ratchet, prune orphaned infra

**Files:**
- Delete dead code: `src/epic_news/tools/custom_tool.py` (`MyCustomTool` — no `src` usage), `src/epic_news/tools/batch_article_scraper_tool.py` + `tests/tools/test_batch_article_scraper_tool.py`.
- Verify migrated-tool tests are gone (they were deleted per-domain in Tasks 2-4; Step 2 is a safety-net check).
- Update prose: `src/epic_news/crews/shopping_advisor/config/agents.yaml`, `src/epic_news/crews/deep_research/config/agents.yaml`.
- Rescope: `tests/tools/test_json_contract_ratchet.py` (`KNOWN_LEGACY`).
- Prune orphaned infra (after grep verify): `search_base.py`, `github_base.py`, `email_base.py`, `cache_manager.py`.

**Interfaces:**
- Tests KEPT (do NOT delete): `test_html_to_pdf_tool.py`, `test_render_report_tool.py`, `test_reporting_tool.py` (Group-2); `test_http_resilience.py` (tests `utils/http`); `test_json_outputs.py` (tests `_json_utils` + `data_centric_tools`); `test_json_contract_ratchet.py`; the 6 repointed factory/selector tests from Tasks 2-4 (`test_web_tools.py`, `test_location_tools.py`, `test_scraper_factory.py`, `test_finance_tools.py`, `test_coinmarketcap_tool.py`, `test_rag_tools.py`); `__init__.py`.

- [ ] **Step 1: Delete dead code (Tier-C drop + `MyCustomTool`).**
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  git rm src/epic_news/tools/custom_tool.py \
         src/epic_news/tools/batch_article_scraper_tool.py \
         tests/tools/test_batch_article_scraper_tool.py
  grep -rn "MyCustomTool\|batch_article_scraper" src tests | grep -v __pycache__ && echo "REF REMAINS — fix" || echo "dead code clean OK"
  ```

- [ ] **Step 2: Verify the migrated tools' tests are already gone (deleted per-domain in Tasks 2-4).** The 35 migrated-tool test modules were removed inside their domain tasks (Task 2 Step 9 = 13 web; Task 3 Step 6 = 13 finance; Task 4 Step 5 = 9 osint/enterprise), and `test_batch_article_scraper_tool.py` in Step 1 above = 36 total. Confirm none survive:
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  ls tests/tools/ | grep -E "^(test_(perplexity_search|tavily|serpapi|scrape_ninja|tech_stack|geoapify_places|google_fact_check|wikipedia_(article|processing|search)|rss_feed_parser|opml_parser|unified_rss|alpha_vantage|coinmarketcap_(historical|info|list|news)|exchange_rate|kraken_api|yahoo_finance_\w+|github_(search|org)|hunter_io|serper_email_search|email_search|todoist|airtable|accuweather|save_to_rag)_tool\.py|manual_kraken_test\.py)$" \
    && echo "STRAGGLER TEST — git rm it (it belonged to a domain task)" || echo "all migrated-tool tests removed OK"
  ```
  If any straggler prints, `git rm -f tests/tools/<file>` it here. (This is a safety net; the domain tasks should have removed them all.)

- [ ] **Step 3: Prune orphaned infra (verify first).** After Steps 1-2 and Tasks 2-4, these infra modules' only consumers were migrated/deleted. Confirm each is genuinely unreferenced, then delete:
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  for m in search_base github_base email_base cache_manager; do
    echo "=== $m ==="
    grep -rn "$m" src tests | grep -v "__pycache__" | grep -v "tools/$m.py"
  done
  ```
  Expected: no hits for any of the four (their consumers — `tech_stack_tool`, `github_*_tool`, `hunter_io_tool`/`serper_email_search_tool`, and the Yahoo/Kraken/AlphaVantage cache users — are all deleted). For each that shows **zero** hits, delete it:
  ```bash
  git rm src/epic_news/tools/search_base.py \
         src/epic_news/tools/github_base.py \
         src/epic_news/tools/email_base.py \
         src/epic_news/tools/cache_manager.py
  ```
  If any module still shows a reference (unexpected), leave that one and note the referrer. Do **not** delete `_json_utils.py` — it is still used by the kept `data_centric_tools.py` (and `test_json_outputs.py`).

- [ ] **Step 4: Update the 2 prose prompts (cosmetic — package keeps identical class names).** The migrated web tools keep their exact class names in the package (`ScrapeNinjaTool`, `BraveSearchTool`, `PerplexitySearchTool`), so no functional rename is needed; align prose for precision only.
  - `src/epic_news/crews/shopping_advisor/config/agents.yaml` — three agents list a bare `- ScrapeNinja` bullet (lines ~13, ~31, ~50) and "Search tools (Serper, ScrapeNinja)" (line ~9). Optionally normalize `ScrapeNinja` → `ScrapeNinjaTool` for consistency with the runtime tool name. No other change.
  - `src/epic_news/crews/deep_research/config/agents.yaml` line ~25 lists `(BraveSearchTool, PerplexitySearchTool, ScrapeNinjaTool, ScrapeWebsiteTool)` — these names are already current/correct in the package; leave as-is (verify-only). If you renamed anything upstream, reflect it here.
  These are agent-backstory prose only (tool names are runtime-transparent — agents call the live `name` from their tool list), so this step is low-severity.

- [ ] **Step 5: Rescope the JSON-contract ratchet to surviving epic_news-owned tools.** `tests/tools/test_json_contract_ratchet.py` scans `src/epic_news/tools/*.py` for `_run` without a JSON marker; its `KNOWN_LEGACY` set was seeded from the pre-migration file list, so deleted filenames are now "stale" (fails `test_known_legacy_list_is_honest`). Re-derive:
  ```bash
  uv run pytest tests/tools/test_json_contract_ratchet.py -v
  ```
  It will report stale entries (deleted files) and/or the current violator set. Edit `KNOWN_LEGACY` to contain **exactly** the surviving `src/epic_news/tools/*.py` files that still define `_run` without a JSON marker (i.e., remove every migrated/deleted filename; keep only Group-2/kept tools that genuinely still violate — e.g. reporting/report-generator tools). Re-run until both ratchet tests pass. This satisfies the spec's "scope the ratchet to epic_news-owned tools."

- [ ] **Step 6: Verify + commit.**
  ```bash
  uv run ruff check --fix tests/tools/test_json_contract_ratchet.py src/epic_news/crews/shopping_advisor/config/agents.yaml src/epic_news/crews/deep_research/config/agents.yaml || true
  uv run yamllint -s src/epic_news/crews/shopping_advisor/config/agents.yaml src/epic_news/crews/deep_research/config/agents.yaml
  uv run pytest -q
  uv run mypy src/epic_news
  git add tests/tools/test_json_contract_ratchet.py \
          src/epic_news/crews/shopping_advisor/config/agents.yaml \
          src/epic_news/crews/deep_research/config/agents.yaml
  # (git rm'd files from Steps 1-3 are already staged)
  git commit -m "chore(tools): drop dead code and orphaned infra; rescope JSON ratchet" \
             -m "Delete MyCustomTool + BatchArticleScraper (Tier-C drop) and now-unreferenced search_base/github_base/email_base/cache_manager. Rescope KNOWN_LEGACY to surviving epic_news-owned tools; refresh 2 prose prompts. (Migrated-tool tests were removed per-domain in Tasks 2-4.)" \
             -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
  ```

---

### Task 7: Final verification + per-domain manual smoke

**Files:** none modified.

**Interfaces:** confirms the full gate CI enforces, plus that tools resolve at runtime (the RSS output file is the one programmatic tool-output consumer to eyeball).

- [ ] **Step 1: Full static + test gate.**
  ```bash
  cd /Users/fjacquet/Projects/crews/epic_news
  uv sync --all-extras && uv pip install -e .
  uv run pytest -q
  uv run mypy src/epic_news
  uv run ruff check .
  ```
  Expected: all green/clean.

- [ ] **Step 2: Import-hygiene final sweep (mirrors Task 5 guards, whole repo).**
  ```bash
  grep -rn "from crewai_custom_tools\.\|import crewai_custom_tools\." src tests | grep -v __pycache__ && echo "DEEP IMPORT" || echo "top-level only OK"
  grep -rln "epic_news.tools" src | grep -v __pycache__   # should list only surviving factories/selectors/Group-2/rag/utils
  ```

- [ ] **Step 3: Manual `crewai flow kickoff` smoke — one crew per domain.** Run the flow (or the smallest crew per domain) and confirm tools resolve and reports render:
  - A **search/web** crew (e.g. deep_research or shopping_advisor) — confirms Perplexity/Hybrid/Scrape resolve.
  - A **finance** crew (fin_daily) — confirms Yahoo/Kraken/CMC/AlphaVantage resolve.
  - The **RSS/news** path (news_daily via `rss_utils.py`) — confirm the `RssFeeds` JSON **output file is still written** (v0.3.0 UnifiedRss restored file output). Check the expected `output/…` path exists and is non-empty after the run.
  ```bash
  crewai flow kickoff   # or: make run-crew
  ```
  Expected: no `ImportError`/`ModuleNotFoundError` for any tool; reports generated; RSS output file present. (The HolidayPlanner OpenRouter `APIError` is a known, out-of-scope LLM issue — not a tool regression.)

- [ ] **Step 4: Report.** Summarize: commits added (Tasks 1-6), tool files deleted (37 Group-1 + 2 dead + up to 4 infra), test modules deleted (36), factories rewritten (10 incl. selectors), and the final `KNOWN_LEGACY` count.

---

## Self-review note — spec coverage map

Every section of `2026-07-08-tools-migration-crewai-custom-tools-design.md` maps to a task:

- **Decision 1 (rip-and-replace Group 1):** Tasks 2/3/4 delete 37 tool files + import classes from the package.
- **Decision 2 (keep Group 2 + factories):** Group-2 tools (`render_report_tool`, `html_to_pdf_tool`, `universal_report_tool`, `reporting_tool`, `html_generator_tool`, `data_centric_tools`, `report_tools`, `utility_tools`) and `_json_utils`/`rag_config` are never deleted; factories rewritten in-place (Tasks 2-4), audited in Task 5.
- **Decision 3 (git-pinned tag):** Task 1 Step 2 adds `@v0.3.0` and stages `uv.lock`.
- **Decision 4 (safety net → upstream → migration):** Task 1 (safety net + dep) precedes Tasks 2-7; Workstream 1/v0.3.0 assumed done (Task 1 Step 4 smoke-verifies its two contracts).
- **Decision 5 / Tier C:** BatchArticleScraper dropped (Task 6 Step 1); SaveToRag `rag_tool=` injection preserved (Task 4 Step 3, `rag_config` kept); UnifiedRss restored signature consumed unchanged by `rss_utils.py` (Task 2 Step 3, smoke Task 7 Step 3).
- **Tier A/B (agent-transparent swaps + the AlphaVantage rename):** Tasks 2-4 repoint imports; Task 3 Step 3/5 handles `AlphaVantageCompanyOverviewTool → AlphaVantageOverviewTool` at import + usage + test; two prose prompts refreshed (Task 6 Step 4); migrated-tool tests deleted per-domain (Tasks 2-4), safety-net verified (Task 6 Step 2).
- **YAGNI-verified unused tools:** the "delete-only, no importer" list (brave/tech_stack/rss_feed/rss_feed_parser/opml_parser/todoist/accuweather/github_org) is deleted without wiring changes (Tasks 2-4).
- **Phases 0-4:** Phase 0 → Task 1; Phase 1 (upstream) → assumed, verified Task 1 Step 4; Phase 2 (repoint) → Tasks 2-4 import steps; Phase 3 (factory bodies) → Tasks 2-4 rewrite steps + Task 5 audit; Phase 4 (delete + reconcile + ratchet) → Task 6.
- **Out of scope:** HolidayPlanner APIError (noted Task 7 Step 3), Group-2 tools (never touched), net-new package tools (not adopted), YAGNI features (not restored), `models/` files (left intact — noted in the call-site map).
- **Risks:** upstream-contract mismatch → Task 1 Step 4 + Task 4 Step 4 smoke; module-layout deep-import → top-level-only constraint + Task 5 Step 1 / Task 7 Step 2 grep; AlphaVantage rename missed → Task 3 Step 7 grep + mypy; agent-transparent surprise → kept safety-net e2e/characterization tests run every task; cache removal → accepted (Kraken/AlphaVantage `cache_manager` deleted in Task 6 Step 3).
- **Testing & verification:** incremental `uv run pytest -q` + `mypy` after every task; kept `tests/flows/test_reception_flow_e2e.py`; manual per-domain kickoff + RSS-file check (Task 7 Step 3).
- **Rollback:** every task is one isolated commit; reverting the Task 1 dependency line + Tasks 2-6 commits restores the in-repo tools (git-tag pin makes the package side inert).
