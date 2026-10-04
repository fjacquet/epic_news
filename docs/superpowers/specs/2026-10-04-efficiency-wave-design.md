# Efficiency Wave — Design

**Date:** 2026-10-04
**Status:** Draft — for review
**Source:** codebase audit 2026-10-04 (efficiency section), re-measured on `main` at `649e877`

## Problem

Crews spend more LLM calls, tokens and wall-clock time than their output needs:

- No crew runs tasks in parallel (`async_execution=True` appears nowhere). PESTEL has 6
  independent dimension tasks, NewsDaily 7 independent region tasks; both run one after
  another.
- Every request pays two LLM round-trips before any crew starts: `extract_info`
  (`InformationExtractionCrew`, which also writes `enriched_brief`) then `classify`
  (`ClassifyCrew`).
- The menu designer runs `CookingCrew` once per recipe, sequentially
  (`main.py:848-849`), and each run makes 3 LLM passes (cook → Paprika YAML → JSON export)
  that mostly re-serialise the same recipe. A 30-recipe request makes ~90 sequential calls.
- DOCX assembly narrates sections one by one (`docx_report/assemble.py:23`). A 6-day
  holiday makes ~11 sequential calls and each day fragment resends the full itinerary
  research.
- The cross-reference crew re-researches the subject from scratch (4 `intelligence_*`
  tasks) after the 6 OSINT crews already produced validated reports.
- A rate-limit failure replays the whole crew (`CREW_KICKOFF_ATTEMPTS=3`,
  `flow_enforcement.py:74`) although LiteLLM now retries the single call (`num_retries=2`).
- `import epic_news.main` takes ~7 s, 2.2 s of it importing Composio eagerly through
  `config/__init__.py`, although only `company_news` uses it.

## Goals

1. Cut wall-clock time of the slowest crews (PESTEL, NewsDaily, menu, holiday DOCX) by
   at least 2–3×.
2. Cut tokens per run where work is duplicated (menu, cross-reference, routing).
3. Keep report quality: no regression on routing accuracy or report content.
4. Measure every claim: each change ships with before/after numbers.

## Non-goals

- Changing the default model or provider (ADR-016).
- Rewriting prompts beyond merging or removing duplicated passes.
- Caching across runs (ADR-006: real-time retrieval stays).
- Structural refactors of `main.py` or crews (simplification wave).

## Design

### E0 — Baseline and measurement (first PR)

Log per crew run: wall-clock duration and `CrewOutput.token_usage` (prompt, completion,
total, successful requests) at INFO, from `kickoff_flow` / `akickoff_flow`, which already
wrap every crew. A small script `scripts/bench_crew.py` replays a fixed input for a named
crew and prints the numbers. Record a baseline for PESTEL, NewsDaily, menu (5 recipes),
holiday DOCX and the routing step before any other change.

### E1 — Cheap fixes (same PR as E0)

- **Lazy Composio:** stop exporting `ComposioConfig` from `config/__init__.py`; import it
  in `company_news` only. Target: −2 s import time.
- **Single crew attempt:** default `CREW_KICKOFF_ATTEMPTS` to 1; LLM-level retries
  (`num_retries=2`, empty-response backoff) handle transient errors without replaying
  finished tasks.
- **Scraper output cap:** wrap crewai's `ScrapeWebsiteTool` (no truncation) so results are
  capped (default 12k characters, `SCRAPE_MAX_CHARS`), like ScrapeNinja's 20k cap.

### E2 — Parallel independent tasks

Set `async_execution=True` on tasks that do not depend on each other, with the
synthesis task listing them in `context=`:

- PESTEL: the 6 dimension tasks (one agent each, so no shared agent state).
- NewsDaily: the 7 region tasks. They share one researcher agent today; give each region
  task its own agent instance built by calling the `@agent` method again. **Never
  `agent.copy()`**: `LLM.__copy__` drops the timeout (ADR-014).

Prior failure: async tasks were turned off in d8cdfca after a raw tool-call list leaked into
`TaskOutput.raw`; 06b8724 added coercion on the async path (`_acall_with_empty_retry`,
`_react_safe_text`). Validate with one live run per crew before merging.

Concurrency raises request rate: keep `max_rpm` per crew and check the Gemini quota tier
(see open questions).

### E3 — Menu designer and recipes

- `CookingCrew` keeps only the cook task, with `output_pydantic=PaprikaRecipe`; YAML and
  JSON exports are produced in Python from the model. `generate_recipe` benefits too.
- Recipes run concurrently: `asyncio.gather` over `akickoff_flow(CookingCrew(), ...)`,
  bounded by a semaphore (`MENU_RECIPE_CONCURRENCY`, default 4). Order of the result list
  follows the menu, not completion order.

Target: −60% tokens and ≥3× faster for a 10-recipe menu.

### E4 — DOCX assembly

- `assemble_fragments` narrates sections in a `ThreadPoolExecutor`
  (`DOCX_FRAGMENT_CONCURRENCY`, default 4), keeping section order. The degraded-section
  check (more than half placeholders → refuse) is unchanged.
- Holiday: each day fragment receives only that day's slice of the itinerary research
  when the research JSON has per-day entries; otherwise it falls back to the full text.

### E5 — Routing in one call

Add `selected_crew: Literal[<CrewCategories>]` to the extraction model so
`InformationExtractionCrew` extracts and classifies in one task; delete `ClassifyCrew`
and the `classify` step, and route on the typed field (no substring match). Acceptance:
routing accuracy on a fixed set of ~25 representative requests (≥1 per crew) is equal or
better than today, measured live before and after.

### E6 — Cross-reference synthesis

Pass the 6 validated OSINT models (compact JSON) as inputs to one synthesis task; delete
the 4 `intelligence_*` re-research tasks and the researcher's tools. Acceptance: side-by-side
comparison of one live OSINT run, reviewed by the user, plus token numbers.

## Validation

- Unit tests for each mechanism (concurrency bounds, ordering, YAML/JSON export from the
  model, routing field, scraper cap, import laziness).
- Live runs with `scripts/bench_crew.py` before and after each PR for the affected crew;
  numbers go in the PR description.
- Full suite, ruff, mypy and the existing guard tests (ADR-014) stay green.

## Rollout (one PR each, in order)

1. E0 + E1 — baseline, logging, cheap fixes
2. E2 — PESTEL and NewsDaily async
3. E4 — DOCX parallel fragments
4. E3 — menu and recipes
5. E5 — routing in one call
6. E6 — cross-reference synthesis

## Open questions

1. **Gemini quota:** which rate-limit tier does the key have? It bounds safe concurrency
   (E2–E4 default to 4).
2. **Live-run budget:** E2–E6 each need before/after live runs. Is a budget of roughly a
   dozen crew runs acceptable?
3. **E5 fallback:** drop `ClassifyCrew` entirely, or keep it as a fallback when the
   extraction field is empty?
4. **E6 quality:** OK to judge the cross-reference change on one side-by-side run?
5. **Order with the simplification wave:** see that spec's open questions.
