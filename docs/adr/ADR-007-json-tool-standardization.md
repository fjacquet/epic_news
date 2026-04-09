# ADR-007: JSON String Standardization for Tool Outputs

## Status

Accepted

## Context

CrewAI tools return their `_run()` output as strings that LLM agents parse. Early tools returned Python repr strings, markdown, or inconsistent formats. Agents wasted tokens and iterations trying to parse these varied outputs, sometimes hallucinating structure.

## Decision

- All tool `_run()` methods must return JSON strings parseable by `json.loads()`
- Centralized helpers in `src/epic_news/tools/_json_utils.py` (`ensure_json_str()`, `safe_json_dumps()`)
- Tools returning lists wrap them in `{"results": [...]}` envelopes
- Error responses use `{"error": "message", "status": "failed"}` format
- Enforced by code review and documented in `src/epic_news/tools/CLAUDE.md`

## Consequences

- Agents parse tool output reliably on the first attempt
- Reduced token waste from retry loops on malformed output
- Consistent error handling across all 70+ tools
- New tool authors have a clear contract to follow
- Pydantic models can validate tool output directly via `model_validate_json()`
