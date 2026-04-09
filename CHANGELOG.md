# Changelog

All notable changes to Epic News are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
