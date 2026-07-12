# Holiday Report Fragments → DOCX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the holiday report's single giant `output_pydantic` LLM call with bounded Markdown fragments assembled into a DOCX by Pandoc, so the report never hits the per-call generation limit and degrades gracefully.

**Architecture:** The 4 research agents keep gathering info. Their per-task outputs feed a new fragment layer in the flow: one bounded LLM call per section, plus an itinerary skeleton call driving one call per day. Each call returns raw Markdown (a failed one yields a placeholder). Pandoc (`pypandoc-binary`) concatenates the fragments into a single DOCX with a table of contents, which the existing email step attaches.

**Tech Stack:** Python 3.13, CrewAI 1.15, `pypandoc-binary` (bundles the pandoc binary), Pydantic v2, pytest, `uv`.

## Global Constraints

- Python `>=3.13,<3.14`; use modern union syntax (`X | None`).
- Package manager is `uv` only (`uv add`, `uv run`). Never `pip`.
- LLM access only via `LLMConfig.get_openrouter_llm()` / `LLMConfig.get_timeout(...)`; never hardcode models/timeouts.
- Logging via `loguru` (`from loguru import logger`), never stdlib logging.
- All imports at top of file. No `os.makedirs` in crew/flow logic (use existing dir helpers).
- Scope: `holiday_planner` crew + its `ReceptionFlow.generate_holiday_plan` slice only. No other crew changes.
- New code must be cross-platform (macOS dev + Linux Docker); no system libs, no browser, no LaTeX.

---

## File Structure

- Create `src/epic_news/models/holiday_report.py` — `ItineraryDay`, `ItinerarySkeleton` Pydantic models.
- Create `src/epic_news/utils/holiday_report/__init__.py` — package exports.
- Create `src/epic_news/utils/holiday_report/docx_builder.py` — `build_docx(fragments, meta, output_path)` (deterministic, no LLM).
- Create `src/epic_news/utils/holiday_report/fragments.py` — `generate_fragment(spec, context)` (one bounded LLM call, placeholder on failure) + `FRAGMENT_SPECS`.
- Create `src/epic_news/utils/holiday_report/skeleton.py` — `generate_skeleton(context)` → `ItinerarySkeleton` with deterministic fallback.
- Create `src/epic_news/utils/holiday_report/assemble.py` — `assemble_holiday_docx(tasks_output, state_inputs, output_path)` orchestrator used by the flow.
- Modify `src/epic_news/crews/holiday_planner/holiday_planner_crew.py` — remove `content_formatter` agent + `format_and_translate_guide` task.
- Modify `src/epic_news/crews/holiday_planner/config/tasks.yaml` — remove `format_and_translate_guide`.
- Modify `src/epic_news/main.py:1358-1373` — replace parse/render/HTML with fragment→DOCX assembly.
- Tests under `tests/models/`, `tests/utils/holiday_report/`, `tests/flows/`.

Task order builds bottom-up: dependency → deterministic builder → models → LLM generators → orchestrator → crew trim → flow wiring.

---

### Task 1: Add `pypandoc-binary` and prove Markdown→DOCX works

**Files:**
- Modify: `pyproject.toml` (deps), `uv.lock`
- Test: `tests/utils/holiday_report/test_pandoc_available.py`

**Interfaces:**
- Produces: a working `pypandoc` import that converts Markdown to a `.docx` file on this platform.

- [ ] **Step 1: Add the dependency**

Run: `uv add pypandoc-binary`
Expected: `pyproject.toml` gains `pypandoc-binary`, `uv.lock` updated.

- [ ] **Step 2: Write the failing test**

```python
# tests/utils/holiday_report/test_pandoc_available.py
from pathlib import Path

import pypandoc


def test_pandoc_markdown_to_docx(tmp_path: Path):
    out = tmp_path / "out.docx"
    pypandoc.convert_text(
        "# Title\n\nHello **world**.",
        to="docx",
        format="markdown",
        outputfile=str(out),
    )
    assert out.exists()
    assert out.stat().st_size > 0
```

- [ ] **Step 3: Run test to verify it fails (before `uv add`) or passes (after)**

Run: `uv run pytest tests/utils/holiday_report/test_pandoc_available.py -v`
Expected: PASS once `pypandoc-binary` is installed (the bundled binary needs no system pandoc).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock tests/utils/holiday_report/test_pandoc_available.py
git commit -m "build(holiday): add pypandoc-binary for DOCX report generation"
```

---

### Task 2: `build_docx` — deterministic fragment → DOCX assembler

**Files:**
- Create: `src/epic_news/utils/holiday_report/__init__.py`
- Create: `src/epic_news/utils/holiday_report/docx_builder.py`
- Test: `tests/utils/holiday_report/test_docx_builder.py`

**Interfaces:**
- Produces: `build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str`
  where `fragments` is an ordered list of `(heading, markdown_body)`; returns `output_path`.

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/holiday_report/test_docx_builder.py
from pathlib import Path

from docx import Document  # python-docx, already transitively available; else add in this task

from epic_news.utils.holiday_report.docx_builder import build_docx


def test_build_docx_writes_headings_and_body(tmp_path: Path):
    out = tmp_path / "guide.docx"
    fragments = [
        ("Introduction", "Bienvenue à **Montreux**."),
        ("Jour 1", "- Départ\n- Route"),
    ]
    result = build_docx(fragments, {"title": "Carnet", "date": "2026-07-16"}, str(out))

    assert result == str(out)
    assert out.exists() and out.stat().st_size > 0
    text = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "Introduction" in text
    assert "Jour 1" in text
    assert "Montreux" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/holiday_report/test_docx_builder.py -v`
Expected: FAIL with `ModuleNotFoundError: epic_news.utils.holiday_report`.

- [ ] **Step 3: Write the implementation**

```python
# src/epic_news/utils/holiday_report/__init__.py
```

```python
# src/epic_news/utils/holiday_report/docx_builder.py
"""Deterministic assembly of Markdown fragments into a single DOCX via Pandoc."""

from pathlib import Path

import pypandoc
from loguru import logger


def build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str:
    """Assemble ordered (heading, markdown_body) fragments into a DOCX with a TOC.

    Each fragment becomes a top-level (H1) section. Deterministic: no LLM, no network.
    """
    title = meta.get("title", "Guide")
    date = meta.get("date", "")

    parts: list[str] = [f"% {title}", f"% {meta.get('author', '')}", f"% {date}", ""]
    for heading, body in fragments:
        parts.append(f"# {heading}\n")
        parts.append(body.strip() + "\n")
    markdown = "\n".join(parts)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    extra_args = ["--toc", "--standalone"]
    pypandoc.convert_text(
        markdown, to="docx", format="markdown", outputfile=output_path, extra_args=extra_args
    )
    logger.info("📄 Holiday DOCX written to {}", output_path)
    return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/holiday_report/test_docx_builder.py -v`
Expected: PASS. (If `python-docx` is missing, `uv add python-docx` first and include it in the commit.)

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/holiday_report/ tests/utils/holiday_report/test_docx_builder.py pyproject.toml uv.lock
git commit -m "feat(holiday): deterministic Markdown fragments -> DOCX builder"
```

---

### Task 3: Itinerary skeleton model + generator with deterministic fallback

**Files:**
- Create: `src/epic_news/models/holiday_report.py`
- Create: `src/epic_news/utils/holiday_report/skeleton.py`
- Test: `tests/utils/holiday_report/test_skeleton.py`

**Interfaces:**
- Produces:
  - `ItineraryDay(date: str, label: str, stops: list[str])`
  - `ItinerarySkeleton(days: list[ItineraryDay])`
  - `generate_skeleton(itinerary_research: str, trip_summary: str, llm) -> ItinerarySkeleton`
    (`llm` is a `LLMConfig.get_openrouter_llm()` instance; falls back to a one-day skeleton if the model output cannot be parsed.)

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/holiday_report/test_skeleton.py
from epic_news.models.holiday_report import ItinerarySkeleton
from epic_news.utils.holiday_report.skeleton import generate_skeleton


class FakeLLM:
    def __init__(self, reply: str):
        self._reply = reply

    def call(self, messages):
        return self._reply


def test_skeleton_parses_json_day_list():
    reply = (
        '[{"date": "2026-07-16", "label": "Montreux -> Montpellier", "stops": ["Montreux"]},'
        ' {"date": "2026-07-17", "label": "Montpellier", "stops": ["Castries"]}]'
    )
    sk = generate_skeleton("research", "summary", FakeLLM(reply))
    assert isinstance(sk, ItinerarySkeleton)
    assert len(sk.days) == 2
    assert sk.days[0].label.startswith("Montreux")


def test_skeleton_falls_back_on_bad_output():
    sk = generate_skeleton("research", "summary", FakeLLM("not json at all"))
    assert isinstance(sk, ItinerarySkeleton)
    assert len(sk.days) == 1  # deterministic single-day fallback
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/holiday_report/test_skeleton.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write the models and generator**

```python
# src/epic_news/models/holiday_report.py
"""Small, bounded models for the fragment-based holiday report."""

from pydantic import BaseModel, Field


class ItineraryDay(BaseModel):
    date: str = Field(default="", description="Human date label for the day")
    label: str = Field(default="", description="Short title for the day")
    stops: list[str] = Field(default_factory=list, description="Key stops/locations")


class ItinerarySkeleton(BaseModel):
    days: list[ItineraryDay] = Field(default_factory=list)
```

```python
# src/epic_news/utils/holiday_report/skeleton.py
"""Generate a small, bounded day-by-day skeleton that drives per-day fragment calls."""

import json
from typing import Any

from loguru import logger

from epic_news.models.holiday_report import ItineraryDay, ItinerarySkeleton

_PROMPT = (
    "Tu es un planificateur de voyage. À partir du résumé et de la recherche d'itinéraire, "
    "renvoie UNIQUEMENT un tableau JSON compact, un objet par jour, champs: "
    '"date" (str), "label" (str court), "stops" (liste de str). Pas de texte autour du JSON.'
)


def generate_skeleton(itinerary_research: str, trip_summary: str, llm: Any) -> ItinerarySkeleton:
    """Ask the LLM for a compact day list; fall back to a single day if parsing fails."""
    messages = [
        {"role": "system", "content": _PROMPT},
        {"role": "user", "content": f"Résumé:\n{trip_summary}\n\nRecherche itinéraire:\n{itinerary_research}"},
    ]
    try:
        raw = llm.call(messages)
        payload = json.loads(_extract_json_array(raw))
        days = [ItineraryDay.model_validate(d) for d in payload]
        if days:
            return ItinerarySkeleton(days=days)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Itinerary skeleton parse failed ({}); using single-day fallback", exc)
    return ItinerarySkeleton(days=[ItineraryDay(label="Itinéraire complet", stops=[])])


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found")
    return text[start : end + 1]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/holiday_report/test_skeleton.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/models/holiday_report.py src/epic_news/utils/holiday_report/skeleton.py tests/utils/holiday_report/test_skeleton.py
git commit -m "feat(holiday): itinerary skeleton generator with deterministic fallback"
```

---

### Task 4: `generate_fragment` — one bounded Markdown fragment, placeholder on failure

**Files:**
- Create: `src/epic_news/utils/holiday_report/fragments.py`
- Test: `tests/utils/holiday_report/test_fragments.py`

**Interfaces:**
- Consumes: `llm` (from `LLMConfig.get_openrouter_llm()`), with a `.call(messages) -> str` method.
- Produces: `generate_fragment(heading: str, instruction: str, context: str, llm) -> str`
  (returns Markdown on success; a placeholder Markdown block on any exception/empty output).

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/holiday_report/test_fragments.py
from epic_news.utils.holiday_report.fragments import generate_fragment


class OkLLM:
    def call(self, messages):
        return "Contenu **riche** en Markdown."


class FailLLM:
    def call(self, messages):
        raise TimeoutError("provider timed out")


class EmptyLLM:
    def call(self, messages):
        return "   "


def test_fragment_returns_markdown_on_success():
    md = generate_fragment("Restauration", "Liste les restaurants.", "recherche", OkLLM())
    assert "Markdown" in md


def test_fragment_returns_placeholder_on_failure():
    md = generate_fragment("Budget", "Détaille le budget.", "recherche", FailLLM())
    assert "indisponible" in md.lower()


def test_fragment_returns_placeholder_on_empty():
    md = generate_fragment("Budget", "Détaille le budget.", "recherche", EmptyLLM())
    assert "indisponible" in md.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/holiday_report/test_fragments.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

```python
# src/epic_news/utils/holiday_report/fragments.py
"""Bounded per-section Markdown fragment generation for the holiday report."""

from typing import Any

from loguru import logger

_SYSTEM = (
    "Tu es un rédacteur de carnet de voyage. Rédige UNIQUEMENT la section demandée, "
    "en français, en Markdown propre (titres de niveau 2+, listes, gras, emojis). "
    "Pas de HTML, pas de JSON, pas de préambule."
)


def generate_fragment(heading: str, instruction: str, context: str, llm: Any) -> str:
    """Generate one Markdown section. On any failure/empty result, return a placeholder."""
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Section: {heading}\n\nConsigne: {instruction}\n\nContexte:\n{context}"},
    ]
    try:
        md = (llm.call(messages) or "").strip()
        if md:
            return md
        logger.warning("⚠️ Fragment '{}' returned empty; using placeholder", heading)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Fragment '{}' failed ({}); using placeholder", heading, exc)
    return f"> ⚠️ Section « {heading} » indisponible pour ce voyage."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/holiday_report/test_fragments.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/holiday_report/fragments.py tests/utils/holiday_report/test_fragments.py
git commit -m "feat(holiday): bounded Markdown fragment generator with placeholder fallback"
```

---

### Task 5: `assemble_holiday_docx` — orchestrate research outputs → fragments → DOCX

**Files:**
- Create: `src/epic_news/utils/holiday_report/assemble.py`
- Modify: `src/epic_news/utils/holiday_report/__init__.py` (export `assemble_holiday_docx`)
- Test: `tests/utils/holiday_report/test_assemble.py`

**Interfaces:**
- Consumes: `build_docx`, `generate_fragment`, `generate_skeleton`; a `crew_result` exposing
  `.tasks_output` (list of objects with `.raw: str`, CrewAI order:
  research_destination, recommend_accommodation_and_dining, plan_itinerary, analyze_and_optimize_budget).
- Produces: `assemble_holiday_docx(crew_result, inputs: dict, output_path: str, llm=None) -> str`
  (returns the DOCX path; builds section fragments + one fragment per skeleton day).

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/holiday_report/test_assemble.py
from pathlib import Path
from types import SimpleNamespace

from docx import Document

from epic_news.utils.holiday_report import assemble_holiday_docx


class StubLLM:
    """Returns a day-list for the skeleton call, Markdown for everything else."""

    def call(self, messages):
        user = messages[-1]["content"]
        if "date" in messages[0]["content"] and "stops" in messages[0]["content"]:
            return '[{"date":"J1","label":"Montreux","stops":["Montreux"]}]'
        return f"## Section\nContenu pour: {user[:20]}"


def _crew_result():
    outs = ["destination research", "accommodation+dining", "itinerary", "budget"]
    return SimpleNamespace(tasks_output=[SimpleNamespace(raw=o) for o in outs])


def test_assemble_builds_docx_with_sections_and_days(tmp_path: Path):
    out = tmp_path / "guide.docx"
    inputs = {"destination": "France", "duration": "2 semaines", "family": "3", "origin": "Montreux",
              "user_preferences_and_constraints": "nature"}
    path = assemble_holiday_docx(_crew_result(), inputs, str(out), llm=StubLLM())
    assert path == str(out)
    text = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "Introduction" in text
    assert "Itinéraire" in text  # at least one day section
    assert "Budget" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/holiday_report/test_assemble.py -v`
Expected: FAIL (`assemble_holiday_docx` not importable).

- [ ] **Step 3: Write the orchestrator**

```python
# src/epic_news/utils/holiday_report/assemble.py
"""Turn holiday research outputs into a DOCX via bounded fragments."""

from typing import Any

from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.utils.holiday_report.docx_builder import build_docx
from epic_news.utils.holiday_report.fragments import generate_fragment
from epic_news.utils.holiday_report.skeleton import generate_skeleton


def _task_raw(crew_result: Any, index: int) -> str:
    try:
        return crew_result.tasks_output[index].raw or ""
    except (AttributeError, IndexError, TypeError):
        return ""


def _trip_summary(inputs: dict) -> str:
    return (
        f"Voyage: {inputs.get('family', '')} — {inputs.get('origin', '')} — "
        f"{inputs.get('duration', '')} — {inputs.get('destination', '')}. "
        f"Préférences: {inputs.get('user_preferences_and_constraints', '')}"
    )


def assemble_holiday_docx(crew_result: Any, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the holiday DOCX from research outputs using bounded fragment calls."""
    llm = llm or LLMConfig.get_openrouter_llm()
    summary = _trip_summary(inputs)

    destination = _task_raw(crew_result, 0)
    lodging_dining = _task_raw(crew_result, 1)
    itinerary = _task_raw(crew_result, 2)
    budget = _task_raw(crew_result, 3)

    fragments: list[tuple[str, str]] = []
    fragments.append(("Introduction", generate_fragment(
        "Introduction", "Présente le voyage, la culture et les points forts.",
        f"{summary}\n\n{destination}", llm)))

    # Itinerary: skeleton then one fragment per day (bounded regardless of trip length).
    skeleton = generate_skeleton(itinerary, summary, llm)
    logger.info("🗓️ Itinerary skeleton: {} day(s)", len(skeleton.days))
    for i, day in enumerate(skeleton.days, start=1):
        heading = f"Itinéraire — Jour {i}" + (f" ({day.date})" if day.date else "")
        fragments.append((heading, generate_fragment(
            heading,
            f"Détaille cette journée: {day.label}. Étapes: {', '.join(day.stops) or 'à préciser'}.",
            f"{summary}\n\nRecherche itinéraire:\n{itinerary}", llm)))

    fragments.append(("Hébergements", generate_fragment(
        "Hébergements", "Liste les hébergements recommandés avec adresse et fourchette de prix.",
        f"{summary}\n\n{lodging_dining}", llm)))
    fragments.append(("Restauration", generate_fragment(
        "Restauration", "Recommande restaurants et spécialités par étape.",
        f"{summary}\n\n{lodging_dining}", llm)))
    fragments.append(("Budget", generate_fragment(
        "Budget", "Détaille un budget en CHF, par catégorie, avec total.",
        f"{summary}\n\n{budget}", llm)))
    fragments.append(("Informations pratiques", generate_fragment(
        "Informations pratiques", "Checklist bagages, sécurité, contacts d'urgence, phrases utiles.",
        f"{summary}\n\n{destination}", llm)))

    meta = {"title": f"Carnet de voyage — {inputs.get('destination', '')}",
            "date": inputs.get("current_date", ""), "author": "Epic News"}
    return build_docx(fragments, meta, output_path)
```

Add to `__init__.py`:

```python
# src/epic_news/utils/holiday_report/__init__.py
from epic_news.utils.holiday_report.assemble import assemble_holiday_docx

__all__ = ["assemble_holiday_docx"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/utils/holiday_report/test_assemble.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/holiday_report/assemble.py src/epic_news/utils/holiday_report/__init__.py tests/utils/holiday_report/test_assemble.py
git commit -m "feat(holiday): assemble research outputs into fragment-based DOCX"
```

---

### Task 6: Trim the holiday crew — drop the giant final task

**Files:**
- Modify: `src/epic_news/crews/holiday_planner/holiday_planner_crew.py` (remove `content_formatter` agent + `format_and_translate_guide` task)
- Modify: `src/epic_news/crews/holiday_planner/config/tasks.yaml` (remove `format_and_translate_guide`)
- Test: `tests/crews/test_holiday_planner_structure.py` (create or update)

**Interfaces:**
- Produces: a `HolidayPlannerCrew` whose `.crew()` runs exactly the 4 research tasks; the crew
  result's `.tasks_output` has 4 entries in the order Task 5 consumes.

- [ ] **Step 1: Write the failing test**

```python
# tests/crews/test_holiday_planner_structure.py
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew


def test_holiday_crew_has_no_content_formatter():
    crew = HolidayPlannerCrew()
    assert not hasattr(crew, "content_formatter")
    built = crew.crew()
    assert len(built.tasks) == 4  # research tasks only, no mega-format task
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/crews/test_holiday_planner_structure.py -v`
Expected: FAIL (5 tasks / `content_formatter` present).

- [ ] **Step 3: Remove the agent and task**

In `holiday_planner_crew.py`: delete the `content_formatter` `@agent` method and the
`format_and_translate_guide` `@task` method. Remove now-unused imports (e.g. the report model,
`get_*_tools` only used by the removed agent — keep those still used by the 4 research agents).

In `config/tasks.yaml`: delete the entire `format_and_translate_guide:` block.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/crews/test_holiday_planner_structure.py -v`
Expected: PASS. Also run `uv run ruff check src/epic_news/crews/holiday_planner/holiday_planner_crew.py` → no unused-import errors.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/crews/holiday_planner/holiday_planner_crew.py src/epic_news/crews/holiday_planner/config/tasks.yaml tests/crews/test_holiday_planner_structure.py
git commit -m "refactor(holiday): drop giant format task; crew is research-only"
```

---

### Task 7: Wire the flow — DOCX assembly + DOCX attachment

**Files:**
- Modify: `src/epic_news/main.py:1358-1373` (inside `generate_holiday_plan`)
- Test: `tests/flows/test_generate_holiday_plan_docx.py`

**Interfaces:**
- Consumes: `assemble_holiday_docx` (Task 5), `kickoff_flow` (unchanged), `self.state.output_file`.
- Produces: `self.state.output_file` points to `output/holiday/itinerary.docx`; `send_email` attaches it unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/flows/test_generate_holiday_plan_docx.py
from types import SimpleNamespace
from unittest.mock import patch

from epic_news.main import ReceptionFlow


def test_generate_holiday_plan_sets_docx_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    flow = ReceptionFlow(user_request="x")
    flow.state.selected_crew = "HOLIDAY_PLANNER"
    flow.state.enriched_brief = "Voyage en France"

    crew_result = SimpleNamespace(tasks_output=[SimpleNamespace(raw="r") for _ in range(4)])

    with (
        patch("epic_news.main.kickoff_flow", return_value=crew_result),
        patch("epic_news.main.dump_crewai_state"),
        patch("epic_news.main.assemble_holiday_docx", return_value="output/holiday/itinerary.docx") as asm,
    ):
        flow.generate_holiday_plan()

    asm.assert_called_once()
    assert flow.state.output_file.endswith("itinerary.docx")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/flows/test_generate_holiday_plan_docx.py -v`
Expected: FAIL (`assemble_holiday_docx` not imported in main; output_file still `.html`).

- [ ] **Step 3: Edit `generate_holiday_plan`**

Add import at top of `main.py` (with the other `epic_news.utils` imports):

```python
from epic_news.utils.holiday_report import assemble_holiday_docx
```

Replace the block at `main.py:1358-1373` (`kickoff_flow` → return) with:

```python
        # Run the research crew (no giant format task); then assemble a DOCX from bounded fragments.
        crew_result = kickoff_flow(HolidayPlannerCrew(), current_inputs)
        dump_crewai_state(crew_result, "HOLIDAY_PLANNER")

        docx_file = "output/holiday/itinerary.docx"
        assemble_holiday_docx(crew_result, current_inputs, docx_file)
        self.state.output_file = docx_file
        self.state.holiday_plan = crew_result
        return "generate_holiday_plan"
```

Remove the now-unused `HolidayPlannerReport` import and `render_and_write_html`/`load_or_parse_model`
usage *for this method only* (leave them if other methods still use them — verify with grep).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/flows/test_generate_holiday_plan_docx.py -v`
Expected: PASS. Then `uv run ruff check src/epic_news/main.py`.

- [ ] **Step 5: Full holiday + report suite regression**

Run: `uv run pytest tests/flows/ tests/utils/holiday_report/ tests/crews/test_holiday_planner_structure.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/main.py tests/flows/test_generate_holiday_plan_docx.py
git commit -m "feat(holiday): generate DOCX travel guide from fragments and attach it"
```

---

### Task 8: Docker — ensure the Linux pandoc wheel resolves

**Files:**
- Modify: `uv.lock` (verify), `Dockerfile` (only if the build cannot resolve the wheel)
- Test: manual build check

**Interfaces:** none (deployment).

- [ ] **Step 1: Verify multi-platform lock**

Run: `uv lock --check` and confirm `pypandoc-binary` has a Linux wheel entry in `uv.lock`.
Expected: lock is consistent and includes the manylinux wheel (pandoc bundled → no apt needed).

- [ ] **Step 2: Build the image**

Run: `make docker-build-all` (or the holiday-relevant image target).
Expected: build succeeds; no missing-pandoc error. If the wheel is absent for the target arch,
add `RUN apt-get update && apt-get install -y --no-install-recommends pandoc` to the Dockerfile
as a fallback and re-run.

- [ ] **Step 3: Commit (only if Dockerfile changed)**

```bash
git add Dockerfile uv.lock
git commit -m "build(holiday): ensure pandoc available in Docker image"
```

---

## Self-Review

**Spec coverage:**
- Fragment generation (sections + per-day) → Tasks 4, 5. ✅
- Markdown (not JSON) generation format → Tasks 3 (`_extract_json_array` only for the small skeleton), 4 (raw MD). ✅
- Pandoc→DOCX via pypandoc-binary → Tasks 1, 2. ✅
- Graceful degradation / placeholder → Tasks 3 (fallback), 4 (placeholder). ✅
- Email attaches DOCX → Task 7 (`state.output_file`). ✅
- Cross-platform, no system libs → Tasks 1, 8. ✅
- Retire content_formatter/format task/HolidayPlannerReport/HTML render → Tasks 6, 7. ✅
- Itinerary skeleton = small structured day list → Task 3. ✅
- Scope holiday-only → no other crew touched. ✅

**Placeholder scan:** No "TBD/TODO"; every code step has real code. Task 6 describes deletions (no code block needed for removal) with exact targets. Task 8 has a conditional Dockerfile line with exact command.

**Type consistency:** `generate_fragment(heading, instruction, context, llm) -> str`,
`generate_skeleton(itinerary_research, trip_summary, llm) -> ItinerarySkeleton`,
`build_docx(fragments: list[tuple[str,str]], meta, output_path) -> str`,
`assemble_holiday_docx(crew_result, inputs, output_path, llm=None) -> str` — used consistently
across Tasks 2–7. `ItineraryDay`/`ItinerarySkeleton` fields (`date`, `label`, `stops`, `days`)
match between model, generator, and orchestrator.

**Note for implementer:** `python-docx` (imported as `docx`) is used only in tests to assert DOCX
contents; if not already present, `uv add --group dev python-docx` in Task 2.
