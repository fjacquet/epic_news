# PR-003: Flow Kickoff-Only and Tool-less Reporting Enforcement

## Summary

Enforce architectural rules across all crews:

- Kickoff-only orchestration (no direct calls to internal renderer/crew methods from outside the flow).
- Two-agent pattern where the final reporting agent has `tools=[]` and runs synchronously.
- Ensure all final outputs are rendered via `TemplateManager` + `RendererFactory`.

## Motivation

- Past regressions included direct calls like `HtmlDesignerCrew.render_unified_report` from orchestration, breaking CrewAI flow.
- Consistent two-agent pattern improves maintainability and predictability.
- Ensures high-quality, deterministic HTML outputs per standards.

## Scope

- Add a small helper for flow kickoff to centralize orchestration calls.
- Audit and fix crews to ensure final reporting agents have no tools and the final task is synchronous.
- Light CI/static checks preventing direct render calls from non-renderer modules.
- Add tracing around CrewAI flows and tool invocations using Langfuse to observe runs, prompts, costs, and errors.

## Non-Goals

- Changing crew business logic or prompts, unless needed for compliance.

## Detailed Changes

- Add: `src/epic_news/utils/flow_enforcement.py`
  - `def kickoff_flow(crew, context: dict) -> dict`: wrapper to call `crew.kickoff()`/`crewai flow kickoff` path, handle logging, and forbid internal method calls.
- Add: `src/epic_news/utils/tracing.py`
  - Initialize Langfuse client from env (e.g., `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`).
  - Context managers/decorators to trace `kickoff_flow`, agent runs, and tool `_run()` calls with metadata (crew name, agent, task, duration, status).
- Crew audits and fixes:
  - `src/epic_news/crews/**`: ensure final agent definitions have `tools: []` and the final task is synchronous. Specific checks for FinDaily, NewsDaily, CompanyNews, ShoppingAdvisor, WebPresence, TechStack, LegalAnalysis, HRIntelligence, GeospatialAnalysis.
- Add CI check:
  - Simple script `scripts/ci/check_no_direct_renderer_calls.py` scanning for forbidden patterns like `.render_unified_report(`, `TemplateManager.render_*(` usage outside renderer modules.

## Files Touched

- Add: `src/epic_news/utils/flow_enforcement.py`
- Add: `src/epic_news/utils/tracing.py`
- Add: `scripts/ci/check_no_direct_renderer_calls.py`
- Modify: crew files under `src/epic_news/crews/**` where needed (final agent tools empty, final task sync).
- Docs: `docs/3_ARCHITECTURAL_PATTERNS.md` and `docs/1_DEVELOPMENT_GUIDE.md` to codify rules.
- Modify: `pyproject.toml` to include `langfuse` client dependency and document required env vars.

## Compatibility & Migration

- Backward compatible: crews already following the pattern are unchanged.
- For crews with tool-enabled final agents, remove tools and, if necessary, move tool usage to upstream research agent tasks.

## Testing Strategy

- Unit: test `kickoff_flow` wrapper doesn’t allow internal-renderer calls and forwards context correctly.
- Integration: run `crewai flow kickoff` for FinDaily, NewsDaily, ShoppingAdvisor and assert final agents are tool-less and synchronous.
- Static: CI script fails the build if forbidden calls appear outside renderer modules.
- Tracing: integration test initializes Langfuse in a test env (or mocked client) and asserts spans/attributes for kickoff and tool calls are recorded.

## Rollout Plan

- Land helper + CI check.
- Apply crew fixes.
- Validate main flows.

## Risks & Mitigations

- Risk: False positives in static check. Mitigation: whitelist `src/epic_news/template_manager.py` and renderer modules.
- Risk: Some crews rely on tools in final step. Mitigation: migrate tool calls to preceding agent.

## Documentation

- Update `docs/3_ARCHITECTURAL_PATTERNS.md` to explicitly state kickoff-only and tool-less final agent requirements.
- Add checklist to `docs/1_DEVELOPMENT_GUIDE.md` for contributors.
