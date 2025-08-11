# PR-005 — HTML/Report Simplification and Consolidation

- Status: Draft
- Author: Cascade
- Date: 2025-08-10
- Related: PR-001 (JSON Output Standard), PR-002 (Scraper Consolidation), PR-003 (Flow & Reporting Enforcement), PR-004 (Rendering Snapshot Tests)

## Motivation

Reduce overengineering and redundancy in the HTML/report generation layer to align with project principles (KISS, YAGNI, DRY) and the consolidated rendering architecture based on `TemplateManager` and `RendererFactory`.

## Current State (Overview)

Multiple, overlapping ways to generate HTML:

- `TemplateManager` + `RendererFactory` (preferred) in `src/epic_news/utils/html/template_manager.py` and `.../template_renderers/`.
- Legacy factory wrappers in `src/epic_news/utils/html/*_html_factory.py` that often instantiate `TemplateManager` and call `render_report()`.
- `RenderReportTool` in `src/epic_news/tools/render_report_tool.py` (Jinja2-driven, separate template).
- `ReportingTool` in `src/epic_news/tools/reporting_tool.py` (string substitution on separate template).
- Helpers in `src/epic_news/utils/html/templates.py` for menu/shopping, overlapping with dedicated renderers.
- A broken, unused `UniversalReportTool` in `src/epic_news/tools/universal_report_tool.py` importing a non-existent `render_universal_report`.

Crews commonly import a bundle from `get_report_tools()` which currently returns both `RenderReportTool` and `ReportingTool`.

## Findings

- __[redundant layers]__ Several parallel HTML paths create confusion and maintenance overhead.
- __[dead/broken tool]__ `UniversalReportTool` is unused and imports a missing function.
- __[duplicate tools]__ `ReportingTool` duplicates functionality (simpler API) alongside `RenderReportTool`.
- __[legacy wrappers]__ `*_html_factory.py` wrappers add minimal value over directly using `TemplateManager`/renderers.
- __[overlap]__ `templates.py` menu/shopping helpers overlap with `menu_renderer.py` and `shopping_renderer.py`.
- __[imports]__ `src/epic_news/main.py` still imports many `*_html_factory` functions.

## Goals

- Single, clear rendering pathway for all crews via `TemplateManager` and `RendererFactory`.
- Remove unused/broken modules.
- Deprecate thin wrappers and duplicated tools.
- Keep tests green (snapshot tests in place) and preserve public behavior where required.

## Non-Goals

- Changing the unified HTML template visuals.
- Removing `RenderReportTool` at this time (used by crews via `get_report_tools()`).

## Proposed Changes

### Minimal, Safe First Patch

1) Remove `src/epic_news/tools/universal_report_tool.py` (unused and broken import).
2) Update `src/epic_news/tools/report_tools.py` to only include `RenderReportTool()` (drop `ReportingTool()` from the bundle).
3) Add `DeprecationWarning` in each `src/epic_news/utils/html/*_html_factory.py`, pointing consumers to `TemplateManager`/renderers.

### Next Patch (Consolidation)

4) Update `src/epic_news/main.py` to stop importing `*_html_factory` modules, use `TemplateManager().render_report(selected_crew, content_data)` (or direct renderer) instead.
5) Deprecate/remove overlapping helpers in `src/epic_news/utils/html/templates.py` (`render_menu_report()`, `render_shopping_list()`), since renderers exist.
6) Migrate any remaining tests that import factories to use `TemplateManager` and renderer paths. Snapshot tests already exercise `TemplateManager`.

## Migration Plan

- Phase 1 (PR-005.1): Apply Minimal Patch, keep CI green. Announce deprecations.
- Phase 2 (PR-005.2): Update `main.py` and tests; remove legacy imports.
- Phase 3 (PR-005.3): Remove deprecated helpers and (after grace period) delete legacy factory files.

## Risks & Mitigations

- Risk: Hidden runtime dependency on legacy factories.
  - Mitigation: Start with DeprecationWarnings; search/grep across codebase; adjust `main.py` and tests in Phase 2.
- Risk: Crew tools expecting `ReportingTool`.
  - Mitigation: `get_report_tools()` will standardize on `RenderReportTool`, which is already in use; update crew bundles if needed.
- Risk: Snapshot drift.
  - Mitigation: Leverage `pytest-regressions` snapshots; normalize volatile fields; update snapshots only when expected.

## Impacted Files (examples)

- `src/epic_news/tools/universal_report_tool.py` (remove)
- `src/epic_news/tools/report_tools.py` (remove `ReportingTool` from bundle)
- `src/epic_news/tools/reporting_tool.py` (deprecate, then remove)
- `src/epic_news/utils/html/*_html_factory.py` (add DeprecationWarning; later remove)
- `src/epic_news/utils/html/templates.py` (deprecate overlapping helpers)
- `src/epic_news/main.py` (stop importing factories; call `TemplateManager`/renderers)

## Test Plan

- Run full test suite.
- Ensure snapshot tests in `tests/rendering/test_template_manager_rendering.py` pass.
- Add targeted tests for `get_report_tools()` bundle behavior (now only `RenderReportTool`).
- Grep checks to ensure no remaining imports of factory modules in production code after Phase 2.

## Acceptance Criteria

- All crews capable of generating HTML via `TemplateManager`/renderers.
- No usage of `UniversalReportTool`.
- `get_report_tools()` returns only `RenderReportTool` (and `HtmlToPdfTool` when available).
- No production code depends on `*_html_factory.py` wrappers.
- CI passes with stable snapshot tests.

## Rollback Plan

- Revert to previous bundle in `get_report_tools()` and restore removed files if critical blocking issues arise.

## References

- `src/epic_news/utils/html/template_manager.py`
- `src/epic_news/utils/html/template_renderers/renderer_factory.py`
- `src/epic_news/tools/report_tools.py`
- `src/epic_news/tools/render_report_tool.py`
- `src/epic_news/tools/reporting_tool.py`
- `src/epic_news/main.py`
- `src/epic_news/utils/html/templates.py`
- `src/epic_news/utils/html/*_html_factory.py`
