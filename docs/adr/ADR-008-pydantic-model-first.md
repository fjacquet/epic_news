# ADR-008: Pydantic-First Model Design for Crew Outputs

## Status

Accepted

## Context

Crew outputs were initially unstructured text that downstream consumers (HTML renderers, API endpoints, email formatters) had to parse heuristically. This led to brittle string matching, inconsistent data extraction, and rendering failures when LLM output format varied slightly.

## Decision

- Define explicit Pydantic models for every crew's structured output in `src/epic_news/models/crews/`
- Use `output_pydantic=MyModel` on the final task of each crew for automatic validation
- Use Python 3.13 union syntax (`X | None`, `X | Y`) — enforced by ruff UP007/UP035/UP045
- Models serve as the contract between crew execution and downstream consumers (renderers, APIs)
- 21 crew-specific models currently defined

## Consequences

- Type safety from crew output through rendering pipeline
- LLM output that doesn't match the schema fails fast with clear validation errors
- Renderers receive guaranteed data structure — no defensive parsing needed
- IDE autocompletion and static analysis work across the full pipeline
- Adding validators (e.g., for French text escaping) fixes issues at the model layer for all consumers
