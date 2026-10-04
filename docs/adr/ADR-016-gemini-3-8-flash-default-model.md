# ADR-016: Gemini 3.8 Flash as the Default Model

## Status

Accepted (2026-10-04). Supersedes [ADR-001](ADR-001-mistral-small-4.md).

## Context

ADR-001 made `openrouter/mistralai/mistral-small-2603` the default model. The project has since run on Google Gemini 3.8 Flash through LiteLLM's native Gemini route (`MODEL=gemini/gemini-3.8-flash`). Gemini 3 behaves differently from the models the configuration was written for:

- Google and LiteLLM recommend keeping temperature at its 1.0 default; lower values can cause looping and degraded reasoning. LiteLLM sets 1.0 itself when no temperature is sent.
- Without `reasoning_effort`, LiteLLM sends no `thinking_level`, so the API default applies (`high` for Gemini 3 Flash): maximum thinking cost and latency on every call.
- Gemini can return thought-only turns with empty text, which CrewAI's ReAct loop treats as an empty response.

## Decision

- Gemini 3.8 Flash on the native `gemini/` route is the default model, set with `MODEL` in `.env`.
- `LLMConfig.get_openrouter_llm()` omits the env-derived temperature for any model whose name contains `gemini`, whatever the route prefix (`gemini/`, `openrouter/google/`, `vertex_ai/`). An explicit caller value is still sent.
- When `LLM_REASONING_EFFORT` is unset, Gemini 3 models get `reasoning_effort="medium"` (mapped by LiteLLM to `thinking_level: medium`).
- Empty responses are retried at most `LLM_EMPTY_RETRIES` times (default 2) with exponential backoff and jitter.
- Gemini authenticates with `GEMINI_API_KEY`. LiteLLM reads `GOOGLE_API_KEY` first, so when the Fact Check key is also set it pays for Gemini calls; the code does not override this.
- OpenRouter remains supported for any `openrouter/...` model, with reasoning sent through `extra_body.reasoning`.

## Consequences

- Lower thinking cost and latency than the API default, with predictable behaviour.
- Switching models stays a `.env` change; the Gemini-specific rules apply automatically.
- The fallback constant (`_DEFAULT_MODEL` in `src/epic_news/config/llm_config.py`) and `MODEL` in `.env.example` were aligned to `gemini/gemini-3.8-flash` in #219, so a fresh checkout matches this decision. `.env.example` keeps `openrouter/mistralai/mistral-small-2603` as the commented OpenRouter alternative.
- Key precedence (`GOOGLE_API_KEY` before `GEMINI_API_KEY`) must be handled in `.env`, not in code.
