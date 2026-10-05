# ADR-005: Deterministic HTML Rendering Over LLM-Based Generation

## Status

Superseded by [ADR-017](ADR-017-docx-only-reports.md) (2026-10-05). It was accepted and amended on 2026-10-04; reports are now DOCX only and the HTML renderers described below are gone.

Historical note, kept as written at the time of the amendment:

- There are no per-crew `*_to_html()` factories. Flow methods call `render_and_write_html(selected_crew, model, html_path)` (`utils/flow_helpers.py`), which calls `TemplateManager().render_report(selected_crew=..., content_data=...)` and refuses paths outside `output/` ([ADR-015](ADR-015-output-trust-boundary.md)).
- The holiday planner produces DOCX only; its HTML renderer was removed.
- LLM- and web-derived text is escaped or sanitised before it reaches the HTML (ADR-015).
- With `output_pydantic`, the two-agent split is no longer needed to keep action traces out of reports; it is kept so the reporting agent has no tools.

## Context

Early crew implementations asked LLMs to generate HTML directly in task output. This produced inconsistent styling, broken markup, and action traces (tool call logs) embedded in the HTML output. Reports needed predictable structure and consistent theming.

## Decision

- Render all HTML programmatically in Python using BeautifulSoup, not via LLM output
- Pipeline: Crew result → Pydantic model validation → `*_to_html()` factory → `TemplateManager.render_report()` → `BaseRenderer` subclass
- Each crew has a dedicated renderer extending `BaseRenderer` in `template_renderers/`
- `RendererFactory` selects the appropriate renderer; `GenericRenderer` as fallback
- Use the two-agent pattern (researcher with tools, reporter without) to keep output clean

## Consequences

- Consistent HTML structure and styling across all 17+ crew report types
- Dark mode, theming, and layout changes apply universally via CSS variables
- Pydantic models enforce data contracts between crews and renderers
- Adding a new crew renderer follows a clear pattern (extend `BaseRenderer`, register in factory)
- LLM creativity is channeled into content, not markup — separation of concerns
