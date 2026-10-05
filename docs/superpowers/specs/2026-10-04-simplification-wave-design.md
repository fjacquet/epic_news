# Simplification Wave — Design

**Date:** 2026-10-04
**Status:** Approved for planning (after the efficiency wave)
**Source:** codebase audit 2026-10-04 (simplification section), re-measured on `main` at `649e877`

## Problem

After the cleanup PRs (#215–#222) the dead code is gone, but the live code still repeats
itself and hides behaviour in long functions:

| Area | Today |
|---|---|
| `main.py` | 1,723 lines, maintainability index 24; 16 `generate_*` methods (19–141 lines); `_run_osint_parallel` 133, `send_email` 102 |
| Routing | crew keys live in `CrewCategories`, the `determine_crew` if-chain (45 lines), the `or_(...)` listener list, `TemplateManager` titles and `RendererFactory` — and they already disagree (e.g. no COMPANY_NEWS title, "RSS" vs "RSS_WEEKLY") |
| Crews | 26 crew modules, 2,637 lines; `LLMConfig.get_openrouter_llm` ×63 and `max_iter=` ×62 repeated by hand; 352 `type: ignore` in crews (597 in `src`); 12 crew modules call `load_dotenv()` at import |
| Parsing | `parse_crewai_output` cyclomatic complexity 49 (F), branching on model class names; home-grown JSON repair |
| Deep research | `DeepResearchExtractor._adapt_json_to_model` complexity 40; extractor package (412 lines) used by one crew |
| Rendering | 27 renderer files, 5,995 lines; header code copied between renderers; `TemplateManager` stateful, swallows renderer errors into an "Erreur" page that can be emailed |
| State | `content_state.py` 352 lines with duplicated per-crew result fields, some mistyped |
| Menu | 5 layers (flow, `services/menu_designer_service.py`, `menu_generator.py` complexity 22, validator, crews); the service swallows errors so the flow's fallback never runs |
| Misc | `kickoff_flow` / `akickoff_flow` near-duplicates; ~330 lines of CrewAI monkeypatches inside `llm_config.py` (585 lines); `observability.py` 524 lines with mostly unused Tracer/Dashboard |

## Goals

1. One source of truth for crew keys, titles, renderers and output paths, while every crew
   stays an explicit Flow step.
2. `main.py` ≤ 1,350 lines (every crew keeps its own Flow step); no function above
   complexity 20 (radon D) in `src`.
3. Crew modules in CrewAI's documented form without `type: ignore` noise; `type: ignore` in
   crews −80%.
4. Behaviour preserved: every PR is a refactor proven by tests, except where noted.

## Non-goals

- Performance changes (efficiency wave).
- New features, new crews, prompt changes.
- Replacing CrewAI decorators (`@CrewBase`, `@agent`, `@task`, `@crew`) — helpers are called
  inside them.

## Design

### S1 — CrewAI-native crew cleanup (mechanical, first)

Revised 2026-10-05: no factory helpers. Every crew keeps CrewAI's documented form,
`Agent(config=self.agents_config[...], ...)` / `Task(...)` / `Crew(...)` written out inside
`@agent` / `@task` / `@crew`. A `make_agent` / `make_task` layer was considered and rejected:
it hides the CrewAI idiom behind a project-specific one.

- Each crew class types what CrewBase sets at runtime (`agents_config` / `tasks_config` as
  `dict[str, Any]`, `agents` / `tasks` as lists), removing the `index`, `arg-type` and
  `attr-defined` ignores.
- mypy's `call-arg` is disabled for `epic_news.crews.*`: CrewAI's `Task(config=...)` and
  decorated methods are untypable; the ADR-014 AST guard rejects unknown kwargs instead.
- `load_dotenv()` moves to the entry points only.
- A snapshot of every built crew's settings is recorded first and must not change.
- The ADR-014 guard tests (AST kwargs, agent contract) keep passing unchanged.
- The repeated `llm=` / `max_iter=` lines stay (they are the documented CrewAI form).

### S2 — Parsing through model validators

Move each model-specific fix in `parse_crewai_output` into a
`@model_validator(mode="before")` on that model; replace the home-grown repair with
`json_repair` (already in `uv.lock` transitively; declare it). Target: `parse_crewai_output`
≈40 lines, complexity < 10. Characterisation tests: the existing parsing fixtures plus the
recorded raw outputs under `debug/` that parse today must still parse to equal models.

### S3 — Deep research on the standard path

Merge the two `DeepResearchReport` schemas (`models/crews/deep_research.py:50`, used by the
flow, state and DOCX; `models/crews/deep_research_report.py:24`, the crew's
`output_pydantic`) into one, whose before-validator absorbs `_adapt_json_to_model`; `generate_deep_research` uses
`load_or_parse_model` + `render_and_write_html` like other crews; delete
`utils/extractors/`. Characterisation: the rendered HTML for a recorded deep-research output
is unchanged.

### S4 — Crew metadata in one place; Flow steps stay explicit

The Flow structure is not changed: every crew keeps its own `@listen` step
(`generate_poem`, `generate_pestel`, ...), `@router determine_crew` keeps returning the step
name, and `crewai flow plot` keeps one node per crew. Collapsing crews into one generic
listener was considered and rejected (2026-10-04): it hides the flow behind a dispatch
table, against the CrewAI Flow model.

What changes:

- `crew_registry.py` holds metadata only: one `CrewSpec(key, title, model_cls, json_path,
  html_path, docx_assembler)` per crew. `TemplateManager` titles, `RendererFactory` keys and
  `CrewCategories` read from it, fixing the existing drift (no COMPANY_NEWS title, "RSS" vs
  "RSS_WEEKLY"). The registry does not route and does not run crews.
- A flow helper `_run_standard(spec, crew, inputs)` holds the steps the standard crews
  repeat (kickoff → dump state → load model → `emit_report`). Each standard `generate_*`
  becomes a short, readable step that prepares its inputs and calls the helper: poem,
  news_company, findaily, news_daily, saint_daily, book_summary, meeting_prep,
  sales_prospecting, pestel. Custom steps stay fully written out for RSS, menu, recipe,
  shopping, deep research, OSINT and holiday.
- The `or_(...)` list of report steps feeding `send_email` stays explicit in the decorator.
- Existing flow wiring tests stay valid; add a test that every `CrewSpec` key has a router
  branch, a listener and a renderer.

### S5 — Rendering

- `TemplateManager` becomes a module function `render_report(key, data) -> str`; renderer
  errors propagate (the flow decides; no "Erreur" page gets emailed). **Behaviour change.**
- Shared header via `BaseRenderer.add_report_header`; drop the abstract `__init__`
  requirement.
- A spec-driven renderer (`SECTIONS = [(field, title, kind)]`) replaces the simple OSINT
  renderers (hr, legal, geospatial, web_presence, tech_stack). Large custom renderers stay.
- Characterisation: snapshot of each renderer's HTML for its fixture model before the change.

### S6 — Flow state

Replace duplicated per-crew fields in `ContentState` with `report: BaseModel | None`,
`raw_output: Any`, and `osint: dict[str, BaseModel]`; crew keys become a `StrEnum` built
from the registry. Check every reader (`app.py`, `api.py`, `send_email`) first.

### S7 — Menu

Delete the flow's unreachable fallback branch, make `parse_menu_structure` walk the typed
`WeeklyMenuPlan` (≈25 lines), fold `MenuDesignerService` into the flow and remove
`services/`. Coordinate with efficiency E3 (same code).

### S8 — Small consolidations

- `kickoff_flow` / `akickoff_flow` share one retry/trace helper.
- CrewAI monkeypatches move from `llm_config.py` to `config/crewai_patches.py`, applied once
  at the entry points, with a docstring listing what to re-check on each CrewAI upgrade.
- `observability.py`: keep only what the flow uses (`trace_task` or its replacement);
  delete unused Tracer/Dashboard/HallucinationGuard (not used outside this repo).
- Infra: drop redundant compose files and Makefile aliases (non-Python, separate PR).

## Validation

- Before each PR: characterisation tests that pin current outputs (rendered HTML, parsed
  models, routing decisions) for the code being changed.
- Each PR: full suite, ruff, mypy, ADR-014 guard tests, radon report (complexity) and a LOC
  delta in the description.
- Live run of one affected crew for S2, S3 and S4 (parsing and routing paths).

## Rollout (one PR each, in order)

1. S1 — CrewAI-native crew cleanup
2. S2 — parsing validators + `json_repair`
3. S3 — deep research standard path
4. S4 — crew metadata registry + standard-step helper
5. S5 — rendering
6. S6 — flow state
7. S7 — menu
8. S8 — small consolidations (Python), then infra (separate)

## Risks

- **Large diffs in `main.py` (S4, S6):** mitigated by one crew per commit and
  characterisation tests; the Flow graph itself does not change.
- **Parsing tolerance (S2, S3):** messy LLM output that parses today might not tomorrow;
  mitigated by replaying recorded raw outputs from `debug/`.
- **Error propagation (S5):** a renderer bug now fails the run instead of sending a broken
  page; this is intended but visible.

## Decisions (2026-10-04)

1. The efficiency wave runs first; this wave starts after it, beginning with S1.
2. Every crew stays its own `@listen` Flow step; no generic dispatcher (S4).
3. Tracer/Dashboard/HallucinationGuard are not used outside this repo: S8 deletes whatever
   the flow does not use.
4. A renderer failure stops the run with a clear error in the logs; no fallback "Erreur"
   page is rendered or emailed (S5).
5. (2026-10-05) No helper layer around CrewAI objects: crews keep `Agent(...)` / `Task(...)`
   / `Crew(...)` written out in their decorated methods (S1).
