# PR-004: Rendering Consistency, Lint/Imports Enforcement, and Documentation

## Summary

Standardize HTML rendering through `TemplateManager` + `RendererFactory`, enforce import placement and lint rules, and update documentation. Add regression tests to prevent reintroduction of empty content, raw objects, or stray Jinja syntax.

## Motivation

- Past issues: direct rendering calls from orchestration, leftover Jinja tags, raw Python objects leaking into HTML, mixed render paths.
- Consistency improves reliability across crews (FinDaily, NewsDaily, ShoppingAdvisor, etc.) and aligns with the project’s “Light as a Haiku” standards.

## Scope

- Align all crews to use the deterministic rendering pipeline.
- Enforce imports-at-top and style via Ruff/isort.
- Add pre-commit hooks and CI checks.
- Update core docs (developer + tools) to codify standards.
- Add HTML snapshot testing using `pytest-regressions` or `syrupy` to lock report structure and prevent regressions.

## Non-Goals

- Redesigning templates or CSS beyond necessary fixes.

## Detailed Changes

- Rendering unification:
  - Ensure all renderers route through `TemplateManager` + `RendererFactory` (e.g., `render_universal_report()`), using placeholders `report_title`, `report_body|safe`, `generation_date`.
  - Remove any string-based Jinja replacements; rely on Jinja2 rendering only.
  - Verify UTF-8 and emoji support across templates and outputs.
  - Confirm NewsDaily fallback logic and Financial/ShoppingAdvisor renderers follow the deterministic pattern already validated.
- Linting & imports:
  - Update `pyproject.toml` Ruff settings to enforce: imports at top (E402), unused imports, complexity, formatting (compatible with Black) and isort import ordering.
  - Add `.pre-commit-config.yaml` to run Ruff (and optionally Black/isort) + simple repo greps for forbidden calls (paired with PR-003 script).
- Tests:
  - Add `tests/rendering/test_html_reports.py`:
    - Load sample JSON outputs (FinDaily, NewsDaily, ShoppingAdvisor) and assert generated HTML:
      - Contains a single `<html>` document, `<head>`, `<body>`, a non-empty title, generation date.
      - No `{% ... %}` or `{{ ... }}` artifacts remain.
      - No Python reprs like `StructuredDataReport(` or `Metric(`.
    - Smoke test dark mode CSS class presence if applicable.
  - Add snapshot assertions using `pytest-regressions` (file_regression) or `syrupy` to compare rendered HTML against golden snapshots per crew.

## Files Touched

- Modify: `src/epic_news/template_manager.py` and any renderer modules to ensure consistent entry points.
- Modify: crew code paths that bypass the factory/manager (if any remain).
- Modify: `pyproject.toml` (Ruff/isort), add `.pre-commit-config.yaml`.
- Add tests: `tests/rendering/test_html_reports.py` and fixtures under `tests/fixtures/`.
- Docs: `docs/1_DEVELOPMENT_GUIDE.md`, `docs/2_TOOLS_HANDBOOK.md`, `docs/3_ARCHITECTURAL_PATTERNS.md`, `README.md` (Advanced Usage).
- Add dev dependencies: `pytest-regressions` (or `syrupy`) in `pyproject.toml`.

## Compatibility & Migration

- Backward compatible; existing crews benefit from consistent rendering. Any ad-hoc render paths are migrated to the unified pipeline.

## Testing Strategy

- Unit: verify renderer functions and template placeholders.
- Integration: end-to-end `crewai flow kickoff` for FinDaily, NewsDaily, ShoppingAdvisor produce valid HTML checked by tests.
- Static: Ruff/isort checks; pre-commit ensures local compliance.
- Snapshot: for each crew, assert rendered HTML matches the committed snapshot; provide an opt-in flag to update snapshots when intentional changes occur.

## Rollout Plan

- Land lint/format configs and tests.
- Update renderer paths as needed.
- Run flows and validate outputs in `output/`.

## Risks & Mitigations

- Risk: Overly strict lint causing noise. Mitigation: start with essential rules (E402, F401/F841, I001 isort), expand later.
- Risk: Template regressions. Mitigation: golden/snapshot tests for key crews.

## Documentation

- Update developer and architectural docs to describe:
  - Deterministic rendering pipeline and placeholders.
  - Import rules and lint expectations.
  - Pre-commit usage and CI expectations.
