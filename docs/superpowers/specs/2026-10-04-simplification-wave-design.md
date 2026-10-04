# Simplification Wave — Design

**Date:** 2026-10-04
**Status:** Draft — for review
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

1. One source of truth for crew keys, titles, renderers and output paths.
2. `main.py` ≤ 1,100 lines; no function above complexity 20 (radon D) in `src`.
3. Crew modules without repeated LLM/agent boilerplate; `type: ignore` in crews −80%.
4. Behaviour preserved: every PR is a refactor proven by tests, except where noted.

## Non-goals

- Performance changes (efficiency wave).
- New features, new crews, prompt changes.
- Replacing CrewAI decorators (`@CrewBase`, `@agent`, `@task`, `@crew`) — helpers are called
  inside them.

## Design

### S1 — Crew factory helpers (mechanical, first)

`crews/_factory.py`:

- `make_agent(crew, name, *, tools=(), task_type="default", **overrides) -> Agent` — reads
  `crew.agents_config[name]`, sets `llm=LLMConfig.get_openrouter_llm(task_type=...)`,
  `max_iter=LLMConfig.get_max_iter()`, `verbose` from `CREW_VERBOSE` (default off), and
  applies overrides (e.g. `max_iter=30` for the stock analyst).
- `make_task(crew, name, **kwargs) -> Task` — typed config access, removing most
  `call-arg` ignores.
- Crew methods become one-liners inside the existing decorators. `load_dotenv()` moves to
  the entry points only.
- The ADR-014 guard tests (AST kwargs, agent contract) keep passing unchanged.

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

### S4 — Crew registry and one standard handler

`crew_registry.py` holds one `CrewSpec(key, crew_factory, model_cls, json_path, html_path,
docx_assembler, title, prepare_inputs=None)` per crew. The router becomes a dict lookup; the
`or_(...)` list is built from the registry; `TemplateManager` titles and `RendererFactory`
keys are read from it (fixing the existing drift). A single `run_standard_crew` listener
handles the crews whose `generate_*` follow the common steps (kickoff → load model →
`emit_report`): poem, news_company, findaily, news_daily, saint_daily, book_summary,
meeting_prep, sales_prospecting, pestel. Custom methods stay for RSS, menu, recipe,
shopping, deep research, OSINT and holiday.

Visible change: `crewai flow plot` shows one node for the standard crews instead of one per
crew. Tests on flow wiring (`test_flow_wiring`, `test_determine_crew_router`, per-crew
wiring tests) are rewritten against the registry.

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

1. S1 — crew factory helpers
2. S2 — parsing validators + `json_repair`
3. S3 — deep research standard path
4. S4 — crew registry + standard handler
5. S5 — rendering
6. S6 — flow state
7. S7 — menu
8. S8 — small consolidations (Python), then infra (separate)

## Risks

- **Large diffs in `main.py` (S4, S6):** mitigated by registry-first, one crew group per
  commit, characterisation tests.
- **Parsing tolerance (S2, S3):** messy LLM output that parses today might not tomorrow;
  mitigated by replaying recorded raw outputs from `debug/`.
- **Error propagation (S5):** a renderer bug now fails the run instead of sending a broken
  page; this is intended but visible.

## Decisions (2026-10-04)

1. The efficiency wave runs first; this wave starts after it, beginning with S1.
2. Tracer/Dashboard/HallucinationGuard are not used outside this repo: S8 deletes whatever
   the flow does not use.

## Open questions

1. **Plot granularity (S4):** is one "standard crews" node in `crewai flow plot` acceptable?
2. **Error propagation (S5):** confirm that a renderer failure should stop the run rather
   than send a fallback page.
