# ADR-005: Deterministic HTML Rendering Over LLM-Based Generation

## Status

Accepted

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
