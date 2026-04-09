# ADR-001: Migration to Mistral Small 4 on OpenRouter

## Status

Accepted

## Context

The project used `openrouter/xiaomi/mimo-v2-flash:free` as default LLM. While free, this model has limited context windows and reasoning capabilities. Mistral Small 4 (`mistral-small-2603`) offers better quality at low cost via OpenRouter.

## Decision

- Change default model to `openrouter/mistralai/mistral-small-2603`
- Add opt-in `reasoning_effort` parameter (for Magistral models)
- Pass `reasoning_effort` through `model_kwargs` to LiteLLM/OpenRouter
- Only send `reasoning_effort` when explicitly configured (not "none" or empty)

## Consequences

- Better output quality for all crews
- Small per-token cost (no longer free tier)
- `reasoning_effort` ready for future Magistral model adoption
- All existing crews work without changes (model selection via `LLMConfig`)
