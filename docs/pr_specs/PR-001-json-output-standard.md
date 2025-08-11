# PR-001: Tool Output Standardization – JSON Strings Only

## Summary

Standardize all agent tools to return JSON strings (UTF-8) instead of Python dicts or model objects. Add a lightweight helper to ensure compliance and refactor violating tools. This reduces downstream ambiguity, aligns with existing Yahoo/Hunter/Serper tools, and prevents raw Python objects from leaking into prompts or HTML.

## Motivation

- Current inconsistency: some tools return dicts/models (`data_centric_tools.py`, parts of `rss_feed_tool.py`), while others return JSON strings (Yahoo Finance, Hunter, Serper).
- LLM prompts and final reporting agents expect JSON strings for deterministic parsing and rendering.
- Prevents accidental repr leakage into crews and HTML.

## Scope

- Introduce `ensure_json_str()` helper (or `JsonReturningToolMixin`) used by tools’ `_run()`.
- Refactor violating tools to return JSON strings.
- Add tests validating all tools return a JSON string that loads with `json.loads`.
- Adopt resilient HTTP stack for tools that call external APIs: `httpx` for requests, `tenacity` for retries/timeouts, and `requests-cache` where existing tools still use `requests` (HTTP caching for those paths). New code should prefer `httpx` + retry logic; caching can be added via a thin TTL cache wrapper if not using `requests`.

## Non-Goals

- Changing tool business logic or inputs.
- Modifying crews’ prompts beyond necessary parsing notes.

## Detailed Changes

- Add `src/epic_news/tools/_json_utils.py`
  - `def ensure_json_str(obj: Any) -> str`: returns `obj` if it’s a JSON-looking string; else `json.dumps(obj, ensure_ascii=False)`; fallback to `json.dumps({"result": str(obj)})`.
- Update tools:
  - `src/epic_news/tools/data_centric_tools.py`
    - `MetricsCalculatorTool._run`: wrap `metric.model_dump()` with `ensure_json_str`.
    - `KPITrackerTool._run`: wrap `kpi.model_dump()` with `ensure_json_str`.
    - `DataVisualizationTool._run`: wrap `series.model_dump()` / `table.model_dump()` and error dicts with `ensure_json_str`.
    - `StructuredReportTool._run`: wrap `report.model_dump()` and error dicts with `ensure_json_str`.
  - `src/epic_news/tools/rss_feed_tool.py`
    - Ensure the top-level `_run()` returns `ensure_json_str(...)` for the final payload. Internal helpers may keep returning dicts.
- HTTP resilience & reuse:
  - Add `src/epic_news/utils/http.py` providing shared `httpx` clients (sync/async) with sane defaults (timeouts, headers) and `tenacity` retry wrappers for transient failures.
  - Enable `requests-cache` for tools that still rely on `requests` during the transition (configurable TTL, cache path). Document migration to `httpx` over time.

## Files Touched

- Add: `src/epic_news/tools/_json_utils.py`
- Add: `src/epic_news/utils/http.py`
- Modify: `src/epic_news/tools/data_centric_tools.py`
- Modify: `src/epic_news/tools/rss_feed_tool.py`
- Modify: `pyproject.toml` to include `httpx`, `tenacity`, and `requests-cache` dependencies
- Tests: `tests/tools/test_json_outputs.py`, `tests/tools/test_http_resilience.py`

## Compatibility & Migration

- Backward compatible: existing consumers reading strings remain unaffected.
- Any downstream that depended on Python dicts should call `json.loads()` explicitly.

## Testing Strategy

- Unit tests for `ensure_json_str()` edge cases (dict/list/str/None/custom objects).
- Parametrized test across all tools in `epic_news.tools` to assert `isinstance(res, str)` and valid JSON when applicable.
- Golden tests for `data_centric_tools.py` to confirm schema fields preserved after serialization.
- HTTP resilience tests: simulate transient 5xx/network errors and assert retries/backoff with `tenacity` wrappers; verify caching layer prevents duplicate calls on identical inputs (where `requests-cache` is enabled). Use pytest monkeypatch or a lightweight stub server to avoid live calls.

## Rollout Plan

- Land helper and tool refactors.
- Run `crewai flow kickoff` for FinDaily/NewsDaily/ShoppingAdvisor to validate end-to-end.

## Risks & Mitigations

- Risk: Downstream code expects dicts. Mitigation: search-and-update; add explicit parsing in consumers.
- Risk: Non-JSON serializable types. Mitigation: fall back to `str(obj)` wrapper in `ensure_json_str` and add logging.

## Documentation

- Update `docs/2_TOOLS_HANDBOOK.md` with “All tools MUST return JSON strings”.
- Add note in `README.md` Advanced Usage (Tools) about JSON outputs.
- Add a dedicated "Testing" section in `README.md` with commands to run the full suite and PR-001-specific tests.
- Explicitly document test files:
  - `tests/tools/test_json_outputs.py`
  - `tests/tools/test_http_resilience.py`
