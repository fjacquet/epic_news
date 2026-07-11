# Prompt Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rephrase/enrich step to `InformationExtractionCrew` that rewrites the raw user request into a clean brief, so structured extraction fills reliably and downstream crews receive a rich `context`.

**Architecture:** Extend the existing single-task `InformationExtractionCrew` into a two-task sequential crew: `enrich_request_task` (raw request → enriched brief) runs first, then the existing extraction task consumes it via `context=[...]`. `main.py::extract_info` captures the brief off `result.tasks_output[0].raw` into `state.enriched_brief`, and `ContentState.to_crew_inputs()` maps it to the `context` input every crew template can read.

**Tech Stack:** CrewAI 1.15+ (`@CrewBase`, `@agent`, `@task`, `Process.sequential`), Pydantic v2, `LLMConfig` (OpenRouter), pytest, `uv`.

## Global Constraints

- Package manager is `uv` only — run tests with `uv run pytest` (never bare `pytest`, `pip`, or `poetry`).
- Tools are assigned in Python `@agent` methods, never in YAML. The enrich agent has NO tools.
- Use `LLMConfig.get_openrouter_llm()` and `LLMConfig.get_timeout(...)` — never hardcode model names or timeouts.
- Pydantic fields use modern `X | None` syntax.
- Faithfulness rule (copied from spec): the enrich agent must **reorganize and clarify only — never invent** facts (no fabricated budget, dates, traveler counts, or preferences).
- Fallback rule: when the enrich output is empty/unusable, extraction and `state.enriched_brief` both fall back to the raw request — never worse than today.
- Loguru for logging (`from loguru import logger`), not stdlib logging.
- `ReceptionFlow(user_request=...)` stores the arg privately; `state.user_request` is only populated by `feed_user_request()`. In tests that call `extract_info()` directly, set `flow.state.user_request` explicitly.

---

### Task 1: `ContentState.enriched_brief` field + `context` injection

**Files:**
- Modify: `src/epic_news/models/content_state.py` (add field near `user_request`; add injection in `to_crew_inputs`)
- Test: `tests/models/test_content_state_enriched_context.py`

**Interfaces:**
- Produces: `ContentState.enriched_brief: str | None` (default `None`); `to_crew_inputs()` returns a dict whose `"context"` equals `enriched_brief` when that field is truthy, otherwise the prior behaviour (extracted context or `""`).

- [ ] **Step 1: Write the failing test**

Create `tests/models/test_content_state_enriched_context.py`:

```python
"""to_crew_inputs must surface the enriched brief as the downstream `context`."""

from epic_news.models.content_state import ContentState


def test_enriched_brief_becomes_context():
    state = ContentState()
    state.user_request = "raw messy request"
    state.enriched_brief = "Clean family road-trip brief with all four cities"
    inputs = state.to_crew_inputs()
    assert inputs["context"] == "Clean family road-trip brief with all four cities"


def test_no_enriched_brief_keeps_default_context():
    state = ContentState()
    state.user_request = "raw messy request"
    inputs = state.to_crew_inputs()
    # Unchanged behaviour: context stays the empty-string placeholder when nothing set it.
    assert inputs.get("context", "") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/models/test_content_state_enriched_context.py -v`
Expected: FAIL — `test_enriched_brief_becomes_context` raises `AttributeError: ... has no field "enriched_brief"` (Pydantic rejects the assignment).

- [ ] **Step 3: Add the field**

In `src/epic_news/models/content_state.py`, in the `REQUEST INFORMATION` block, immediately after the `extracted_info: ExtractedInfo | None = None` line, add:

```python
    enriched_brief: str | None = None
```

- [ ] **Step 4: Inject it as `context` in `to_crew_inputs`**

In `src/epic_news/models/content_state.py`, in `to_crew_inputs`, locate the final return:

```python
        # Return clean dictionary, removing None values but keeping required placeholders
        return {k: v for k, v in inputs.items() if v is not None}
```

Immediately **before** that return, add:

```python
        # The enriched brief is a clean, complete rewrite of the whole request, so it is
        # the best working context for any downstream crew. Prefer it; fall back to
        # whatever context extraction produced (or the placeholder) when absent.
        if self.enriched_brief:
            inputs["context"] = self.enriched_brief
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/models/test_content_state_enriched_context.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/models/content_state.py tests/models/test_content_state_enriched_context.py
git commit -m "feat(state): add enriched_brief and surface it as downstream context"
```

---

### Task 2: Add enrich agent + task to `InformationExtractionCrew`

**Files:**
- Modify: `src/epic_news/crews/information_extraction/config/agents.yaml` (add `prompt_enricher_agent`)
- Modify: `src/epic_news/crews/information_extraction/config/tasks.yaml` (add `enrich_request_task`)
- Modify: `src/epic_news/crews/information_extraction/information_extraction_crew.py` (add agent method + task method defined BEFORE the extraction task; wire `context`)
- Test: `tests/crews/test_information_extraction_enrich.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: a 2-agent / 2-task crew. `crew.tasks[0]` is the enrich task (plain text output, no `output_pydantic`); `crew.tasks[1]` is the extraction task with `output_pydantic is ExtractedInfo` and a non-empty `context` list containing the enrich task. Task execution/definition order is enrich-first.

- [ ] **Step 1: Write the failing test**

Create `tests/crews/test_information_extraction_enrich.py`:

```python
"""InformationExtractionCrew runs an enrich task before extraction, and the
extraction task consumes the enriched brief as context."""

from epic_news.crews.information_extraction.information_extraction_crew import (
    InformationExtractionCrew,
)
from epic_news.models.extracted_info import ExtractedInfo


def test_crew_has_two_agents_and_two_tasks():
    crew = InformationExtractionCrew().crew()
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2


def test_enrich_runs_first_and_extraction_consumes_it():
    crew = InformationExtractionCrew().crew()
    enrich_task, extract_task = crew.tasks[0], crew.tasks[1]

    # Enrich task emits plain text (the brief), not the structured model.
    assert enrich_task.output_pydantic is None
    # Extraction task still produces ExtractedInfo, and now reads the enrich task.
    assert extract_task.output_pydantic is ExtractedInfo
    assert extract_task.context, "extraction task must consume the enrich task as context"
    assert enrich_task in extract_task.context


def test_faithfulness_guard_is_present_in_config():
    """The 'never invent' constraint is the core safety property — lock it in so a
    future edit can't quietly drop it. Real LLM faithfulness is checked manually
    (see the plan's end-to-end verification), not in CI."""
    ie = InformationExtractionCrew()
    agent_backstory = ie.prompt_enricher_agent().backstory.lower()
    task_desc = ie.enrich_request_task().description.lower()
    assert "never invent" in agent_backstory
    assert "do not" in task_desc and "invent" in task_desc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/crews/test_information_extraction_enrich.py -v`
Expected: FAIL — `test_crew_has_two_agents_and_two_tasks` asserts 2 but the crew currently has 1 agent / 1 task.

- [ ] **Step 3: Add the enrich agent to `agents.yaml`**

Append to `src/epic_news/crews/information_extraction/config/agents.yaml`:

```yaml
prompt_enricher_agent:
  role: >
    Request Clarity Editor
  goal: >
    Rewrite a user's raw request into a single clear, well-structured brief that a
    downstream specialist can act on without re-reading the original. Preserve every
    fact; add nothing.
  backstory: >-
    You are a precise editor. You take rambling, multi-part, or multilingual requests
    and reorganise them into one coherent brief: who, what, where, when, and any stated
    preferences or constraints. You NEVER invent details — no budgets, dates, traveler
    counts, or preferences the user did not state. If a detail is missing, you leave it
    out rather than guessing. You keep the user's original language.
```

- [ ] **Step 4: Add the enrich task to `tasks.yaml`**

Add to `src/epic_news/crews/information_extraction/config/tasks.yaml` (place it **above** `comprehensive_information_extraction_task` for readability; task order is controlled in Python, not YAML):

```yaml
enrich_request_task:
  description: >
    Rewrite the following user request into ONE clear, well-organised brief that a
    downstream specialist can act on directly. Reorganise and clarify only — do NOT
    add, infer, or invent any facts that are not present in the original (no budgets,
    dates, traveler counts, destinations, or preferences the user did not state). If a
    detail is absent, leave it out. Preserve the user's original language. When the
    request lists several places, stages, or steps, keep them all, in order.
    Negative example: if the user says "a week in Anglet with my family", do NOT write
    "a week in Anglet with my family of four on a mid-range budget" — the family size and
    budget were never stated. Write only what was given.
    User request: "{user_request}"
  expected_output: >
    A single concise brief in plain prose (no JSON, no bullet headers required),
    written in the same language as the request, containing every concrete detail the
    user gave and nothing they did not.
  agent: prompt_enricher_agent
```

- [ ] **Step 5: Wire the crew — add the agent + task methods, extraction consumes enrich**

Edit `src/epic_news/crews/information_extraction/information_extraction_crew.py`. Add the enrich agent method and the enrich task method **before** `comprehensive_information_extraction_task`, and add `context=` to the extraction task. Replace the body between the class docstring/config lines and the `@crew` method with:

```python
    @agent
    def prompt_enricher_agent(self) -> Agent:
        """Agent that rewrites the raw request into a clean, faithful brief."""
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["prompt_enricher_agent"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("quick"),
            verbose=True,
        )

    @agent
    def detailed_request_analyzer_agent(self) -> Agent:
        """Agent that analyzes the user request in detail."""
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["detailed_request_analyzer_agent"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @task
    def enrich_request_task(self) -> Task:
        """Task that produces the enriched brief (runs first)."""
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["enrich_request_task"],
            agent=self.prompt_enricher_agent(),  # type: ignore[call-arg]
        )

    @task
    def comprehensive_information_extraction_task(self) -> Task:
        """Task to extract information into a Pydantic model from the enriched brief."""
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["comprehensive_information_extraction_task"],
            agent=self.detailed_request_analyzer_agent(),  # type: ignore[call-arg]
            context=[self.enrich_request_task()],  # type: ignore[call-arg]
            output_pydantic=ExtractedInfo,
        )
```

Leave the `@crew` method unchanged (it already builds from `self.agents` / `self.tasks`).

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/crews/test_information_extraction_enrich.py -v`
Expected: PASS (3 passed).

- [ ] **Step 7: Guard against async-agent regression (existing suite)**

Run: `uv run pytest tests/crews/ -q`
Expected: PASS — the crew still builds; no shared-agent/async violations.

- [ ] **Step 8: Commit**

```bash
git add src/epic_news/crews/information_extraction/ tests/crews/test_information_extraction_enrich.py
git commit -m "feat(extraction): enrich the request before extracting structured fields"
```

---

### Task 3: Capture the enriched brief in `main.py::extract_info`

**Files:**
- Modify: `src/epic_news/main.py` (the `extract_info` method)
- Test: `tests/flows/test_extract_info_enriched_brief.py`

**Interfaces:**
- Consumes: `kickoff_flow(...)` returns a CrewOutput-like object with `.pydantic` (the `ExtractedInfo`) and `.tasks_output` (a list whose `[0].raw` is the enriched brief). It also stores `state.user_request` (set upstream by `feed_user_request`).
- Produces: after `extract_info()`, `state.enriched_brief` is the brief text, or `state.user_request` when no usable brief is present.

- [ ] **Step 1: Write the failing test**

Create `tests/flows/test_extract_info_enriched_brief.py`:

```python
"""extract_info stores the enriched brief on state, falling back to the raw request."""

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow


class _TaskOutput:
    def __init__(self, raw):
        self.raw = raw


class _Result:
    def __init__(self, tasks_output, pydantic=None):
        self.tasks_output = tasks_output
        self.pydantic = pydantic


def _flow(monkeypatch, result):
    flow = ReceptionFlow(user_request="raw messy request")
    flow.state.user_request = "raw messy request"
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda *a, **k: result)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    return flow


def test_captures_enriched_brief(monkeypatch):
    result = _Result([_TaskOutput("Clean brief"), _TaskOutput("{}")], pydantic=None)
    flow = _flow(monkeypatch, result)

    flow.extract_info()

    assert flow.state.enriched_brief == "Clean brief"


def test_falls_back_to_raw_request_when_no_brief(monkeypatch):
    result = _Result([], pydantic=None)  # crew produced no task outputs
    flow = _flow(monkeypatch, result)

    flow.extract_info()

    assert flow.state.enriched_brief == "raw messy request"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/flows/test_extract_info_enriched_brief.py -v`
Expected: FAIL — `state.enriched_brief` is `None` (extract_info does not set it yet), so both asserts fail.

- [ ] **Step 3: Implement brief capture in `extract_info`**

In `src/epic_news/main.py`, find the `extract_info` body:

```python
        extraction_crew = InformationExtractionCrew()
        extracted_data = kickoff_flow(extraction_crew, {"user_request": self.state.user_request})

        dump_crewai_state(extracted_data, "EXTRACTED_INFO")
        # Update the state with the extracted information
        if extracted_data:
            # Assuming extracted_data has a .pydantic attribute for the model instance
            self.state.extracted_info = extracted_data.pydantic
            self.logger.info("✅ Information extraction complete.")
        else:
            self.logger.warning("⚠️ Information extraction failed or returned no data.")
```

Insert brief capture immediately after the `dump_crewai_state(...)` line (before `if extracted_data:`):

```python
        # The enrich task runs first, so its brief is the first task output. Store it as
        # the working context for downstream crews; fall back to the raw request when the
        # crew produced no usable brief (never worse than mailing the raw request).
        tasks_output = getattr(extracted_data, "tasks_output", None) or []
        brief = tasks_output[0].raw.strip() if tasks_output and tasks_output[0].raw else ""
        self.state.enriched_brief = brief or self.state.user_request
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/flows/test_extract_info_enriched_brief.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the broader flow + model suites for regressions**

Run: `uv run pytest tests/flows/ tests/models/ tests/crews/ -q`
Expected: PASS (includes the shipped `test_holiday_no_destination.py` and Tasks 1–2 tests).

- [ ] **Step 6: Lint & format the changed files**

Run: `uv run ruff check --fix src/epic_news/main.py src/epic_news/models/content_state.py src/epic_news/crews/information_extraction/information_extraction_crew.py && uv run ruff format .`
Expected: no remaining errors.

- [ ] **Step 7: Commit**

```bash
git add src/epic_news/main.py tests/flows/test_extract_info_enriched_brief.py
git commit -m "feat(flow): capture the enriched brief into state during extraction"
```

---

## Manual end-to-end verification (after Task 3)

The automated tests stub the LLM. To confirm the real pipeline, run the original failing request through the flow with email disabled and inspect the extracted fields + brief:

- Set `EPIC_ENABLE_EMAIL=false`.
- Kick off with the Montreux→Montpellier→Anglet→Poitiers→Bourges request (the default in `main.py::kickoff`).
- Confirm in `./debug/crewai_state_extracted_info_*.json` that `destination_location` (and ideally `origin_location`/`event_or_trip_duration`) are now populated, and that `output/holiday/itinerary.html` is written (crew ran).

This is a human check, not a CI test (it makes live LLM calls).
