# Implementation Validation Plan (pre-refactor)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin the current ReceptionFlow implementation with deterministic tests (zero LLM calls, zero network) and fix only the live defects those tests expose — before any structural refactor.

**Architecture:** Three layers of validation: (1) contract tests that introspect wiring and configuration statically (flow listeners, agent LLM config, tool JSON conventions), (2) characterization tests that pin current behavior of pure functions (`to_crew_inputs`), (3) one mocked end-to-end flow test that drives `ReceptionFlow` with stubbed `kickoff_flow`/`akickoff_flow` and asserts the deterministic glue (routing → parsing → HTML rendering → email gating). Minimal fixes are folded into the task that exposes them; nothing else changes.

**Tech Stack:** Python 3.13, pytest + pytest-env (sentinel API keys already configured in `pyproject.toml`), CrewAI 1.15.1 (flow metadata via `__flow_method_definition__`), Loguru, uv.

## Global Constraints

- Package manager: `uv` only. Before any pytest run in a fresh session: `uv sync --all-extras` (plain `uv sync` prunes test extras and pytest falls back to a global 3.12 install).
- Tests must never call an LLM or the network. Sentinel keys come from `[tool.pytest_env]` in `pyproject.toml` (already sets `OPENROUTER_API_KEY=test_...`, `EPIC_ENABLE_EMAIL=false`, `POSTHOG_DISABLED=1`).
- No assertions on LLM-generated content — tests assert code behavior with canned fixtures only.
- Git: stage files explicitly by path; never `git add -A`. Do not stage `uv.lock`, `.serena/project.yml`, or `src/epic_news/main.py` unless a task says so.
- All imports at top of files; Loguru (never stdlib `logging`) in `src/`; Python 3.13 union syntax (`X | None`).
- Every commit message ends with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Run `uv run ruff check --fix <changed files> && uv run ruff format <changed files>` before each commit (pre-commit hooks enforce this anyway).

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `tests/crews/test_async_agent_isolation.py` | commit as-is (Task 1) | existing async-isolation guard |
| `src/epic_news/utils/flow_enforcement.py` | modify (Task 2) | switch to Loguru, fix log placeholders |
| `tests/utils/test_flow_enforcement.py` | create (Task 2) | kickoff wrapper behavior + log formatting |
| `tests/test_flow_wiring.py` | create (Task 3) | flow listener/route/category wiring contract |
| `src/epic_news/main.py` | modify (Task 3) | remove dead listeners, fix holiday "error" return |
| `src/epic_news/models/content_state.py` | modify (Task 3 + Task 5) | remove orphan categories; prints → logger |
| `tests/crews/test_agent_llm_contract.py` | create (Task 4) | every agent's LLM comes from LLMConfig |
| 5 crew files (listed in Task 4) | modify (Task 4) | add missing `llm=` |
| `tests/models/test_content_state_crew_inputs.py` | create (Task 5) | characterize `to_crew_inputs()` |
| `tests/flows/test_reception_flow_e2e.py` | create (Task 6) | mocked end-to-end flow test |
| `tests/tools/test_json_contract_ratchet.py` | create (Task 7) | tool JSON-convention ratchet |

---

### Task 1: Baseline — green suite, commit pending async-isolation work

**Files:**
- Commit (already modified in working tree): `src/epic_news/crews/company_profiler/company_profiler_crew.py`, `src/epic_news/crews/cross_reference_report_crew/cross_reference_report_crew.py`, `src/epic_news/crews/fin_daily/fin_daily.py`, `src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py`, `src/epic_news/crews/hr_intelligence/hr_intelligence_crew.py`, `src/epic_news/crews/legal_analysis/legal_analysis_crew.py`, `src/epic_news/crews/news_daily/news_daily.py`, `src/epic_news/crews/tech_stack/tech_stack_crew.py`, `src/epic_news/crews/web_presence/web_presence_crew.py`
- Commit (untracked): `tests/crews/test_async_agent_isolation.py`

**Interfaces:**
- Produces: a clean, committed baseline; later tasks assume `uv run pytest -q` is green.

- [ ] **Step 1: Sync environment**

Run: `uv sync --all-extras && uv pip install -e .`
Expected: exits 0.

- [ ] **Step 2: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (≈205 tests). If any fail, STOP and report — the baseline must be green before validation work starts.

- [ ] **Step 3: Commit the pending async-isolation work (explicit paths only)**

```bash
git add src/epic_news/crews/company_profiler/company_profiler_crew.py \
        src/epic_news/crews/cross_reference_report_crew/cross_reference_report_crew.py \
        src/epic_news/crews/fin_daily/fin_daily.py \
        src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py \
        src/epic_news/crews/hr_intelligence/hr_intelligence_crew.py \
        src/epic_news/crews/legal_analysis/legal_analysis_crew.py \
        src/epic_news/crews/news_daily/news_daily.py \
        src/epic_news/crews/tech_stack/tech_stack_crew.py \
        src/epic_news/crews/web_presence/web_presence_crew.py \
        tests/crews/test_async_agent_isolation.py
git commit -m "fix(crews): isolate agents for concurrent async tasks (CrewAI 1.15)" \
           -m "Concurrent async tasks sharing one Agent hit 'Executor is already running'; each now gets its own Agent via .copy(). Adds structural regression test." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Leave `uv.lock` and `.serena/project.yml` uncommitted (out of scope).

---

### Task 2: Fix flow_enforcement logging defect (Loguru)

`src/epic_news/utils/flow_enforcement.py` uses stdlib `logging` with Loguru-style `{}` placeholders (lines 63-65, 71, 95-99, 105) — every kickoff produces a logging formatting error. Fix by switching to Loguru.

**Files:**
- Modify: `src/epic_news/utils/flow_enforcement.py`
- Test: `tests/utils/test_flow_enforcement.py` (create)

**Interfaces:**
- Consumes: `kickoff_flow(crew_or_factory, context: dict) -> Any` (unchanged signature).
- Produces: same public API; log lines now render correctly. Task 6's e2e test patches this function by name in `epic_news.main`.

- [ ] **Step 1: Write the failing test**

Create `tests/utils/test_flow_enforcement.py`:

```python
"""Tests for the kickoff_flow wrapper: behavior and log formatting."""

import pytest
from loguru import logger

from epic_news.utils.flow_enforcement import kickoff_flow


class StubCrew:
    """Mimics a @CrewBase factory: has .crew() returning an object with .kickoff()."""

    def __init__(self):
        self.received_inputs = None

    def crew(self):
        return self

    def kickoff(self, inputs):
        self.received_inputs = inputs
        return "SENTINEL_RESULT"


def test_kickoff_flow_calls_kickoff_and_returns_result():
    stub = StubCrew()
    result = kickoff_flow(stub, {"topic": "x"})
    assert result == "SENTINEL_RESULT"
    assert stub.received_inputs == {"topic": "x"}


def test_kickoff_flow_rejects_non_dict_context():
    with pytest.raises(ValueError):
        kickoff_flow(StubCrew(), "not a dict")


def test_kickoff_flow_logs_are_formatted():
    """Placeholders must be interpolated: no literal '{}' or '%.2fs' in output."""
    records: list[str] = []
    sink_id = logger.add(lambda msg: records.append(str(msg)), level="INFO")
    try:
        kickoff_flow(StubCrew(), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    text = "".join(records)
    assert "StubCrew" in text
    assert "{}" not in text
    assert "%.2fs" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/test_flow_enforcement.py -v`
Expected: `test_kickoff_flow_logs_are_formatted` FAILS (`"StubCrew" in text` fails — stdlib logging never reaches the loguru sink). The two behavior tests PASS.

- [ ] **Step 3: Fix the implementation**

In `src/epic_news/utils/flow_enforcement.py`:

Replace:
```python
import logging
import time
```
with:
```python
import time
```

Replace:
```python
logger = logging.getLogger(__name__)
```
with:
```python
from loguru import logger
```
(move the import up to the import block, after `import time`, keeping all imports at top).

In `kickoff_flow`, replace the finally-block log line:
```python
            logger.info("✅ Crew {} finished in %.2fs", crew_name, elapsed)
```
with:
```python
            logger.info("✅ Crew {} finished in {:.2f}s", crew_name, elapsed)
```

In `akickoff_flow`, replace the identical finally-block line the same way:
```python
            logger.info("✅ Crew {} finished in {:.2f}s", crew_name, elapsed)
```

The two "🚀 Kicking off …" calls already use `{}` placeholders — they become correct automatically once the logger is Loguru. Make no other changes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/utils/test_flow_enforcement.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/epic_news/utils/flow_enforcement.py tests/utils/test_flow_enforcement.py
uv run ruff format src/epic_news/utils/flow_enforcement.py tests/utils/test_flow_enforcement.py
git add src/epic_news/utils/flow_enforcement.py tests/utils/test_flow_enforcement.py
git commit -m "fix(utils): use Loguru in flow_enforcement, repair log placeholders" \
           -m "stdlib logging with {} placeholders raised a formatting error on every crew kickoff." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Flow wiring contract test + remove dead wiring

Every listener trigger must reference a real method or router label; every routable category must have a route. Today this fails three ways: `send_email` listens to non-existent `generate_cross_reference_report` / `generate_html_report`; `generate_holiday_plan` returns the label `"error"` from a non-router method (inert); `CrewCategories` defines `LEAD_SCORING`, `LOCATION`, `POST_ONLY`, `SHOPPING_ADVISOR` which the router dead-ends to `go_unknown`.

**Files:**
- Test: `tests/test_flow_wiring.py` (create — sits next to existing `tests/test_determine_crew_router.py`)
- Modify: `src/epic_news/main.py` (lines ~1347-1368: `send_email` decorators; line ~1315: holiday return)
- Modify: `src/epic_news/models/content_state.py` (lines 47, 49, 56, 62: orphan category constants)

**Interfaces:**
- Consumes: CrewAI 1.15 stores each decorated flow method's metadata in `method.__flow_method_definition__` (a `FlowMethodDefinition` with `.listen: str | dict | None`, `.router: bool`). Conditions are trees of `str | dict | list` — collect string leaves recursively.
- Produces: `ROUTER_LABELS` list in the test — Task 6 does not depend on it, but future refactors will use this test as the wiring gate.

- [ ] **Step 1: Write the failing test**

Create `tests/test_flow_wiring.py`:

```python
"""Wiring contract for ReceptionFlow: no dead listeners, no unroutable categories.

Introspects CrewAI 1.15 flow metadata (__flow_method_definition__) without
running the flow. Zero LLM calls.
"""

from epic_news.main import ReceptionFlow
from epic_news.models.content_state import CrewCategories

# Labels the @router("classify") method can return (mirrors determine_crew).
ROUTER_LABELS = {
    "go_generate_holiday_plan",
    "go_generate_meeting_prep",
    "go_generate_book_summary",
    "go_generate_recipe",
    "go_generate_menu_designer",
    "go_generate_shopping_advice",
    "go_generate_poem",
    "go_generate_news_company",
    "go_generate_osint",
    "go_generate_rss_weekly",
    "go_generate_findaily",
    "go_generate_news_daily",
    "go_generate_saint_daily",
    "go_generate_sales_prospecting_report",
    "go_generate_deep_research",
    "go_generate_pestel",
    "go_unknown",
}


def _flow_methods() -> dict[str, object]:
    """All decorated flow methods on ReceptionFlow, by name."""
    return {
        name: member
        for name, member in vars(ReceptionFlow).items()
        if hasattr(member, "__flow_method_definition__")
    }


def _string_leaves(condition) -> set[str]:
    """Collect every string leaf from a condition tree (str | dict | list)."""
    if condition is None:
        return set()
    if isinstance(condition, str):
        return {condition}
    if isinstance(condition, dict):
        leaves: set[str] = set()
        for value in condition.values():
            leaves |= _string_leaves(value)
        return leaves
    if isinstance(condition, (list, tuple)):
        leaves = set()
        for item in condition:
            leaves |= _string_leaves(item)
        return leaves
    return set()


def test_every_listener_trigger_exists():
    """Each name a listener waits on must be a real method or a router label."""
    methods = _flow_methods()
    known_events = set(methods) | ROUTER_LABELS

    dead: dict[str, set[str]] = {}
    for name, member in methods.items():
        triggers = _string_leaves(member.__flow_method_definition__.listen)
        unknown = {
            t for t in triggers if t not in known_events and t not in ("AND", "OR")
        }
        if unknown:
            dead[name] = unknown

    assert not dead, f"Listeners waiting on non-existent events: {dead}"


def test_every_router_label_has_a_listener():
    """Each label determine_crew can emit must trigger at least one listener."""
    methods = _flow_methods()
    all_triggers: set[str] = set()
    for member in methods.values():
        all_triggers |= _string_leaves(member.__flow_method_definition__.listen)

    unhandled = ROUTER_LABELS - all_triggers
    assert not unhandled, f"Router labels nothing listens to: {unhandled}"


def test_every_category_is_routable():
    """Every classifier category except UNKNOWN must have a router branch.

    Guards against categories the classifier can emit that dead-end in
    go_unknown (previously: LEAD_SCORING, LOCATION, POST_ONLY, SHOPPING_ADVISOR).
    """
    flow_source_categories = set(CrewCategories.to_dict().values()) - {"UNKNOWN"}
    # Categories determine_crew actually routes (mirrors its if-chain).
    routed = {
        "HOLIDAY_PLANNER",
        "MEETING_PREP",
        "BOOK_SUMMARY",
        "COOKING",
        "MENU",
        "SHOPPING",
        "POEM",
        "COMPANY_NEWS",
        "OPEN_SOURCE_INTELLIGENCE",
        "RSS",
        "FINDAILY",
        "NEWSDAILY",
        "SAINT",
        "SALES_PROSPECTING",
        "DEEPRESEARCH",
        "PESTEL",
    }
    unroutable = flow_source_categories - routed
    assert not unroutable, f"Categories with no router branch: {unroutable}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_flow_wiring.py -v`
Expected: `test_every_listener_trigger_exists` FAILS listing `send_email → {generate_cross_reference_report, generate_html_report}`; `test_every_category_is_routable` FAILS listing the 4 orphan categories. (`test_every_router_label_has_a_listener` should PASS.)

If `test_every_listener_trigger_exists` instead errors with `AttributeError` on `__flow_method_definition__`, inspect one method (`python -c "from epic_news.main import ReceptionFlow; m = vars(ReceptionFlow)['send_email']; print(type(m), vars(m).keys())"`) and adjust the attribute access in `_flow_methods()` accordingly — the metadata object is defined in `crewai/flow/flow_wrappers.py` and merged by `crewai/flow/dsl/_utils.py`.

- [ ] **Step 3: Remove the dead wiring in `src/epic_news/main.py`**

Delete the entire second stacked listener decorator on `send_email`:
```python
    @listen(or_("generate_cross_reference_report", "generate_html_report"))
```
(the line between the big `or_(...)` decorator and `@trace_task(tracer)`).

In the big `or_(...)` decorator on `send_email`, delete the line:
```python
            "generate_cross_reference_report",
```

In `generate_holiday_plan`, replace:
```python
        if not current_inputs.get("destination"):
            self.logger.warning("⚠️ No destination found for holiday plan. Aborting and routing to error.")
            # TODO: Define an actual 'error' step or handle this more gracefully.
            return "error"  # Or another appropriate error state like 'go_unknown'
```
with:
```python
        if not current_inputs.get("destination"):
            self.logger.warning("⚠️ No destination found for holiday plan; skipping crew execution.")
            return None
```

- [ ] **Step 4: Remove the orphan categories in `src/epic_news/models/content_state.py`**

Delete these four lines from `CrewCategories`:
```python
    LEAD_SCORING = "LEAD_SCORING"
```
```python
    LOCATION = "LOCATION"
```
```python
    POST_ONLY = "POST_ONLY"
```
```python
    SHOPPING_ADVISOR = "SHOPPING_ADVISOR"
```

Note: `ContentState` fields `lead_score_report` / `location_report` / `post_report` stay — only the classifier-visible category constants are removed (the classifier could previously pick them and dead-end).

- [ ] **Step 5: Run wiring test + full suite**

Run: `uv run pytest tests/test_flow_wiring.py tests/test_determine_crew_router.py -v`
Expected: all PASS (the existing router test's drift check uses `CrewCategories.to_dict()` and must stay green).

Run: `uv run pytest -q`
Expected: all PASS. If `tests/models/test_content_state.py` asserts the removed constants exist, update those assertions to match (removal is intentional).

- [ ] **Step 6: Commit**

```bash
uv run ruff check --fix src/epic_news/main.py src/epic_news/models/content_state.py tests/test_flow_wiring.py
uv run ruff format src/epic_news/main.py src/epic_news/models/content_state.py tests/test_flow_wiring.py
git add src/epic_news/main.py src/epic_news/models/content_state.py tests/test_flow_wiring.py
git commit -m "fix(flow): remove dead listeners and unroutable categories, add wiring contract test" \
           -m "send_email listened to two non-existent steps; 4 classifier categories had no router branch; holiday planner returned an inert 'error' label." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Agent LLM-config contract test + fix 5 drifting crews

Five crews never set `llm=` on their agents (`geospatial_analysis`, `company_news`, `meeting_prep`, `saint_daily`, `shopping_advisor`), silently falling back to env-var resolution and losing `LLMConfig`'s temperature/base_url/reasoning settings. The discriminator: `LLMConfig.get_openrouter_llm()` sets `base_url="https://openrouter.ai/api/v1"`; env-resolved agents don't.

**Files:**
- Test: `tests/crews/test_agent_llm_contract.py` (create)
- Modify: `src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py`, `src/epic_news/crews/company_news/company_news_crew.py`, `src/epic_news/crews/meeting_prep/meeting_prep_crew.py`, `src/epic_news/crews/saint_daily/saint_daily.py`, `src/epic_news/crews/shopping_advisor/shopping_advisor.py`

**Interfaces:**
- Consumes: `ASYNC_CREWS` list from `tests/crews/test_async_agent_isolation.py` (13 constructible crews) — reuse its construction pattern, not the list itself.
- Produces: `ALL_CREWS` / `SKIP_CONSTRUCTION` lists other structural tests can copy.

- [ ] **Step 1: Write the failing test**

Create `tests/crews/test_agent_llm_contract.py`:

```python
"""Contract: every agent's LLM must come from LLMConfig (OpenRouter base_url).

Agents without llm= resolve via env fallback and silently lose temperature,
base_url, and reasoning settings. Construction only — zero LLM calls.
"""

import os

import pytest

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("MODEL", "openrouter/test/model")

from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_news.company_news_crew import CompanyNewsCrew
from epic_news.crews.company_profiler.company_profiler_crew import CompanyProfilerCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import (
    CrossReferenceReportCrew,
)
from epic_news.crews.deep_research.deep_research import DeepResearchCrew
from epic_news.crews.fin_daily.fin_daily import FinDailyCrew
from epic_news.crews.geospatial_analysis.geospatial_analysis_crew import (
    GeospatialAnalysisCrew,
)
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.hr_intelligence.hr_intelligence_crew import HRIntelligenceCrew
from epic_news.crews.information_extraction.information_extraction_crew import (
    InformationExtractionCrew,
)
from epic_news.crews.legal_analysis.legal_analysis_crew import LegalAnalysisCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew
from epic_news.crews.news_daily.news_daily import NewsDailyCrew
from epic_news.crews.pestel.pestel_crew import PestelCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.post.post_crew import PostCrew

# ReceptionCrew is referenced nowhere outside its own package (dead-code
# candidate for the refactor phase) but the LLM contract still applies.
from epic_news.crews.reception.reception_crew import ReceptionCrew
from epic_news.crews.rss_weekly.rss_weekly_crew import RssWeeklyCrew
from epic_news.crews.saint_daily.saint_daily import SaintDailyCrew
from epic_news.crews.sales_prospecting.sales_prospecting_crew import (
    SalesProspectingCrew,
)
from epic_news.crews.shopping_advisor.shopping_advisor import ShoppingAdvisorCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ALL_CREWS = [
    ClassifyCrew,
    CompanyNewsCrew,
    CompanyProfilerCrew,
    CookingCrew,
    CrossReferenceReportCrew,
    DeepResearchCrew,
    FinDailyCrew,
    GeospatialAnalysisCrew,
    HolidayPlannerCrew,
    HRIntelligenceCrew,
    InformationExtractionCrew,
    LegalAnalysisCrew,
    LibraryCrew,
    MeetingPrepCrew,
    MenuDesignerCrew,
    NewsDailyCrew,
    PestelCrew,
    PoemCrew,
    PostCrew,
    ReceptionCrew,
    RssWeeklyCrew,
    SaintDailyCrew,
    SalesProspectingCrew,
    ShoppingAdvisorCrew,
    TechStackCrew,
    WebPresenceCrew,
]

# Crews whose construction needs an external process (e.g. MCP server) or
# missing external config. Seed empty; populate ONLY with an inline reason
# if Step 2 shows a construction error that is genuinely environmental.
# Likely candidates: DeepResearchCrew, HolidayPlannerCrew, LibraryCrew
# (they start the Wikipedia MCP server) — add them ONLY if construction
# actually fails in this environment.
SKIP_CONSTRUCTION: dict[type, str] = {}


@pytest.mark.parametrize("crew_cls", ALL_CREWS, ids=lambda c: c.__name__)
def test_every_agent_uses_llmconfig(crew_cls):
    if crew_cls in SKIP_CONSTRUCTION:
        pytest.skip(SKIP_CONSTRUCTION[crew_cls])
    crew = crew_cls().crew()
    offenders = []
    for agent in crew.agents:
        base_url = getattr(agent.llm, "base_url", None)
        if base_url != OPENROUTER_BASE_URL:
            offenders.append(f"{agent.role!r} (base_url={base_url!r})")
    assert not offenders, (
        f"{crew_cls.__name__}: agents not configured via "
        f"LLMConfig.get_openrouter_llm(): {offenders}"
    )
```

- [ ] **Step 2: Run test to verify it fails for exactly the 5 known crews**

Run: `uv run pytest tests/crews/test_agent_llm_contract.py -v`
Expected: FAIL for `GeospatialAnalysisCrew`, `CompanyNewsCrew`, `MeetingPrepCrew`, `SaintDailyCrew`, `ShoppingAdvisorCrew`; PASS for the rest.

Contingencies:
- If a crew fails with a *construction* error (MCP/subprocess/env), add it to `SKIP_CONSTRUCTION` with a one-line reason and re-run — that is a documented environmental limit, not a contract failure.
- If a passing crew's `agent.llm` has no `base_url` attribute at all, print `vars(agent.llm)` for one agent and adjust the attribute name (`base_url` vs `api_base`) to whatever `LLMConfig.get_openrouter_llm()` actually produces — the contract is "same attributes as LLMConfig's LLM".

- [ ] **Step 3: Fix the 5 crews**

In each of the 5 files, for **every** `@agent` method's `Agent(...)` call that lacks `llm=`, add these two arguments (matching the pattern used by the sibling OSINT crews, e.g. `src/epic_news/crews/hr_intelligence/hr_intelligence_crew.py`):

```python
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
```

And add the import at the top of each file if missing:

```python
from epic_news.config.llm_config import LLMConfig
```

Files and agents:
- `geospatial_analysis_crew.py`: `geospatial_researcher`, `geospatial_reporter`
- `company_news_crew.py`: every `@agent` method in the file
- `meeting_prep_crew.py`: every `@agent` method in the file
- `saint_daily.py`: every `@agent` method in the file
- `shopping_advisor.py`: every `@agent` method in the file

Change nothing else in these files (no `max_rpm`/`verbose` changes — this task is only the LLM contract).

- [ ] **Step 4: Run contract test + full suite**

Run: `uv run pytest tests/crews/test_agent_llm_contract.py -v`
Expected: all PASS (or skip, for documented `SKIP_CONSTRUCTION` entries).

Run: `uv run pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check --fix tests/crews/test_agent_llm_contract.py \
    src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py \
    src/epic_news/crews/company_news/company_news_crew.py \
    src/epic_news/crews/meeting_prep/meeting_prep_crew.py \
    src/epic_news/crews/saint_daily/saint_daily.py \
    src/epic_news/crews/shopping_advisor/shopping_advisor.py
uv run ruff format tests/crews/test_agent_llm_contract.py \
    src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py \
    src/epic_news/crews/company_news/company_news_crew.py \
    src/epic_news/crews/meeting_prep/meeting_prep_crew.py \
    src/epic_news/crews/saint_daily/saint_daily.py \
    src/epic_news/crews/shopping_advisor/shopping_advisor.py
git add tests/crews/test_agent_llm_contract.py \
    src/epic_news/crews/geospatial_analysis/geospatial_analysis_crew.py \
    src/epic_news/crews/company_news/company_news_crew.py \
    src/epic_news/crews/meeting_prep/meeting_prep_crew.py \
    src/epic_news/crews/saint_daily/saint_daily.py \
    src/epic_news/crews/shopping_advisor/shopping_advisor.py
git commit -m "fix(crews): route 5 crews' agents through LLMConfig, add LLM contract test" \
           -m "geospatial/company_news/meeting_prep/saint_daily/shopping_advisor relied on env fallback, losing temperature/base_url/reasoning settings." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Characterize `to_crew_inputs()` + silence its debug prints

`ContentState.to_crew_inputs()` is the universal input marshaller — pin its mapping behavior before any refactor. It also contains `print()` debug statements (lines 221-223, 247, 251, 256, 258, 303, 307, 310 of `content_state.py`) polluting stdout on every call.

**Files:**
- Test: `tests/models/test_content_state_crew_inputs.py` (create — separate from existing `tests/models/test_content_state.py`)
- Modify: `src/epic_news/models/content_state.py` (prints → `logger.debug`)

**Interfaces:**
- Consumes: `ContentState.to_crew_inputs() -> dict`, `ExtractedInfo` fields (`main_subject_or_activity`, `target_company`, `destination_location`, …).
- Produces: nothing new — behavior is pinned, not changed.

- [ ] **Step 1: Write the tests (characterization + no-stdout)**

Create `tests/models/test_content_state_crew_inputs.py`:

```python
"""Characterization tests pinning to_crew_inputs() before refactoring."""

from epic_news.models.content_state import ContentState
from epic_news.models.extracted_info import ExtractedInfo


def _state() -> ContentState:
    return ContentState(
        user_request="Plan a trip",
        extracted_info=ExtractedInfo(
            main_subject_or_activity="Trip to Rome",
            target_company="ACME Corp",
            destination_location="Rome",
            origin_location="Geneva",
            event_or_trip_duration="3 days",
            traveler_details="2 adults",
            user_preferences_and_constraints="vegetarian",
        ),
    )


def test_extracted_info_field_mapping():
    inputs = _state().to_crew_inputs()
    assert inputs["topic"] == "Trip to Rome"
    assert inputs["company"] == "ACME Corp"
    assert inputs["destination"] == "Rome"
    assert inputs["origin"] == "Geneva"
    assert inputs["duration"] == "3 days"
    assert inputs["family"] == "2 adults"
    assert inputs["user_preferences_and_constraints"] == "vegetarian"


def test_required_placeholders_always_present():
    inputs = ContentState(user_request="x").to_crew_inputs()
    for key in ("user_preferences_and_constraints", "context", "original_message", "target_audience"):
        assert key in inputs, f"missing required placeholder: {key}"


def test_none_values_are_stripped():
    inputs = ContentState(user_request="x").to_crew_inputs()
    assert all(v is not None for v in inputs.values())


def test_computed_fields_present():
    inputs = ContentState(user_request="x").to_crew_inputs()
    assert "current_date" in inputs
    assert "season" in inputs
    assert "topic_slug" in inputs
    assert "menu_slug" in inputs


def test_target_falls_back_from_company_to_topic():
    with_company = _state().to_crew_inputs()
    assert with_company["target"] == "ACME Corp"

    topic_only = ContentState(
        user_request="x",
        extracted_info=ExtractedInfo(main_subject_or_activity="Solar panels"),
    ).to_crew_inputs()
    assert topic_only["target"] == "Solar panels"


def test_no_stdout_noise(capsys):
    """to_crew_inputs must not print() — it runs on every crew kickoff."""
    _state().to_crew_inputs()
    captured = capsys.readouterr()
    assert captured.out == ""
```

- [ ] **Step 2: Run tests to verify current state**

Run: `uv run pytest tests/models/test_content_state_crew_inputs.py -v`
Expected: `test_no_stdout_noise` FAILS (debug prints); the characterization tests PASS. If any characterization test fails, do NOT change the assertion blindly — inspect `to_crew_inputs()` to confirm what current behavior actually is, then pin that (this task documents reality, it does not redesign).

- [ ] **Step 3: Replace prints with logger.debug**

In `src/epic_news/models/content_state.py`, add to the import block at top:

```python
from loguru import logger
```

Then replace every `print(...)` call inside `_flatten_extracted_info` and `_add_menu_mappings` with `logger.debug(...)`, keeping the message text unchanged. Example:

```python
        logger.debug("🔍 DEBUG _flatten_extracted_info:")
        logger.debug(f"  extracted_data keys: {list(extracted_data.keys())}")
```

(9 call sites total: lines 221-223, 247, 251, 256, 258, 303, 307, 310.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/models/test_content_state_crew_inputs.py tests/models/test_content_state.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
uv run ruff check --fix src/epic_news/models/content_state.py tests/models/test_content_state_crew_inputs.py
uv run ruff format src/epic_news/models/content_state.py tests/models/test_content_state_crew_inputs.py
git add src/epic_news/models/content_state.py tests/models/test_content_state_crew_inputs.py
git commit -m "test(models): characterize to_crew_inputs(), replace debug prints with logger.debug" \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Mocked end-to-end ReceptionFlow test

The centerpiece: drive the real flow (routing, parsing, HTML rendering, email gating) with `kickoff_flow`/`akickoff_flow` stubbed — zero LLM calls. Covers the happy path (POEM route) and the unknown-category path.

**Files:**
- Test: `tests/flows/test_reception_flow_e2e.py` (create; also create empty `tests/flows/__init__.py` if other tests dirs have one — mirror whatever `tests/models/` does)

**Interfaces:**
- Consumes: `epic_news.main.kickoff_flow` / `epic_news.main.akickoff_flow` (patched by name in the `main` module); `parse_crewai_output` reads `.raw` from crew output; `extract_info` reads `.pydantic`; `classify` calls `str(...)` on the result.
- Produces: `FakeCrewOutput` fixture class — the refactor phase will reuse it.

- [ ] **Step 1: Write the construction smoke test**

Create `tests/flows/test_reception_flow_e2e.py` (first slice):

```python
"""Deterministic end-to-end tests for ReceptionFlow with stubbed crew kickoffs.

No LLM calls: kickoff_flow/akickoff_flow are patched in epic_news.main.
All file output is redirected to tmp_path via monkeypatch.chdir (the flow's
paths are cwd-relative).
"""

import json

import pytest

from epic_news.main import ReceptionFlow
from epic_news.models.extracted_info import ExtractedInfo


class FakeCrewOutput:
    """Mimics crewai CrewOutput for the attributes ReceptionFlow reads."""

    def __init__(self, raw: str = "", pydantic=None):
        self.raw = raw
        self.pydantic = pydantic
        self.tasks_output = []
        self.json_dict = None

    def __str__(self) -> str:
        return self.raw


def test_flow_constructs():
    flow = ReceptionFlow(user_request="test request")
    assert flow._user_request == "test request"
```

- [ ] **Step 2: Run the smoke test**

Run: `uv run pytest tests/flows/test_reception_flow_e2e.py -v`
Expected: PASS.

Contingency: if construction fails inside `Memory(...)` (network/storage init), patch it at module level in the test file before the `ReceptionFlow` import is used:

```python
# only if real Memory construction fails under sentinel env:
from unittest.mock import MagicMock
import epic_news.main as main_module
main_module.Memory = MagicMock()
```

and note in the test docstring why. Do not proceed until construction passes.

- [ ] **Step 3: Add the POEM happy-path and unknown-route tests**

Append to `tests/flows/test_reception_flow_e2e.py`:

```python
def _fake_kickoff_factory(classification: str, poem_json: str):
    """Returns a kickoff_flow replacement dispatching on crew class name."""

    def fake_kickoff(crew_or_factory, context):
        crew_name = type(crew_or_factory).__name__
        if crew_name == "InformationExtractionCrew":
            return FakeCrewOutput(
                raw="{}",
                pydantic=ExtractedInfo(
                    main_subject_or_activity="a test poem",
                    topic="a test poem",
                ),
            )
        if crew_name == "ClassifyCrew":
            return FakeCrewOutput(raw=classification)
        if crew_name == "PoemCrew":
            return FakeCrewOutput(raw=poem_json)
        raise AssertionError(f"Unexpected crew kicked off: {crew_name}")

    return fake_kickoff


def test_poem_route_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")

    poem_json = json.dumps({"title": "Ode to Tests", "poem": "Lines of green.\nNo flakes seen."})
    monkeypatch.setattr(
        "epic_news.main.kickoff_flow", _fake_kickoff_factory("POEM", poem_json)
    )

    flow = ReceptionFlow(user_request="Write me a poem about tests")
    flow.kickoff()

    assert flow.state.selected_crew == "POEM"
    html = tmp_path / "output" / "poem" / "poem.html"
    assert html.exists(), "poem HTML was not written"
    content = html.read_text(encoding="utf-8")
    assert "Ode to Tests" in content
    assert flow.state.email_sent is True  # email step ran and was gated off


def test_unknown_category_routes_to_error_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")

    monkeypatch.setattr(
        "epic_news.main.kickoff_flow",
        _fake_kickoff_factory("GIBBERISH_NO_CATEGORY", "{}"),
    )

    flow = ReceptionFlow(user_request="unclassifiable nonsense")
    flow.kickoff()

    assert flow.state.selected_crew == "UNKNOWN"
    assert flow.state.final_report is not None
    assert flow.state.final_report.startswith("Error:")
```

- [ ] **Step 4: Run the e2e tests**

Run: `uv run pytest tests/flows/test_reception_flow_e2e.py -v`
Expected: 3 PASS.

Contingencies (diagnose, don't loosen assertions):
- `AssertionError: Unexpected crew kicked off` → a flow step invokes a crew the dispatcher doesn't know; add a branch returning a minimal `FakeCrewOutput(raw="{}")` for it and re-run.
- Classification lands on the wrong category → remember `classify()` substring-scans `str(result)`; the fake raw must contain the category token exactly once and no other category token (`"POEM"` also matches inside no other category name — verify against `CrewCategories`).
- HTML missing → check whether `load_or_parse_model` fell back correctly: it reads `output/poem/poem.json` first (won't exist), then parses `FakeCrewOutput.raw` — the raw JSON must validate against `PoemJSONOutput` exactly (`title`, `poem` keys only).

- [ ] **Step 5: Run full suite and commit**

Run: `uv run pytest -q`
Expected: all PASS.

```bash
uv run ruff check --fix tests/flows/test_reception_flow_e2e.py
uv run ruff format tests/flows/test_reception_flow_e2e.py
git add tests/flows/
git commit -m "test(flow): add deterministic end-to-end ReceptionFlow tests with stubbed kickoffs" \
           -m "Covers POEM happy path (route -> parse -> render -> email gate) and unknown-category fallback. Zero LLM calls." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Tool JSON-convention ratchet test

The project rule says every tool's `_run()` returns a JSON string; ~17 tools violate it. Refactoring them is out of scope — instead, freeze the violation list so it can only shrink.

**Files:**
- Test: `tests/tools/test_json_contract_ratchet.py` (create)

**Interfaces:**
- Consumes: static source scan of `src/epic_news/tools/*.py`.
- Produces: `KNOWN_LEGACY` set — the refactor phase burns it down file by file.

- [ ] **Step 1: Write the ratchet test with an empty legacy set**

Create `tests/tools/test_json_contract_ratchet.py`:

```python
"""Ratchet: tools whose _run() doesn't produce JSON may not increase.

Static heuristic: a tool module defining _run() is compliant if its source
references a JSON-producing helper. Crude but deterministic — the point is
to freeze the legacy list so it only shrinks. Remove a file from
KNOWN_LEGACY when you fix it; never add to it.
"""

from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "tools"

JSON_MARKERS = ("json.dumps", "ensure_json_str", "model_dump_json", "to_json")

# Seeded from the state of the codebase on 2026-07-04. Shrink-only.
KNOWN_LEGACY: set[str] = set()  # populated in Step 2 from the first run


def _violators() -> set[str]:
    found = set()
    for path in sorted(TOOLS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "def _run(" not in source:
            continue
        if not any(marker in source for marker in JSON_MARKERS):
            found.add(path.name)
    return found


def test_json_contract_violations_do_not_grow():
    current = _violators()
    new_violations = current - KNOWN_LEGACY
    assert not new_violations, (
        f"New tools without JSON output: {sorted(new_violations)}. "
        "New tools must return JSON strings (see tools/CLAUDE.md and _json_utils)."
    )


def test_known_legacy_list_is_honest():
    """Entries fixed in the source must be removed from KNOWN_LEGACY."""
    current = _violators()
    stale = KNOWN_LEGACY - current
    assert not stale, f"Fixed tools still listed in KNOWN_LEGACY: {sorted(stale)}"
```

- [ ] **Step 2: Run, seed the legacy list from actual output**

Run: `uv run pytest tests/tools/test_json_contract_ratchet.py -v`
Expected: `test_json_contract_violations_do_not_grow` FAILS, printing the actual violator filenames.

Copy the printed filenames verbatim into `KNOWN_LEGACY`, e.g.:

```python
KNOWN_LEGACY: set[str] = {
    "accuweather_tool.py",
    "airtable_tool.py",
    "exchange_rate_tool.py",
    # ... exactly the files the first run printed
}
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/tools/test_json_contract_ratchet.py -v`
Expected: 2 PASS.

- [ ] **Step 4: Full suite + commit**

Run: `uv run pytest -q`
Expected: all PASS.

```bash
uv run ruff check --fix tests/tools/test_json_contract_ratchet.py
uv run ruff format tests/tools/test_json_contract_ratchet.py
git add tests/tools/test_json_contract_ratchet.py
git commit -m "test(tools): ratchet test freezing the JSON-contract violation list" \
           -m "Shrink-only list; refactor phase burns it down." \
           -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Final Verification (after all tasks)

- [ ] Run: `uv run pytest -q` → all PASS
- [ ] Run: `make lint && uv run mypy src/epic_news` → clean (matches CI gates)
- [ ] Run: `rtk git log --oneline -7` → 6 commits from this plan on top of the baseline
- [ ] Report: list of new test files, defects fixed, and the seeded `KNOWN_LEGACY` count — these numbers are the "validated" baseline the refactor plan starts from.

## Explicitly Out of Scope (refactor phase, separate plan)

- Structured classification (`output_pydantic` on ClassifyCrew) and table-driven routing.
- Uniform failure policy / stub-report generalization.
- `ContentState` cleanup (`validate_assignment`, duplicate fields, per-crew input dicts).
- Fixing the tools in `KNOWN_LEGACY`; OSINT crew template dedup; cruft sweep (`.bak`, dead tools, commented graveyards).
