# Simplification S4 — Crew Metadata in One Place Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One `CrewSpec` per crew holds its key, title, model, JSON path, DOCX path and DOCX assembler. The crew categories and the email subject read from it, and the ten standard Flow steps share one `_run_standard` helper. Every crew keeps its own `@listen` step.

**Architecture:** New `src/epic_news/crew_registry.py` holds `CrewSpec` (frozen dataclass) and `CREW_REGISTRY: dict[str, CrewSpec]`. It holds metadata only: it does not route and does not run crews. `ContentState.categories` / `CrewCategories.to_dict()` are built from its keys. `prepare_email_params` takes the subject title from it. In `main.py`, `ReceptionFlow._run_standard(spec, crew, inputs)` does what the standard steps repeat: delete a stale JSON, kickoff (closing MCP), debug dump, `load_or_parse_model`, `emit_report`. Each standard `generate_*` prepares its inputs, calls the helper and stores its state fields. `determine_crew`, the `@listen` decorators and the `or_(...)` list feeding `send_email` stay written out.

**Tech Stack:** Python 3.13, CrewAI 1.15.23 Flow, Pydantic 2, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S4; decisions 2, 5, 6).

Facts this plan relies on (checked on `main` at `d52d97a`):

- `main.py` is 1,497 lines. `determine_crew` (main.py:336-382) is a 16-branch if-chain on `self.state.selected_crew`.
- `CrewCategories` (content_state.py:48-74) lists 16 keys plus `UNKNOWN`. Its users are `main.py:182,323` (`UNKNOWN`), `routing_guide.py:56` (`to_dict`), `ContentState.categories` (content_state.py:118) and tests. Two tests read `CrewCategories.PESTEL`.
- The report titles lived in the deleted `TemplateManager` and had already drifted (no `COMPANY_NEWS` title). Today nothing reads a title: the email subject is `f"Epic News Report: {state.selected_crew} - {state.user_request}"` (report_utils.py:126).
- Standard steps follow the same shape: kickoff → `dump_crewai_state` → `load_or_parse_model(json, Model, ...)` → `emit_report(state, lambda: assemble_x(model, self.state.to_crew_inputs(), docx))`. They are poem, news_company, findaily, news_daily, saint_daily, book_summary, meeting_prep, sales_prospecting, pestel and (since S3) deep_research. PESTEL and deep research close their Wikipedia MCP server in a `finally`; `close_mcp` is a no-op for a crew without one (mcp_config.py:43-53).
- Only OSINT and deep research delete a stale JSON before the kickoff today. In every other standard step, a JSON left by an earlier run is read as this run's output whenever the crew fails to write one.
- Tests patch `main_module.assemble_pestel_docx` (2 tests) and `main_module.assemble_deep_research_docx` (1 test). Once those steps go through the registry, these tests must patch the registry entry instead.
- Assemblers and models do not import `content_state` or `report_utils`, so `content_state → crew_registry → assemblers/models` makes no import cycle.

Decisions this plan takes where the spec is silent or predates S3/S5 (each is listed in the PR description):

1. **Deep research is a standard step.** The spec lists it as custom because of its extractor, which S3 removed. Its step now has exactly the standard shape.
2. **Paths that are computed per run are `None`.** Cooking, menu and shopping name their DOCX after the request, so `CrewSpec.json_path` / `docx_path` / `model_cls` are `None` where a crew has no fixed value. Those crews stay custom steps.
3. **The title is used in the email subject:** `Epic News — <title> : <user_request>`. This is the only reader of the title. Without it the field would be dead.
4. **The helper deletes the stale JSON** for every standard step. This extends the OSINT/deep-research rule: an earlier run's file is never used as this run's report.
5. **Debug dump labels become the registry key**, for example `dump_crewai_state(output, "SAINT")` instead of `"SAINT_DAILY"`. Only the debug file names change.

## Global Constraints

- The Flow structure does not change: every crew keeps its own `@listen` step, `@router determine_crew` keeps returning the step name, and `crewai flow plot` keeps one node per crew (spec S4, decision 2).
- `crew_registry.py` holds metadata only: one `CrewSpec(key, title, model_cls, json_path, docx_path, docx_assembler)` per crew. It does not route and does not run crews (spec S4).
- Report titles and `CrewCategories` read from the registry (spec S4).
- `_run_standard(spec, crew, inputs)` holds kickoff → dump state → load model → `emit_report`. Custom steps stay fully written out for RSS, menu, recipe, shopping, OSINT and holiday (spec S4; deep research moves to standard, see Decision 1).
- The `or_(...)` list of report steps feeding `send_email` stays explicit in the decorator (spec S4).
- Existing flow wiring tests stay valid. Add a test that every `CrewSpec` key has a router branch, a listener and a DOCX assembler (spec S4).
- No helper layer around CrewAI `Agent`/`Task`/`Crew` (decision 5): the helper calls `kickoff_flow(crew, inputs)` on a crew instance the step builds itself. No crew module changes.
- A report-building error stops the run; no placeholder report (decision 4, ADR-017).
- Project rules: `uv` only, imports at the top of the file, Loguru, Python 3.13 union syntax, mypy `warn_unused_ignores`.

## Review Focus

1. A JSON left by an earlier run must not be reused by any standard step when this run's crew writes none (test in Task 2).
2. PESTEL and deep research must still stop their MCP server when the kickoff raises (existing tests `test_generate_deep_research_mcp_cleanup.py` plus a helper test in Task 2).
3. A classified key with no registry entry, for example a typo from the extraction crew, must still route to `go_unknown`, as today (test in Task 1).
4. The email subject must still be built when `selected_crew` is unset or `UNKNOWN`. It falls back to the key, never raises (test in Task 1).
5. Every standard step's assembler must still receive `self.state.to_crew_inputs()`, not the crew inputs, so DOCX metadata is unchanged (test in Task 2).

---

### Task 1: The crew registry

**Files:**
- Create: `src/epic_news/crew_registry.py`
- Modify: `src/epic_news/models/content_state.py:47-74` (`CrewCategories`)
- Modify: `src/epic_news/utils/report_utils.py:126` (subject)
- Modify: `tests/crews/test_pestel_structure.py:65`, `tests/models/test_content_state.py:15`, `tests/utils/test_report_utils.py:33`
- Create: `tests/test_crew_registry.py`

**Interfaces:**
- Produces: `epic_news.crew_registry.CrewSpec` (frozen dataclass: `key: str`, `title: str`, `model_cls: type[BaseModel] | None`, `json_path: str | None`, `docx_path: str | None`, `docx_assembler: Callable[..., str]`), `epic_news.crew_registry.CREW_REGISTRY: dict[str, CrewSpec]` (16 entries keyed by `CrewSpec.key`), `epic_news.crew_registry.STANDARD_CREWS: tuple[str, ...]`. `CrewCategories.UNKNOWN` and `CrewCategories.to_dict()` keep their names and return the same values as today.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_crew_registry.py`:

```python
"""One CrewSpec per crew: metadata only, consistent with the Flow (simplification S4)."""

import inspect
import re

from epic_news.crew_registry import CREW_REGISTRY, STANDARD_CREWS
from epic_news.main import ReceptionFlow
from epic_news.models.content_state import ContentState, CrewCategories

EXPECTED_KEYS = {
    "BOOK_SUMMARY",
    "COMPANY_NEWS",
    "COOKING",
    "DEEPRESEARCH",
    "FINDAILY",
    "HOLIDAY_PLANNER",
    "MEETING_PREP",
    "MENU",
    "NEWSDAILY",
    "OPEN_SOURCE_INTELLIGENCE",
    "PESTEL",
    "POEM",
    "RSS",
    "SAINT",
    "SALES_PROSPECTING",
    "SHOPPING",
}


def _router_branches() -> dict[str, str]:
    """selected_crew value -> returned step name, read from determine_crew's source."""
    source = inspect.getsource(ReceptionFlow.determine_crew)
    pairs = re.findall(r'selected_crew == "(\w+)":\s*return "(\w+)"', source)
    return dict(pairs)


def _listened_events() -> set[str]:
    events: set[str] = set()
    for member in vars(ReceptionFlow).values():
        definition = getattr(member, "__flow_method_definition__", None)
        trigger = getattr(definition, "trigger_methods", None) or getattr(member, "__trigger_methods__", None)
        if trigger:
            events |= {str(t) for t in trigger}
    return events


def test_registry_has_one_spec_per_crew():
    assert set(CREW_REGISTRY) == EXPECTED_KEYS
    for key, spec in CREW_REGISTRY.items():
        assert spec.key == key
        assert spec.title and spec.title.strip() == spec.title
        assert callable(spec.docx_assembler)
        for path in (spec.json_path, spec.docx_path):
            assert path is None or path.startswith("output/")
        assert spec.docx_path is None or spec.docx_path.endswith(".docx")
        assert spec.json_path is None or spec.json_path.endswith(".json")
    assert len({spec.title for spec in CREW_REGISTRY.values()}) == len(CREW_REGISTRY)


def test_standard_crews_have_every_field():
    assert set(STANDARD_CREWS) <= set(CREW_REGISTRY)
    for key in STANDARD_CREWS:
        spec = CREW_REGISTRY[key]
        assert spec.model_cls is not None and spec.json_path and spec.docx_path, key


def test_every_spec_has_a_router_branch_and_a_listener():
    branches = _router_branches()
    events = _listened_events()
    for key in CREW_REGISTRY:
        assert key in branches, f"determine_crew has no branch for {key}"
        assert branches[key] in events, f"no @listen for {branches[key]}"
    assert set(branches) == set(CREW_REGISTRY)


def test_categories_come_from_the_registry():
    expected = {key: key for key in CREW_REGISTRY} | {"UNKNOWN": "UNKNOWN"}
    assert CrewCategories.to_dict() == expected
    assert CrewCategories.UNKNOWN == "UNKNOWN"
    assert ContentState().categories == expected


def test_unregistered_key_routes_to_unknown():
    flow = ReceptionFlow(user_request="x")
    flow.state.selected_crew = "NOT_A_CREW"
    assert flow.determine_crew() == "go_unknown"
```

If `_listened_events` finds nothing because CrewAI 1.15.23 stores listener triggers under another attribute, read how `tests/test_flow_wiring.py` collects listener conditions (`_flow_methods`, `_string_leaves`) and use the same attribute. Keep the assertions.

In `tests/utils/test_report_utils.py`, replace the subject assertion at line 33 and add two tests below the existing ones. Use the fixture or `mock_state` construction that file already uses, and set `selected_crew` on it:

```python
    assert params["subject"] == f"Epic News — {CREW_REGISTRY[mock_state.selected_crew].title} : {mock_state.user_request}"
```

```python
def test_subject_falls_back_to_the_key_for_unknown_crews(mock_state):
    mock_state.selected_crew = "UNKNOWN"
    params = prepare_email_params(mock_state)
    assert params["subject"] == f"Epic News — UNKNOWN : {mock_state.user_request}"


def test_subject_handles_a_missing_crew(mock_state):
    mock_state.selected_crew = None
    params = prepare_email_params(mock_state)
    assert params["subject"] == f"Epic News — Rapport : {mock_state.user_request}"
```

(Import `CREW_REGISTRY` at the top of that test file. If `mock_state.selected_crew` is not a registered key in the existing fixture, set it to `"POEM"` in the first assertion's test.)

In `tests/crews/test_pestel_structure.py:65` and `tests/models/test_content_state.py:15`, replace `assert CrewCategories.PESTEL == "PESTEL"` with:

```python
    assert CrewCategories.to_dict()["PESTEL"] == "PESTEL"
```

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_crew_registry.py tests/utils/test_report_utils.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'epic_news.crew_registry'`.

- [ ] **Step 3: Create the registry**

Create `src/epic_news/crew_registry.py`:

```python
"""Crew metadata in one place (simplification S4).

One ``CrewSpec`` per crew: its routing key, report title, output model, JSON and DOCX
paths and DOCX assembler. Metadata only: routing stays in ``ReceptionFlow.determine_crew``
and every crew keeps its own ``@listen`` step. ``None`` marks a value the step computes
per run (a file named after the request) or does not have.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.models.crews.company_news_report import CompanyNewsReport
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.models.crews.shopping_advice_report import ShoppingAdviceOutput
from epic_news.utils.docx_report.crews.book_summary import assemble_book_summary_docx
from epic_news.utils.docx_report.crews.company_news import assemble_company_news_docx
from epic_news.utils.docx_report.crews.cooking import assemble_cooking_docx
from epic_news.utils.docx_report.crews.deep_research import assemble_deep_research_docx
from epic_news.utils.docx_report.crews.fin_daily import assemble_fin_daily_docx
from epic_news.utils.docx_report.crews.meeting_prep import assemble_meeting_prep_docx
from epic_news.utils.docx_report.crews.menu import assemble_menu_docx
from epic_news.utils.docx_report.crews.news_daily import assemble_news_daily_docx
from epic_news.utils.docx_report.crews.osint import assemble_osint_docx
from epic_news.utils.docx_report.crews.pestel import assemble_pestel_docx
from epic_news.utils.docx_report.crews.poem import assemble_poem_docx
from epic_news.utils.docx_report.crews.rss_weekly import assemble_rss_docx
from epic_news.utils.docx_report.crews.saint import assemble_saint_docx
from epic_news.utils.docx_report.crews.sales_prospecting import assemble_sales_prospecting_docx
from epic_news.utils.docx_report.crews.shopping import assemble_shopping_docx
from epic_news.utils.holiday_report import assemble_holiday_docx


@dataclass(frozen=True)
class CrewSpec:
    """Metadata for one crew. It does not route and does not run anything."""

    key: str
    title: str
    model_cls: type[BaseModel] | None
    json_path: str | None
    docx_path: str | None
    docx_assembler: Callable[..., str]


_SPECS = (
    CrewSpec("POEM", "Création poétique", PoemJSONOutput, "output/poem/poem.json", "output/poem/poem.docx", assemble_poem_docx),
    CrewSpec(
        "COMPANY_NEWS",
        "Actualités d'entreprise",
        CompanyNewsReport,
        "output/company_news/report.json",
        "output/company_news/report.docx",
        assemble_company_news_docx,
    ),
    CrewSpec(
        "FINDAILY",
        "Analyse financière quotidienne",
        FinancialReport,
        "output/findaily/report.json",
        "output/findaily/report.docx",
        assemble_fin_daily_docx,
    ),
    CrewSpec(
        "NEWSDAILY",
        "Revue de presse quotidienne",
        NewsDailyReport,
        "output/news_daily/news_data.json",
        "output/news_daily/report.docx",
        assemble_news_daily_docx,
    ),
    CrewSpec(
        "SAINT",
        "Saint du jour",
        SaintData,
        "output/saint_daily/report.json",
        "output/saint_daily/report.docx",
        assemble_saint_docx,
    ),
    CrewSpec(
        "BOOK_SUMMARY",
        "Analyse littéraire",
        BookSummaryReport,
        "output/library/book_summary.json",
        "output/library/book_summary.docx",
        assemble_book_summary_docx,
    ),
    CrewSpec(
        "MEETING_PREP",
        "Préparation de réunion",
        MeetingPrepReport,
        "output/meeting/meeting_preparation.json",
        "output/meeting/meeting_preparation.docx",
        assemble_meeting_prep_docx,
    ),
    CrewSpec(
        "SALES_PROSPECTING",
        "Prospection commerciale",
        SalesProspectingReport,
        "output/sales_prospecting/report.json",
        "output/sales_prospecting/report.docx",
        assemble_sales_prospecting_docx,
    ),
    CrewSpec(
        "PESTEL",
        "Analyse PESTEL",
        PestelReport,
        "output/pestel/report.json",
        "output/pestel/report.docx",
        assemble_pestel_docx,
    ),
    CrewSpec(
        "DEEPRESEARCH",
        "Recherche approfondie",
        DeepResearchReport,
        "output/deep_research/report.json",
        "output/deep_research/report.docx",
        assemble_deep_research_docx,
    ),
    CrewSpec(
        "RSS",
        "Synthèse RSS hebdomadaire",
        RssWeeklyReport,
        "output/rss_weekly/final-report.json",
        "output/rss_weekly/report.docx",
        assemble_rss_docx,
    ),
    CrewSpec("COOKING", "Recette", PaprikaRecipe, None, None, assemble_cooking_docx),
    CrewSpec("MENU", "Menu de la semaine", WeeklyMenuPlan, None, None, assemble_menu_docx),
    CrewSpec(
        "SHOPPING",
        "Conseil d'achat",
        ShoppingAdviceOutput,
        "output/shopping_advisor/shopping_advice.json",
        None,
        assemble_shopping_docx,
    ),
    CrewSpec(
        "HOLIDAY_PLANNER",
        "Planificateur de vacances",
        None,
        "output/holiday/itinerary.json",
        "output/holiday/itinerary.docx",
        assemble_holiday_docx,
    ),
    CrewSpec(
        "OPEN_SOURCE_INTELLIGENCE",
        "Intelligence open source",
        CrossReferenceReport,
        "output/osint/global_report.json",
        "output/osint/report.docx",
        assemble_osint_docx,
    ),
)

CREW_REGISTRY: dict[str, CrewSpec] = {spec.key: spec for spec in _SPECS}

# Crews whose Flow step runs through ReceptionFlow._run_standard.
STANDARD_CREWS: tuple[str, ...] = (
    "POEM",
    "COMPANY_NEWS",
    "FINDAILY",
    "NEWSDAILY",
    "SAINT",
    "BOOK_SUMMARY",
    "MEETING_PREP",
    "SALES_PROSPECTING",
    "PESTEL",
    "DEEPRESEARCH",
)
```

Before writing it, check each model import against the real class names (`grep -n "^class " src/epic_news/models/crews/menu_designer_report.py src/epic_news/models/crews/shopping_advice_report.py src/epic_news/models/crews/rss_weekly_report.py`). Check each path against the step in `main.py` that writes it (RSS: `translated_report_path`, main.py:468; shopping: main.py:857; holiday: main.py:1263 and 1293; OSINT: main.py:1227 and 1094). If a value differs, use the one in `main.py` and report it. `ruff format` may rewrite the one-line `CrewSpec(...)` entries; accept its output.

- [ ] **Step 4: Build the categories from the registry**

In `src/epic_news/models/content_state.py`, import `from epic_news.crew_registry import CREW_REGISTRY` at the top and replace the `CrewCategories` class with:

```python
class CrewCategories:
    """Crew categories: the registry keys plus UNKNOWN (simplification S4)."""

    UNKNOWN = "UNKNOWN"

    @classmethod
    def to_dict(cls) -> dict[str, str]:
        """Category name -> value, as the classifier and routing guide expect."""
        return {key: key for key in CREW_REGISTRY} | {cls.UNKNOWN: cls.UNKNOWN}
```

- [ ] **Step 5: Subject from the registry title**

In `src/epic_news/utils/report_utils.py`, import `from epic_news.crew_registry import CREW_REGISTRY` at the top and replace line 126 with:

```python
    crew = state.selected_crew
    title = CREW_REGISTRY[crew].title if crew in CREW_REGISTRY else (crew or "Rapport")
    subject = f"Epic News — {title} : {state.user_request}"
```

Leave `topic` (line 130) unchanged.

- [ ] **Step 6: Run the tests**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest tests/test_crew_registry.py tests/utils/test_report_utils.py tests/test_flow_wiring.py tests/test_determine_crew_router.py tests/crews/test_classify_config.py tests/models -q
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check . && uv run mypy src/epic_news
```
Expected: all PASS; ruff and mypy clean. If an import cycle appears, report the cycle (module chain) instead of moving imports inside functions.

- [ ] **Step 7: Commit**

```bash
git add src/epic_news/crew_registry.py src/epic_news/models/content_state.py src/epic_news/utils/report_utils.py tests
git commit -m "feat: crew registry holds crew metadata; categories and email subject read from it"
```

---

### Task 2: `_run_standard` and the ten standard steps

**Files:**
- Modify: `src/epic_news/main.py` (new method `_run_standard`; steps `generate_poem`, `generate_news_company`, `generate_findaily`, `generate_news_daily`, `generate_saint_daily`, `generate_book_summary`, `generate_meeting_prep`, `generate_sales_prospecting_report`, `generate_pestel`, `generate_deep_research`)
- Modify: tests that patch `main_module.assemble_pestel_docx` or `main_module.assemble_deep_research_docx` (find them with `grep -rn "assemble_pestel_docx\|assemble_deep_research_docx" tests`)
- Create: `tests/test_run_standard.py`

**Interfaces:**
- Consumes: Task 1's `CREW_REGISTRY`, `STANDARD_CREWS`, `CrewSpec`.
- Produces: `ReceptionFlow._run_standard(self, spec: CrewSpec, crew: Any, inputs: dict[str, Any]) -> tuple[Any, BaseModel]`, which returns `(crew_output, model)` and leaves `state.output_file` set to `spec.docx_path`.

- [ ] **Step 1: Write the failing helper tests**

Create `tests/test_run_standard.py`:

```python
"""ReceptionFlow._run_standard: the steps the standard crews share (simplification S4)."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.crew_registry import CREW_REGISTRY
from epic_news.main import ReceptionFlow

POEM = {"title": "Titre", "poem": "Vers un\nVers deux"}


@pytest.fixture
def flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ReceptionFlow:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    (tmp_path / "output" / "poem").mkdir(parents=True)
    monkeypatch.setattr(main_module, "dump_crewai_state", lambda *_a, **_k: None)
    return ReceptionFlow(user_request="un poème sur la mer")


def _spec_with(assembler):
    return dataclasses.replace(CREW_REGISTRY["POEM"], docx_assembler=assembler)


def test_writes_the_docx_and_returns_output_and_model(flow, monkeypatch):
    def _kickoff(_crew, inputs):
        Path(inputs["output_file"]).write_text(json.dumps(POEM), encoding="utf-8")
        return SimpleNamespace(raw=json.dumps(POEM), output=None)

    seen: dict = {}

    def _assemble(model, inputs, output_path, llm=None):
        seen["inputs"] = inputs
        Path(output_path).write_bytes(b"docx")
        return output_path

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    output, model = flow._run_standard(_spec_with(_assemble), object(), flow.state.to_crew_inputs())
    assert model.title == "Titre"
    assert output.raw == json.dumps(POEM)
    assert flow.state.output_file == "output/poem/poem.docx"
    assert seen["inputs"]["user_request"] == "un poème sur la mer"  # state inputs, not crew inputs
    assert "output_file" in seen["inputs"]


def test_stale_json_is_deleted_before_the_kickoff(flow, monkeypatch):
    stale = Path("output/poem/poem.json")
    stale.write_text(json.dumps({"title": "Ancien", "poem": "vieux"}), encoding="utf-8")
    built: list = []

    def _kickoff(_crew, _inputs):
        assert not stale.exists()
        return SimpleNamespace(raw="not json at all", output=None)

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    with pytest.raises(ValueError):
        flow._run_standard(_spec_with(lambda *a, **k: built.append(a)), object(), flow.state.to_crew_inputs())
    assert built == []


def test_mcp_is_closed_when_the_kickoff_fails(flow, monkeypatch):
    closed: list = []
    crew = object()

    def _kickoff(_crew, _inputs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    monkeypatch.setattr(main_module, "close_mcp", closed.append)
    with pytest.raises(RuntimeError, match="provider down"):
        flow._run_standard(CREW_REGISTRY["POEM"], crew, flow.state.to_crew_inputs())
    assert closed == [crew]
```

Check that `POEM` validates against `PoemJSONOutput` (`grep -n "class PoemJSONOutput" -A8 src/epic_news/models/crews/poem_report.py`). Adjust the dict keys to the model's required fields if they differ, and say so in your report.

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_run_standard.py -q`
Expected: FAIL with `AttributeError: 'ReceptionFlow' object has no attribute '_run_standard'`.

- [ ] **Step 3: Add the helper**

In `src/epic_news/main.py`, import `from epic_news.crew_registry import CREW_REGISTRY, CrewSpec` and `from pydantic import BaseModel` at the top (only what is missing), and add this method to `ReceptionFlow`, just above `determine_crew`:

```python
    def _run_standard(self, spec: CrewSpec, crew: Any, inputs: dict[str, Any]) -> tuple[Any, BaseModel]:
        """Run a standard crew: kickoff, debug dump, model from its JSON, DOCX report.

        A JSON left by an earlier run is deleted first so it is never read as this run's
        output; an MCP server the crew started is stopped even if the kickoff fails.
        Returns the raw crew output and the validated model.
        """
        if spec.model_cls is None or spec.json_path is None or spec.docx_path is None:
            raise ValueError(f"{spec.key} is not a standard crew (missing model or paths)")
        model_cls, json_path, docx_path = spec.model_cls, spec.json_path, spec.docx_path
        Path(json_path).unlink(missing_ok=True)
        self.state.output_file = json_path
        inputs["output_file"] = json_path
        try:
            output = kickoff_flow(crew, inputs)
        finally:
            # CrewBase stops an MCP server only after a successful kickoff.
            close_mcp(crew)
        dump_crewai_state(output, spec.key)
        model = load_or_parse_model(json_path, model_cls, output, inputs, spec.title)
        emit_report(self.state, lambda: spec.docx_assembler(model, self.state.to_crew_inputs(), docx_path))
        return output, model
```

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_run_standard.py -q`
Expected: PASS.

- [ ] **Step 4: Migrate the steps, one commit per crew**

Rewrite each step so that it keeps its decorators, docstring, input preparation and log lines, calls the helper, and stores its state fields. The two migrations below show the pattern; apply the same to the other eight. For each crew, read its current body and keep every line that prepares inputs (extra keys, fallbacks, log lines). Remove only: setting `state.output_file` / `inputs["output_file"]` to the JSON path, the `kickoff_flow` call (and its `try/finally close_mcp`), `dump_crewai_state`, `load_or_parse_model` and `emit_report`.

`generate_poem` becomes:

```python
    @listen("go_generate_poem")
    @trace_task(tracer)
    def generate_poem(self):
        """
        Handles requests classified for the 'PoemCrew'.

        Invokes the `PoemCrew` to generate a poem based on the provided topic.
        Sets `output_file` to `output/poem/poem.docx`.
        """
        inputs = self.state.to_crew_inputs()
        self.logger.info(f"Generating poem about: {inputs.get('topic', 'N/A')}")
        self._run_standard(CREW_REGISTRY["POEM"], PoemCrew(), inputs)
```

`generate_saint_daily` becomes:

```python
    @listen("go_generate_saint_daily")
    @trace_task(tracer)
    def generate_saint_daily(self):
        """
        (keep the existing docstring)
        """
        self.logger.info("⛪ Generating daily saint report in French...")
        output, saint_model = self._run_standard(
            CREW_REGISTRY["SAINT"], SaintDailyCrew(), self.state.to_crew_inputs()
        )
        self.state.saint_daily_report = output
        self.state.saint_daily_model = saint_model
        self.logger.info(f"✅ Saint content generated → {self.state.output_file}")
```

State fields each step must keep setting (from the current code):

| Step | Key | Crew | Keep |
|---|---|---|---|
| `generate_poem` | POEM | `PoemCrew()` | — |
| `generate_news_company` | COMPANY_NEWS | `CompanyNewsCrew()` | `state.company_news_report = output` |
| `generate_findaily` | FINDAILY | `FinDailyCrew()` | csv paths + `current_date` inputs; `state.fin_daily_report = output` |
| `generate_news_daily` | NEWSDAILY | `NewsDailyCrew()` | `current_date`, `report_language` inputs; `state.news_daily_report = output`; `state.news_daily_model = model` |
| `generate_saint_daily` | SAINT | `SaintDailyCrew()` | `state.saint_daily_report = output`; `state.saint_daily_model = model` |
| `generate_book_summary` | BOOK_SUMMARY | `LibraryCrew()` | `state.book_summary = output` |
| `generate_meeting_prep` | MEETING_PREP | `MeetingPrepCrew()` | company fallback; `state.meeting_prep_report = model` |
| `generate_sales_prospecting_report` | SALES_PROSPECTING | `SalesProspectingCrew()` | `our_product` default, company warning; no state field |
| `generate_pestel` | PESTEL | `PestelCrew()` | geography/language/current_date/recent_* inputs; `state.pestel_report = model` |
| `generate_deep_research` | DEEPRESEARCH | `DeepResearchCrew()` | `current_date` input; `state.deep_research_report = model` |

For PESTEL and deep research, the helper's `finally: close_mcp(crew)` replaces the step's own `try/finally`. For deep research, the step's own `Path(output_file).unlink(...)` goes (the helper does it), and its assembler now receives `self.state.to_crew_inputs()` like the others.

After each step: run `env -u VIRTUAL_ENV uv run pytest -q -x`. Tests that patched `main_module.assemble_pestel_docx` / `main_module.assemble_deep_research_docx` must now patch the registry entry instead:

```python
monkeypatch.setitem(
    crew_registry.CREW_REGISTRY,
    "PESTEL",
    dataclasses.replace(crew_registry.CREW_REGISTRY["PESTEL"], docx_assembler=_fake_assemble),
)
```

with `from epic_news import crew_registry` and `import dataclasses` at the top of that test file. Keep every assertion. Then commit:

```bash
git add src/epic_news/main.py tests
git commit -m "refactor(flow): <step> runs through _run_standard"
```

- [ ] **Step 5: Remove what the migration made unused**

Delete imports in `main.py` that no standard step uses any more. Candidates: the ten `assemble_*_docx` of the standard crews and their model classes, unless a custom step or `_run_cross_reference_report` still uses one. Let `uv run ruff check .` (F401) decide. Keep `CrewCategories`, which main.py:182/323 use.

- [ ] **Step 6: Verify**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check . && uv run mypy src/epic_news
wc -l src/epic_news/main.py
uvx radon cc -s -n C src/epic_news/main.py
```
Expected: all tests pass; ruff and mypy clean; report the `main.py` line count (it was 1,497) and any function at radon grade C or worse.

- [ ] **Step 7: Commit (if anything is left after Step 5)**

```bash
git add src/epic_news/main.py
git commit -m "refactor(flow): drop imports the standard-step migration left unused"
```

---

### Task 3: Docs

**Files:**
- Modify: `src/epic_news/utils/CLAUDE.md` ("Flow helpers" section: how a standard step is wired)
- Modify: root `CLAUDE.md` ("ReceptionFlow Pattern" section: mention `crew_registry.py` and `_run_standard`)
- Modify: `src/epic_news/crews/CLAUDE.md` only where it shows how to add a crew to the flow
- Modify: `docs/explanations/architecture.md` only where it describes the routing keys or the step body

**Interfaces:**
- Consumes: Task 1 (`CrewSpec`, `CREW_REGISTRY`, `STANDARD_CREWS`, categories from the registry, subject `Epic News — <title> : <request>`), Task 2 (`_run_standard(spec, crew, inputs) -> (output, model)`).

- [ ] **Step 1: Update the Flow helpers example**

In `src/epic_news/utils/CLAUDE.md`, replace the wiring example with:

```python
from epic_news.crew_registry import CREW_REGISTRY

@listen("go_generate_poem")
@trace_task(tracer)
def generate_poem(self):
    inputs = self.state.to_crew_inputs()
    self._run_standard(CREW_REGISTRY["POEM"], PoemCrew(), inputs)
```

Then add one paragraph: `_run_standard` deletes a stale JSON, runs `kickoff_flow` (closing MCP in a `finally`), dumps state, loads the model with `load_or_parse_model` and calls `emit_report` with the spec's assembler. It returns `(output, model)`. Custom steps (RSS, menu, recipe, shopping, OSINT, holiday) are written out.

- [ ] **Step 2: Add a crew, the new checklist**

In the root `CLAUDE.md` ReceptionFlow section (and `crews/CLAUDE.md` if it has an "add a crew" list), state the steps: add a `CrewSpec` to `crew_registry.py` (add the key to `STANDARD_CREWS` if the step is standard), a branch in `determine_crew`, a `@listen` step, and the step name in `send_email`'s `or_(...)`. `tests/test_crew_registry.py` checks the first three agree.

- [ ] **Step 3: Check and commit**

Run: `grep -rn "CrewCategories\|Epic News Report:" docs README.md CLAUDE.md src/epic_news/*/CLAUDE.md` and fix any statement made false by Task 1. Leave historical docs (`docs/superpowers/`, `docs/archive/`, `TODO.md`, `CHANGELOG.md`) alone.

```bash
git add CLAUDE.md src/epic_news docs
git commit -m "docs: crew registry and the standard-step helper (S4)"
```

Do not stage `docs/audits/` (untracked, must stay out of git).

---

Controller, before the PR: live run of one standard crew with `EPIC_ENABLE_EMAIL=false` (`env -u VIRTUAL_ENV uv run python scripts/bench_flow.py saint`), then compare wall clock and LiteLLM calls with the S5 saint run (276.3 s, 11 calls) in `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md`, and open the DOCX. In the PR description, report the `main.py` line count, the radon report and the five decisions listed at the top of this plan.
