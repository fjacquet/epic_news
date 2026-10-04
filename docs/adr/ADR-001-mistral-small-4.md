# ADR-001: Migration to Mistral Small 4 on OpenRouter

## Status

**Superseded (2026-10-04)** by [ADR-016](ADR-016-gemini-3-8-flash-default-model.md) — the default model is now Gemini 3.8 Flash on the native `gemini/` route. The opt-in `reasoning_effort` described below is now sent through `extra_body.reasoning` on OpenRouter routes, because LiteLLM drops a top-level `reasoning_effort` for models it does not know support reasoning (Magistral).

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
