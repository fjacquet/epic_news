# Changelog

All notable changes to Epic News are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [3.0.0] — 2026-04-26

A modernization milestone that closes the door on accumulated infrastructure debt and re-aligns the repository with current industry conventions. No runtime API surface change; the major bump signals the operational reset (branch rename, working CI, secrets-free tests).

### Changed

- **Default branch renamed** `master` → `main`. All workflow triggers, README badges, and `mkdocs.yml::edit_uri` updated. Local clones must run `git branch -m master main && git fetch origin && git branch -u origin/main main`.
- **Dependency-installation step in CI** now runs `make dev` (full extras) instead of `make install`. After v2.2.0 moved pytest/pytest-cov/pytest-asyncio/etc. into `[project.optional-dependencies] test`, the production `make install` no longer installed the test runner.
- **`get_project_root()`** rewritten to be portable: `EPIC_NEWS_PROJECT_ROOT` env override → walk up from `__file__` for `pyproject.toml` → legacy `~/Projects/crews/epic_news` fallback. Drops the hardcoded path that broke CI (`/home/runner/work/epic_news/epic_news`).
- **Pre-commit hooks** point at `uv run <tool>` (ruff, yamllint, mypy) so they find their executables in `.venv` instead of failing with "command not found".
- **`make validate`** now runs lint + mypy + test (was lint + test). Matches CI exactly so failures surface locally before push.
- **`pestel_crew.py`** — added `# type: ignore[call-arg, arg-type]` markers on the 7 `Task()` constructors and the `Crew()` constructor so mypy stops complaining about CrewAI's `@CrewBase` decorator magic (description/expected_output are injected from YAML; `max_iter` is a runtime kwarg).

### Fixed

- **CI hadn't run automatically since July 2025** — the workflow trigger was `branches: [ main ]` while the repo was on `master`. Now consistent on `main`.
- **20 mypy errors** in `pestel_crew.py` that were never seen because CI was silent.
- **GitHub Actions versions bumped** to clear Node.js 20 deprecation warnings: `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v8.1.0` (pinned — no floating `v8` major tag), `codecov/codecov-action@v6`, `actions/upload-pages-artifact@v5`, `actions/deploy-pages@v5`, `actions/labeler@v6`, `docker/build-push-action@v7`, `docker/login-action@v4`, `docker/metadata-action@v6`, `docker/setup-buildx-action@v4`.
- **`uv.lock` version drift** that broke the four Dockerfile builds (lock recorded `epic-news==0.1.0` after the v2.1.0 bump).

### Security

- **Tests no longer require real API keys.** `pyproject.toml::[tool.pytest.ini_options].env` injects sentinel values for every credential at pytest startup (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `COMPOSIO_API_KEY`, `TAVILY_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHAVANTAGE_API_KEY`, `COINMARKETCAP_API_KEY`, `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`, `MAIL`, `EPIC_ENABLE_EMAIL=false`). The CI `create env file` step that was passing real GitHub secrets into the test job is replaced with a stub `.env` containing only sentinels.

## [2.2.0] — 2026-04-26

### Added
- **Documentation site auto-published to GitHub Pages**: every push to `master` that touches `docs/`, `mkdocs.yml`, `README.md`, or `CHANGELOG.md` rebuilds the site at https://fjacquet.github.io/epic_news/ (Material theme, Diátaxis nav, light/dark toggle).
- **Per-category use case pages** in `docs/tutorials/use_cases/` (finance, news_research, business_intel, lifestyle) — each lists its crews, sample prompts, and outputs.
- **`docs/how-to/troubleshooting.md`** — diagnoses wrong crew classification, missing email, Composio Gmail connection issues, using the loguru/PostResult breadcrumbs added in v2.1.0.
- **`docs/reference/outputs.md`** — explains where Epic News writes HTML/JSON, what each loguru emoji line means, how PostResult fields map to delivery outcomes.

### Changed
- **README slimmed** from 341 → ~50 lines: title + badges + 30-second TL;DR + a small table linking into the docs (which is now the manual). New "Docs" badge points at the published site.
- **`docs/tutorials/user_guide.md`** rewritten as a 4-step landing page with a ToC pointing into the per-category use_case pages.
- **`docs/tutorials/index.md`** updated to surface the new pages.

### Removed
- **Standalone HTML dashboard pipeline**: deleted `src/epic_news/utils/dashboard_generator.py`, `templates/dashboard_template.html`, `templates/css/dashboard.css`, and `tests/utils/test_dashboard_generator.py`. The metrics-collecting `Dashboard` class in `epic_news.utils.observability` is unrelated and stays.

### Fixed
- **`uv.lock` version drift**: the v2.1.0 release bumped `pyproject.toml` to `2.1.0` but the lock still referenced `epic-news==0.1.0`, breaking `uv sync --locked` in all four Dockerfile builds. Refreshed.

### Security
- **litellm 1.83.0 advisories** (CVE-2025-65039 / Critical SQLi in proxy API key verification, CVE-2025-65033 / High RCE in MCP stdio test, CVE-2025-65034 / High SSTI in `/prompts/test`): not exploitable here — Epic News uses litellm only as the SDK called by CrewAI for completions; the litellm proxy server is never run. Constraint relaxed from `>=1.75.3` to `>=1.83.0` to track future fixed releases as they become resolvable against `crewai~=1.14.x`.

## [2.1.0] — 2026-04-26

### Added
- **Consolidated report stylesheet** (`templates/css/report.css`, ~1100 lines): single source of truth for all rendered HTML reports. Inlined at render time by `TemplateManager` so reports stay self-contained for email. Replaces the inline `<style>` blocks formerly scattered across 19 renderers + the universal template (#83).
- **Print-optimized typography** in `ui_theme.py`: Arial Nova Light (with system fallbacks) as `--font-family-base`, plus a `@media print` block that forces `html { font-size: 9pt }` and adds page-break protections on sections, tables, articles. Drastically reduces page count when printing reports (#83).
- **Theme CSS variables**: `--accent-color`, `--link-color`, `--text-muted`, `--subheader-color` for both light and dark themes (previously referenced by renderers without fallback). All renderer-specific styles now consume these vars (#83).
- **Email send observability** in `main.py::send_email`: payload log (recipient, subject, attachment, output_file) before kickoff, parsed `PostResult` log after kickoff (status, recipient, error_message). Replaces bare `print()` / stdlib `logging.getLogger` that bypassed the loguru sink (#84).
- **ADR-011**: Architecture Decision Record for the consolidated CSS source pattern.

### Changed
- **`PostCrew`** now uses loguru exclusively for tool-loading and fallback diagnostics, with explicit `🔧 Loading Gmail send tools from Composio...` and `✅ Loaded N Gmail send tools: [...]` traces (#84).
- **`generate_rss_weekly_html_report`** accepts both the canonical `RssWeeklyReport` shape and the legacy `RssFeeds` shape via runtime double-validation. Re-raises on validation failure instead of swallowing the exception (#85).
- **`generate_rss_weekly`** wraps the HTML generation step in `try/except` and only marks `state.output_file` on actual success — no more "✅ pipeline complete" lies when the HTML write failed (#85).
- **`send_email`** drops the attachment from `email_inputs` if the file does not exist on disk, so the email is sent body-only rather than wasting minutes in the Composio agent (#85).
- **`pyproject.toml`** runtime dependencies trimmed from 70 → 51 entries, organized into commented logical sections (core CrewAI, pydantic/data, HTTP/web, scraping, rendering, numerical/plotting). Dev/test tooling moved into `[project.optional-dependencies] test` and `[dependency-groups] dev` (#86).

### Fixed
- **RSS weekly HTML report** rendered an empty body (only title + summary) because `RssWeeklyRenderer` did not handle the canonical `feeds` top-level shape and used wrong article keys (`url`/`date`/`source` instead of `link`/`published`/`source_feed`). Now renders all articles across all feed digests with working links and parsed HTML summaries (#85).
- **Stdlib import shadowing risk**: removed `pathlib>=1.0.1` (deprecated Py2 backport) from runtime deps. Also removed `shutils`, `unicode`, `suppress` — declared but never imported, mostly Py2 fossils (#86).

### Removed
- Inline `<style>` blocks (~2200 lines of CSS) from 19 renderers — they now emit only semantic HTML with class names, the styling lives in `report.css` (#83).
- 4 unused/Py2-fossil packages: `pathlib`, `shutils`, `unicode`, `suppress` (#86).

## [Unreleased] — Epic News v2.0 Migration

### Added
- **ADR-001 through ADR-010**: Architecture Decision Records covering model selection, scoped memory, search migration, flow orchestration, HTML rendering, real-time retrieval, JSON standardization, Pydantic models, Composio integration, and UV package management
- **PRD-federated-html**: Product Requirements Document for CSS theme centralization
- **Federated HTML theme**: Single source of truth for CSS variables in `src/epic_news/config/ui_theme.py` with `generate_theme_css()` injected into templates at render time
- **Scoped memory**: Per-agent memory isolation via `LLMConfig.get_memory_config()` with `.scope()` — enabled for `fin_daily` and `meeting_prep` crews
- **Opt-in `reasoning_effort`**: Support for Magistral model reasoning via `LLM_REASONING_EFFORT` env var, passed through `model_kwargs`
- **CHANGELOG.md**: This file

### Changed
- **Default LLM**: Migrated from `openrouter/xiaomi/mimo-v2-flash:free` to `openrouter/mistralai/mistral-small-2603` (ADR-001)
- **Search provider**: Replaced `SerperDevTool` with `PerplexitySearchTool` as primary search across all crews (ADR-003)
- **Ruff config**: Added `fix = true` for automatic safe-fix application on lint
- **Template rendering**: `universal_report_template.html` now uses `{{ theme_css_vars }}` placeholder instead of hardcoded CSS variables

### Fixed
- **`CodeInterpreterTool` import**: Removed from `deep_research` crew (no longer exported by `crewai_tools`)
- **`langchain` import**: Replaced with `crewai.tools.BaseTool` in `data_centric_tools.py` (bare `langchain` not installed)

### Removed
- `SerperDevTool` as default search provider (kept as fallback in `HybridSearchTool` cascade)
- `CodeInterpreterTool` usage (replaced by built-in `allow_code_execution=True`)
- `langchain.tools.BaseTool` import (unnecessary — `crewai.tools.BaseTool` sufficient)
- **Scoped memory feature**: Removed `LLMConfig.get_memory_config()` and all `memory=` wiring from `fin_daily` and `meeting_prep` crews. CrewAI's default `Memory` hardcoded `llm='gpt-4o-mini'`, leaking an unused OpenAI dependency. The feature was opt-in and not productively used. ReceptionFlow's auto-spawned Flow memory is now overridden with our OpenRouter LLM and `read_only=True`. ADR-002 marked Superseded.

## [0.5] — 2025-08-11

### Added
- Pydantic output validation for all crews with parallel task execution
- Pydantic validators to handle LLM output variations
- OSINT specialized HTML renderers and consolidated report
- Comprehensive API keys reference documentation
- Documentation reorganized using Diataxis framework
- Mypy type checking in pre-commit and GitHub Actions
- Claude Code Review and PR Assistant GitHub workflows

### Changed
- OSINT crew: replaced `SerperDevTool` with `HybridSearchTool`, reduced agent count
- Python 3.13 upgrade with modern union syntax (`X | None`, `X | Y`)
- All mypy type errors resolved (zero errors achieved)
- Ruff UP047 fixes and code formatting applied
- Hierarchical CLAUDE.md files for better AI context

### Fixed
- `generate_osint` made async to work within CrewAI event loop

### Security
- Replaced MD5 with SHA-256 for event ID generation

## [0.4] — 2025-07-04

### Changed
- Consolidated HTML rendering through `TemplateManager`, removed legacy renderers
- JSON output standardization (PR-001), scraper consolidation (PR-002), rendering lint (PR-004)
- Added `workflow_dispatch` trigger to all Docker publish workflows

## [0.3] — 2025-07-04

### Added
- Combined Docker setup with supervisor for FastAPI and Streamlit
- Deep research crew with 4-agent architecture (strategist, collector, analyst, writer)
- PhD-level and ultra-comprehensive research flows
- Extractors package for structured crew output parsing
- Nutritional information requirement for menu generation

### Changed
- Imports reorganized to use `epic_news` namespace
- Removed unused and deprecated code in `src/` (Fixes #22)

## [0.2.2-alpha] — 2025-07-23

### Changed
- Docker and namespace improvements

## [0.2.1-alpha] — 2025-07-17

### Added
- Deep research flows with PhD-level academic research
- Extractors package for crew output parsing

## [0.2.0-alpha] — 2025-06-30

### Added
- Menu designer crew with structured HTML output and Pydantic models
- Menu plan validation and error recovery system
- Email sending with PostCrew and financial report integration
- Cross-reference report HTML generation
- Holiday planner HTML rendering system overhaul
- Company news renderer with comprehensive HTML tests
- Observability: tracing integration into core application flow
- Meeting prep crew output files
- Loguru logging (replaced standard `logging`)
- Advanced testing libraries (Faker, pytest-mock)
- Project-level TODO list for development planning

### Changed
- All crews refactored to comply with development guide (Two-Agent Pattern)
- Modular Pydantic models and structured outputs across all crews
- HTML rendering reorganized with new template system
- Documentation refactored and consolidated (Diataxis)
- Tests converted from `unittest.mock` to `pytest-mock`

### Removed
- `MarketingWritersCrew` and all associated code

## [0.1.2-alpha] — 2025-06-22

### Changed
- CI/CD improvements for GitHub Actions

## [0.1.1-alpha] — 2025-06-22

### Added
- New services and `.env` file creation
- Simplification and cleanup

## [0.1.0-alpha] — 2025-06-22

### Added
- Initial release with CrewAI-based multi-agent architecture
- ReceptionFlow orchestration pattern with crew dispatch
- 24+ specialized crews (financial, news, research, planning, content)
- HTML report generation with dark mode support
- OpenRouter LLM integration via `LLMConfig`
- Tool ecosystem (70+ tools: search, finance, scraping, RAG)
- Composio integration for external services (Gmail, Slack, Reddit)
- MCP server support (Wikipedia)
- FastAPI and Streamlit interfaces
- Docker deployment support
- pytest test suite with structure and rendering tests
