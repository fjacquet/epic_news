# Simplification S6 — Flow State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ContentState` replaces its 34 per-crew result fields with three fields: `report`, `raw_output` and `osint`. The crew keys become a `StrEnum` (`CrewKey`) that keys the registry and the router.

**Architecture:**
- `CrewKey` (a `StrEnum` in `crew_registry.py`) lists every crew key plus `UNKNOWN`.
- `CREW_REGISTRY` is keyed by `CrewKey`, and a test keeps the two in step.
- `determine_crew` compares `CrewKey` members instead of string literals. The step names it returns are unchanged.
- `ContentState` keeps its request, configuration, communication and meeting fields, plus `final_report` / `error_message`. Its result fields become:
  - `report: SerializeAsAny[BaseModel] | None`: the validated model of the report step that ran;
  - `raw_output: Any`: that step's raw crew result;
  - `osint: dict[str, SerializeAsAny[BaseModel]]`: the OSINT sub-reports by crew name.
- `_run_standard` sets `report` / `raw_output`, and the custom steps set them themselves.
- `to_crew_inputs()` stops dumping the result fields into crew inputs.

**Tech Stack:** Python 3.13 (`enum.StrEnum`), Pydantic 2, CrewAI 1.15.23 Flow, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S6; decisions 2, 4, 5).

Facts this plan relies on (checked on `main` at `9e11281`):

- `content_state.py` is 329 lines. Its result fields (content_state.py:105-153) are:
  - `final_report`, `error_message`;
  - the 34 per-crew report fields, from `company_profile` to `saint_daily_model`.
  Several hold the wrong type: `company_news_report`, `fin_daily_report`, `news_daily_report`, `saint_daily_report` and `book_summary` receive a raw `CrewOutput` but are annotated with a model, and `menu_designer_report` receives a path string.
- **Writers:** only `main.py` writes these fields. `self.state.<field> = ...` appears at main.py:429, 564, 588-589, 608-609, 702, 720, 764, 805, 841, 889, 931, 1101 and 1158. The OSINT parallel crews write through `setattr(self.state, state_attr, output)` at main.py:1075. `end_unknown` writes `final_report` at main.py:400.
- **Readers in `src/`, `scripts/`, `api.py`, `app.py` and `send_email`:** none. `app.py`'s `final_report` is `st.session_state.final_report`, which is a different object.
- **Readers in tests:**
  - `state.pestel_report` (4 places);
  - `state.deep_research_report` (3);
  - `state.menu_designer_report` (1);
  - `state.final_report` (2);
  - the deep-research field annotation test, if still present.
- **Crew inputs:** `to_crew_inputs()` starts from `self.model_dump(exclude={"extracted_info"})`, so every result field also becomes a crew input. No crew YAML uses any of those names as a placeholder (checked with `grep -rlE "\{<field>\}" src/epic_news/crews` for each field: 0 hits).
- **Routing:** `determine_crew` (main.py:331-376) compares `self.state.selected_crew` with 16 string literals. `main.py:182` and `main.py:323` use `CrewCategories.UNKNOWN`. Steps look specs up as `CREW_REGISTRY["POEM"]` etc.
- **Tests that parse source:** `tests/test_crew_registry.py` reads `determine_crew` with the regex `selected_crew == "(\w+)":\s*return "(\w+)"`, and `_run_standard` callers with `_run_standard\(\s*CREW_REGISTRY\["(\w+)"\]`.
- **`main.py` length:** 1,359 lines. The spec target is ≤ 1,350.

## Global Constraints

- Replace the duplicated per-crew fields in `ContentState` with `report: BaseModel | None`, `raw_output: Any` and `osint: dict[str, BaseModel]`. Crew keys become a `StrEnum` built from the registry. Check every reader (`app.py`, `api.py`, `send_email`) first (spec S6).
- The Flow structure does not change. Every crew keeps its own `@listen` step, and `determine_crew` returns the same step names (decision 2).
- No helper layer around CrewAI `Agent`/`Task`/`Crew` (decision 5). No crew module or YAML change.
- A report-building error stops the run, and no placeholder report is produced (decision 4, ADR-017).
- The classifier categories and routing guide text stay byte-identical, order included (pinned by `tests/test_crew_registry.py`).
- Project rules:
  - use `uv` only;
  - put imports at the top of the file;
  - log with Loguru;
  - use Python 3.13 union syntax;
  - respect mypy `warn_unused_ignores`;
  - never commit `ruff format` changes to tracked Markdown files; format only the Python files you change.

## Review Focus

1. A crew YAML placeholder that relied on a result field being present in the crew inputs would raise `KeyError` at kickoff. None exist today, so a test pins it: no `{placeholder}` in any crew YAML names a removed field (test in Task 2).
2. After a failed report step, `state.report` / `state.raw_output` must not hold a previous step's values. Each flow run has its own state; the helper sets the fields only after the report is built (test in Task 2).
3. When an OSINT sub-crew fails, `state.osint` holds only the crews that succeeded; there is no `KeyError` and no `None` entry (test in Task 2).
4. A `selected_crew` value from the LLM that is not a `CrewKey`, for example `"poem"` (lower case) or `""`, must still route to `go_unknown` (test in Task 1).
5. `ContentState().model_dump()` and `model_dump_json()` must still work when `report` holds a real model, because CrewAI serializes flow state for events. The dump must keep the model's fields, not `{}` (test in Task 2).

---

### Task 1: `CrewKey` keys the registry and the router

**Files:**
- Modify: `src/epic_news/crew_registry.py` (add `CrewKey`; type `CrewSpec.key` and `CREW_REGISTRY` with it; spec entries use `CrewKey.X`)
- Modify: `src/epic_news/models/content_state.py` (`CrewCategories` reads `CrewKey`)
- Modify: `src/epic_news/main.py` (`determine_crew` compares `CrewKey` members; `CREW_REGISTRY[CrewKey.X]` lookups; `CrewCategories.UNKNOWN` → `CrewKey.UNKNOWN`)
- Modify: `tests/test_crew_registry.py` (regexes and a `CrewKey` test)

**Interfaces:**
- Produces: `epic_news.crew_registry.CrewKey(StrEnum)` with members `BOOK_SUMMARY, COMPANY_NEWS, COOKING, DEEPRESEARCH, FINDAILY, HOLIDAY_PLANNER, MEETING_PREP, MENU, NEWSDAILY, OPEN_SOURCE_INTELLIGENCE, PESTEL, POEM, RSS, SAINT, SALES_PROSPECTING, SHOPPING, UNKNOWN`. Each member's value equals its name. `CREW_REGISTRY: dict[CrewKey, CrewSpec]` keeps all members except `UNKNOWN`. `CrewSpec.key: CrewKey`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_crew_registry.py`:

1. Import `CrewKey` next to `CREW_REGISTRY`.
2. Change the two source regexes:

```python
    pairs = re.findall(r'selected_crew == CrewKey\.(\w+):\s*return "(\w+)"', source)
```

```python
    used = set(re.findall(r"_run_standard\(\s*CREW_REGISTRY\[CrewKey\.(\w+)\]", source))
```

3. Add:

```python
def test_crew_keys_match_the_registry():
    assert {key.value for key in CrewKey} == set(CREW_REGISTRY) | {"UNKNOWN"}
    assert all(key.value == key.name for key in CrewKey)
    assert all(isinstance(key, CrewKey) for key in CREW_REGISTRY)
    assert CrewKey.UNKNOWN not in CREW_REGISTRY


def test_non_member_values_route_to_unknown():
    flow = ReceptionFlow(user_request="x")
    for value in ("poem", "", "POEM "):
        flow.state.selected_crew = value
        assert flow.determine_crew() == "go_unknown", value
```

Keep the existing assertions, including the byte-identical routing string and the category order.

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_crew_registry.py -q`
Expected: FAIL (`ImportError: cannot import name 'CrewKey'`).

- [ ] **Step 3: Add `CrewKey` and key the registry with it**

In `src/epic_news/crew_registry.py`, add `from enum import StrEnum` at the top, and add this above `CrewSpec`:

```python
class CrewKey(StrEnum):
    """Routing key of every crew, plus UNKNOWN. Values equal names (classifier output)."""

    BOOK_SUMMARY = "BOOK_SUMMARY"
    COMPANY_NEWS = "COMPANY_NEWS"
    COOKING = "COOKING"
    DEEPRESEARCH = "DEEPRESEARCH"
    FINDAILY = "FINDAILY"
    HOLIDAY_PLANNER = "HOLIDAY_PLANNER"
    MEETING_PREP = "MEETING_PREP"
    MENU = "MENU"
    NEWSDAILY = "NEWSDAILY"
    OPEN_SOURCE_INTELLIGENCE = "OPEN_SOURCE_INTELLIGENCE"
    PESTEL = "PESTEL"
    POEM = "POEM"
    RSS = "RSS"
    SAINT = "SAINT"
    SALES_PROSPECTING = "SALES_PROSPECTING"
    SHOPPING = "SHOPPING"
    UNKNOWN = "UNKNOWN"
```

Then make these changes in the same file:
- change `key: str` to `key: CrewKey` in `CrewSpec`;
- in `_SPECS`, replace each string key with its member (`CrewSpec(CrewKey.POEM, "Création poétique", ...)`);
- type `CREW_REGISTRY: dict[CrewKey, CrewSpec]`;
- type `STANDARD_CREWS: tuple[CrewKey, ...]` and replace its strings with members.

Because `StrEnum` members are `str`, `CREW_REGISTRY["POEM"]` and `"POEM" in CREW_REGISTRY` keep working.

- [ ] **Step 4: Categories, router and lookups**

In `src/epic_news/models/content_state.py`, import `CrewKey` with `CREW_REGISTRY` and set `UNKNOWN = CrewKey.UNKNOWN` in `CrewCategories`. Change `to_dict` to:

```python
        return {key.value: key.value for key in sorted(CREW_REGISTRY)} | {cls.UNKNOWN.value: cls.UNKNOWN.value}
```

In `src/epic_news/main.py`:
- import `CrewKey` from `epic_news.crew_registry`;
- in `determine_crew`, replace every `self.state.selected_crew == "X"` with `self.state.selected_crew == CrewKey.X`, keeping the same order and the same returned step names;
- replace every `CREW_REGISTRY["X"]` with `CREW_REGISTRY[CrewKey.X]`;
- replace `CrewCategories.UNKNOWN` (main.py:182, 323) with `CrewKey.UNKNOWN`, and remove the `CrewCategories` import if nothing else in main.py uses it.

- [ ] **Step 5: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
```
Expected: all tests pass, including the byte-identical routing string; ruff and mypy are clean.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/crew_registry.py src/epic_news/models/content_state.py src/epic_news/main.py tests/test_crew_registry.py
git commit -m "refactor: CrewKey StrEnum keys the crew registry and the router"
```

---

### Task 2: `report`, `raw_output`, `osint` replace the per-crew state fields

**Files:**
- Modify: `src/epic_news/models/content_state.py` (fields; `to_crew_inputs` exclude; imports)
- Modify: `src/epic_news/main.py` (`_run_standard`; every step that wrote a removed field; OSINT `run_crew`)
- Modify: tests that read `state.pestel_report`, `state.deep_research_report` or `state.menu_designer_report`. Find them with `grep -rnE "state\.(pestel_report|deep_research_report|menu_designer_report|cross_reference_report|company_profile|tech_stack|web_presence_report|hr_intelligence_report|legal_analysis_report|geospatial_analysis)" tests`.
- Create: `tests/models/test_content_state_results.py`

**Interfaces:**
- Consumes: Task 1's `CrewKey`, `CREW_REGISTRY`.
- Produces:
  - `ContentState.report: SerializeAsAny[BaseModel] | None = None`
  - `ContentState.raw_output: Any = None`
  - `ContentState.osint: dict[str, SerializeAsAny[BaseModel]] = {}`

  `_run_standard` sets `report` and `raw_output` after `emit_report` returns. Custom steps set them as listed in Step 5. `to_crew_inputs()` never includes `report`, `raw_output` or `osint`.

- [ ] **Step 1: Write the failing state tests**

Create `tests/models/test_content_state_results.py`:

```python
"""ContentState keeps one report, the raw output and the OSINT sub-reports (simplification S6)."""

import json
import re
from pathlib import Path

from epic_news.models.content_state import ContentState
from epic_news.models.crews.poem_report import PoemJSONOutput

REMOVED = {
    "company_profile", "tech_stack", "tech_stack_report", "contact_info_report", "lead_score_report",
    "geospatial_analysis", "osint_report", "hr_intelligence_report", "legal_analysis_report",
    "web_presence_report", "cross_reference_report", "pestel_report", "news_report",
    "company_news_report", "deep_research_report", "rss_weekly_report", "fin_daily_report",
    "news_daily_report", "saint_daily_report", "post_report", "location_report", "holiday_plan",
    "recipe", "menu_designer_report", "menu_plan", "book_summary", "shopping_advice_report",
    "shopping_advice_model", "poem", "meeting_prep_report", "financial_report_model",
    "news_daily_model", "saint_daily_model",
}
CREWS_DIR = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "crews"


def _poem() -> PoemJSONOutput:
    return PoemJSONOutput.model_validate({"title": "Titre", "poem": "Vers"})


def test_result_fields_are_report_raw_output_and_osint():
    fields = set(ContentState.model_fields)
    assert {"report", "raw_output", "osint", "final_report", "error_message"} <= fields
    assert not (REMOVED & fields)


def test_results_never_reach_crew_inputs():
    state = ContentState(user_request="x")
    state.report = _poem()
    state.raw_output = object()
    state.osint = {"tech_stack": _poem()}
    inputs = state.to_crew_inputs()
    assert not ({"report", "raw_output", "osint"} & set(inputs))


def test_dump_keeps_the_report_fields():
    state = ContentState(user_request="x")
    state.report = _poem()
    state.osint = {"tech_stack": _poem()}
    dumped = json.loads(state.model_dump_json(exclude={"raw_output"}))
    assert dumped["report"]["title"] == "Titre"
    assert dumped["osint"]["tech_stack"]["poem"] == "Vers"


def test_no_crew_prompt_uses_a_removed_field():
    placeholders: set[str] = set()
    for yaml_file in CREWS_DIR.glob("*/config/*.yaml"):
        placeholders |= set(re.findall(r"\{(\w+)\}", yaml_file.read_text(encoding="utf-8")))
    assert not (placeholders & (REMOVED | {"report", "raw_output", "osint"}))
```

Check `PoemJSONOutput`'s required fields (`grep -n "class PoemJSONOutput" -A10 src/epic_news/models/crews/poem_report.py`) and adjust the dict if needed. `ruff format` may reflow `REMOVED`; accept its output.

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/models/test_content_state_results.py -q`
Expected: FAIL (`report` is not a field; removed fields are still present).

- [ ] **Step 3: Replace the fields**

In `src/epic_news/models/content_state.py`, replace everything from `# Business Intelligence Reports` down to and including `saint_daily_model: ...` (inside the "CREW RESULTS" section; keep `final_report` and `error_message`) with:

```python
    # The validated model of the report step that ran, and its raw crew result.
    report: SerializeAsAny[BaseModel] | None = None
    raw_output: Any = None
    # OSINT sub-reports by crew name (company_profile, tech_stack, ...): only the crews that succeeded.
    osint: dict[str, SerializeAsAny[BaseModel]] = Field(default_factory=dict)
```

Add `SerializeAsAny` to the `pydantic` import. Delete the model imports (content_state.py:15-34) that nothing else in the file uses (ruff F401 tells you), and drop `Optional` if it is unused. In `to_crew_inputs`, change the first dump to:

```python
        inputs = self.model_dump(exclude={"extracted_info", "report", "raw_output", "osint"})
```

If `raw_output` holding a `CrewOutput` makes `model_dump` warn or fail in a test, report the error and stop. Do not add `arbitrary_types_allowed` or custom serializers without asking.

- [ ] **Step 4: The helper sets the results**

In `main.py`, in `_run_standard`, add these lines after `emit_report(...)` and before `return output, model`:

```python
        self.state.report = model
        self.state.raw_output = output
```

Then remove every line in the ten standard steps that stored the output or the model in a removed field. These are main.py:429, 564, 588-589, 608-609, 764, 841, 889 and 931 at `9e11281`; locate them by content, because Task 1 shifts lines. Each `output, model = self._run_standard(...)` whose values are no longer used becomes `self._run_standard(...)`.

- [ ] **Step 5: The custom steps set the results**

| Step | Today | After |
|---|---|---|
| `generate_rss_weekly` | `state.rss_weekly_report = f"Report generated at ..."` | `self.state.report = <the RssWeeklyReport passed to assemble_rss_docx>`; build it once into a local variable before `emit_report` and reuse it in the lambda |
| `generate_recipe` | (nothing stored) | `self.state.report = recipe_model`, after `emit_report` |
| `generate_menu_designer` | `state.menu_plan = menu_plan`; `state.menu_designer_report = final_report` (a path) | `self.state.report = menu_plan` after its `emit_report`; delete the `menu_designer_report` line and keep the `output_file` restore |
| `generate_shopping_advice` | `state.shopping_advice_model = shopping_advice_obj` | `self.state.report = shopping_advice_obj` |
| `generate_osint` / `run_crew` | `return (state_attr, output)` + `setattr(self.state, state_attr, output)` | `return (crew_name, model)` + `self.state.osint[crew_name] = model`; delete the now-unused `state_attr` tuple element from `parallel_crews` and from the `run_crew` signature |
| `_run_cross_reference_report` | `state.cross_reference_report = output` | `self.state.raw_output = output` there, and `self.state.report = report_model` after its model is loaded |
| `generate_holiday_plan` | `state.holiday_plan = crew_result` | `self.state.raw_output = crew_result` |
| `end_unknown` | `state.final_report = "Error: ..."` | unchanged |

Keep each step's order of operations otherwise unchanged. A model is stored only after the step built its report, so a failed step leaves `report` empty.

- [ ] **Step 6: Flow tests for the results**

Add to `tests/test_run_standard.py`:

```python
def test_report_and_raw_output_are_set_after_the_docx(flow, monkeypatch):
    def _kickoff(_crew, inputs):
        Path(inputs["output_file"]).write_text(json.dumps(POEM), encoding="utf-8")
        return SimpleNamespace(raw=json.dumps(POEM), output=None)

    def _assemble(model, inputs, output_path, llm=None):
        assert flow.state.report is None  # not set before the report is built
        Path(output_path).write_bytes(b"docx")
        return output_path

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    output, model = flow._run_standard(_spec_with(_assemble), object(), flow.state.to_crew_inputs())
    assert flow.state.report is model
    assert flow.state.raw_output is output


def test_failed_report_leaves_no_result(flow, monkeypatch):
    def _kickoff(_crew, inputs):
        Path(inputs["output_file"]).write_text(json.dumps(POEM), encoding="utf-8")
        return SimpleNamespace(raw=json.dumps(POEM), output=None)

    def _assemble(*_a, **_k):
        raise RuntimeError("pandoc missing")

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    with pytest.raises(RuntimeError, match="pandoc missing"):
        flow._run_standard(_spec_with(_assemble), object(), flow.state.to_crew_inputs())
    assert flow.state.report is None
    assert flow.state.raw_output is None
```

For OSINT, find the existing test of `generate_osint` / the parallel crews (`grep -rln "parallel_crews\|generate_osint\|_run_osint" tests`). Add a test in that file where one of the six stubbed crews raises. Assert that `flow.state.osint` has exactly the five other crew names as keys, and that every value is a `BaseModel` instance. Reuse that file's stubs. If no such test file exists, report it, and write the test in `tests/test_osint_state.py` with stubs for `akickoff_flow`, `dump_crewai_state` and the six crew classes, following `tests/test_generate_deep_research_flow.py`.

- [ ] **Step 7: Update the tests that read removed fields**

Replace each read of `state.pestel_report`, `state.deep_research_report` or `state.menu_designer_report` with `state.report`. Keep the assertion's meaning: a test that checked the PESTEL model now checks `isinstance(flow.state.report, PestelReport)` plus its original checks. Delete a test that only checked a removed field's annotation (for example `ContentState.model_fields["deep_research_report"]`) and name it in your report.

- [ ] **Step 8: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
wc -l src/epic_news/main.py src/epic_news/models/content_state.py
grep -rnE "state\.(company_profile|tech_stack|web_presence_report|hr_intelligence_report|legal_analysis_report|geospatial_analysis|cross_reference_report|pestel_report|company_news_report|deep_research_report|rss_weekly_report|fin_daily_report|news_daily_report|saint_daily_report|holiday_plan|menu_designer_report|menu_plan|book_summary|shopping_advice_model|meeting_prep_report|news_daily_model|saint_daily_model)\b" src scripts tests
```
Expected:
- all tests pass, and ruff and mypy are clean;
- report both line counts (`main.py` was 1,359, `content_state.py` 329);
- the final grep prints nothing.

- [ ] **Step 9: Commit**

```bash
git add src/epic_news/models/content_state.py src/epic_news/main.py tests
git commit -m "refactor(state): report, raw_output and osint replace the per-crew result fields"
```

---

### Task 3: Docs

**Files:**
- Modify: `src/epic_news/utils/CLAUDE.md` and root `CLAUDE.md`, where they name a removed state field, `CrewCategories` constants or `CREW_REGISTRY["X"]`
- Modify: `docs/explanations/architecture.md`, `docs/tutorials/getting_started.md` (Step 7 uses `CREW_REGISTRY["BOOK_RECOMMENDER"]`: add a `CrewKey` member and use `CREW_REGISTRY[CrewKey.BOOK_RECOMMENDER]`), `src/epic_news/crews/CLAUDE.md`, only where a statement is now false

**Interfaces:**
- Consumes: Task 1 (`CrewKey`, registry keyed by it) and Task 2 (`report`, `raw_output`, `osint`; results excluded from crew inputs).

- [ ] **Step 1: Find stale statements**

```bash
grep -rnE "CREW_REGISTRY\[\"|CrewCategories\.[A-Z]|state\.(pestel_report|deep_research_report|menu_designer_report|news_daily_model|saint_daily_model|fin_daily_report|company_news_report|holiday_plan|book_summary)|content_state.*(field|report)" CLAUDE.md src/epic_news/*/CLAUDE.md docs/explanations docs/tutorials docs/reference docs/how-to README.md
```

List the hits in your report. Leave historical docs (`docs/superpowers/`, `docs/archive/`, `TODO.md`, `CHANGELOG.md`) alone.

- [ ] **Step 2: Rewrite each hit**

State what is true after Tasks 1-2:
- **Adding a crew:** add a `CrewKey` member and a `CrewSpec`.
- **Lookups:** steps look specs up with `CREW_REGISTRY[CrewKey.X]`.
- **Flow state:** the state holds the report step's model in `report`, its raw result in `raw_output`, and the OSINT sub-reports in `osint`.

Edit only the wrong sentences and code samples.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md src/epic_news docs
git commit -m "docs: CrewKey and the report/raw_output/osint flow state (S6)"
```

Do not stage `docs/audits/` (untracked, must stay out of git). Do not run `ruff format .` (it rewrites tracked Markdown).

---

Controller, before the PR: live run of one standard crew and of OSINT is not needed. S6 changes no crew input, no prompt and no report path, and the tests pin the routing text and the crew inputs. Run one live `saint` with `EPIC_ENABLE_EMAIL=false` (`env -u VIRTUAL_ENV uv run python scripts/bench_flow.py saint`) to check the flow end to end, and record it with the other runs. In the PR description, report the `main.py` and `content_state.py` line counts against the spec target (`main.py` ≤ 1,350).
