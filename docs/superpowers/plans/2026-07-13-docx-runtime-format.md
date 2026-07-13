# DOCX Runtime Format Selection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DOCX a first-class, on-demand output for every routable crew (except POEM) without losing any crew's HTML — HTML stays the default, a request opts into DOCX at run time, and each crew gains a bespoke DOCX assembler on a shared framework factored from holiday.

**Architecture:** A shared `docx_report` package (Pandoc fragment engine + LLM narration + deterministic sections) factored out of `holiday_report`; a runtime format resolver (`OUTPUT_FORMAT` flag > parsed request intent > default HTML); one `assemble_{crew}_docx` per crew; and a dispatch that runs the assembler when DOCX is requested, else the existing HTML path.

**Tech Stack:** Python 3.13, pypandoc/Pandoc, python (dataclasses), Loguru, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-07-13-docx-runtime-format-design.md`

## Global Constraints

- **Package manager: `uv` only** (`uv run pytest`, `uv add`). Never pip/poetry.
- **`src/epic_news/main.py` is the SENTINEL FILE** — it holds the user's uncommitted personal query edit. Implementer subagents MUST NOT edit or `git add` main.py. All main.py edits (the `classify` parser call and the per-crew dispatch call sites) are **controller-only, sentinel-safe surgery** (stash sentinel → edit → commit → restore), grouped into the tasks explicitly marked **[CONTROLLER]**.
- **Logging: Loguru** (`from loguru import logger`), never stdlib logging.
- **Types: Python 3.13 unions** (`X | None`, `X | Y`).
- **TDD**: write the failing test, watch it fail, implement, watch it pass, commit.
- **Renderers/assemblers consume `model.model_dump()`** where a model is passed (the existing HTML path bypasses `to_template_data()`); assemblers receive the crew's model and/or `crew_result` explicitly.
- **LLM must never re-type precise data** (figures, prices, quantities, feed URLs, ingredient amounts) — those sections are **deterministic** Markdown built from the model.
- **LLM access** is via `LLMConfig.get_openrouter_llm()`; narration uses `llm.call(messages)`.
- Lint/type: `uv run ruff check --fix .`, `uv run ruff format .`, `uv run mypy src/epic_news` must pass before each commit.

---

## Phase 1 — Foundation (independently shippable: DOCX works for holiday + 2 reference crews)

### Task 1: `docx_report` framework package — the Section model + assemble engine

**Files:**
- Create: `src/epic_news/utils/docx_report/__init__.py`
- Create: `src/epic_news/utils/docx_report/docx_builder.py`
- Create: `src/epic_news/utils/docx_report/fragments.py`
- Create: `src/epic_news/utils/docx_report/sections.py`
- Create: `src/epic_news/utils/docx_report/assemble.py`
- Test: `tests/utils/docx_report/test_assemble.py`

**Interfaces:**
- Produces:
  - `Section(heading: str, instruction: str | None = None, context: str | None = None, body: str | None = None)` — a dataclass. `body is not None` → deterministic (used verbatim); else narrated (from `instruction`+`context`).
  - `build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str`
  - `generate_fragment(heading: str, instruction: str, context: str, llm, system: str) -> str`
  - `assemble_fragments(sections: list[Section], meta: dict[str, str], output_path: str, llm, system: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/docx_report/test_assemble.py
import zipfile
from epic_news.utils.docx_report import Section, assemble_fragments


class _StubLLM:
    def __init__(self):
        self.calls = []

    def call(self, messages):
        self.calls.append(messages)
        return f"## Narrated\n\nprose for {messages[1]['content'][:20]}"


def _docx_text(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def test_deterministic_section_makes_no_llm_call(tmp_path):
    llm = _StubLLM()
    out = assemble_fragments(
        [Section("Prix", body="| Item | CHF |\n|---|---|\n| A | 9.90 |")],
        {"title": "T", "author": "Epic News", "date": "2026-07-13"},
        str(tmp_path / "r.docx"),
        llm,
        system="sys",
    )
    assert out.endswith("r.docx")
    assert llm.calls == []                       # deterministic → no narration
    assert "9.90" in _docx_text(out)             # exact value preserved


def test_narrated_section_calls_llm(tmp_path):
    llm = _StubLLM()
    assemble_fragments(
        [Section("Intro", instruction="Présente.", context="ctx")],
        {"title": "T", "author": "Epic News", "date": ""},
        str(tmp_path / "n.docx"),
        llm,
        system="sys",
    )
    assert len(llm.calls) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/utils/docx_report/test_assemble.py -v`
Expected: FAIL (module `epic_news.utils.docx_report` does not exist).

- [ ] **Step 3: Write the implementation**

`sections.py`:
```python
"""Section spec for DOCX assembly: narrated (LLM) or deterministic (verbatim body)."""

from dataclasses import dataclass


@dataclass
class Section:
    """One report section. `body` set → used verbatim (deterministic, no LLM).
    Otherwise narrated from `instruction` + `context`."""

    heading: str
    instruction: str | None = None
    context: str | None = None
    body: str | None = None
```

`docx_builder.py` (moved from `holiday_report/docx_builder.py`, plus optional reference doc):
```python
"""Deterministic assembly of Markdown fragments into a single DOCX via Pandoc."""

from pathlib import Path

import pypandoc
from loguru import logger

_REFERENCE_DOC = Path(__file__).parent / "reference.docx"


def build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str:
    """Assemble ordered (heading, markdown_body) fragments into a DOCX with a TOC.

    Each fragment becomes a top-level (H1) section. Deterministic: no LLM, no network.
    """
    title = meta.get("title", "Rapport")
    date = meta.get("date", "")
    parts: list[str] = [f"% {title}", f"% {meta.get('author', 'Epic News')}", f"% {date}", ""]
    for heading, body in fragments:
        parts.append(f"# {heading}\n")
        parts.append((body or "").strip() + "\n")
    markdown = "\n".join(parts)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    extra_args = ["--toc", "--standalone"]
    if _REFERENCE_DOC.exists():
        extra_args += ["--reference-doc", str(_REFERENCE_DOC)]
    # LLM fragment bodies use `---` as separators. Disable yaml_metadata_block so every
    # `---` stays a thematic break (otherwise Pandoc dies with exitcode 64).
    pypandoc.convert_text(
        markdown,
        to="docx",
        format="markdown-yaml_metadata_block",
        outputfile=output_path,
        extra_args=extra_args,
    )
    logger.info("📄 DOCX written to {}", output_path)
    return output_path
```

`fragments.py` (factored from `holiday_report/fragments.py`, `system` is now a parameter):
```python
"""Bounded per-section Markdown fragment generation via an LLM."""

from typing import Any

from loguru import logger


def generate_fragment(heading: str, instruction: str, context: str, llm: Any, system: str) -> str:
    """Generate one Markdown section. On any failure/empty result, return a placeholder."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Section: {heading}\n\nConsigne: {instruction}\n\nContexte:\n{context}"},
    ]
    try:
        md = (llm.call(messages) or "").strip()
        if md:
            return md
        logger.warning("⚠️ Fragment '{}' returned empty; using placeholder", heading)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Fragment '{}' failed ({}); using placeholder", heading, exc)
    return f"> ⚠️ Section « {heading} » indisponible."
```

`assemble.py`:
```python
"""Turn a list of Section specs into a DOCX, narrating or passing through per section."""

from typing import Any

from epic_news.utils.docx_report.docx_builder import build_docx
from epic_news.utils.docx_report.fragments import generate_fragment
from epic_news.utils.docx_report.sections import Section


def assemble_fragments(
    sections: list[Section], meta: dict[str, str], output_path: str, llm: Any, system: str
) -> str:
    """Render each Section (deterministic body verbatim, else LLM-narrated) → DOCX."""
    fragments: list[tuple[str, str]] = []
    for s in sections:
        if s.body is not None:
            fragments.append((s.heading, s.body))
        else:
            fragments.append(
                (s.heading, generate_fragment(s.heading, s.instruction or "", s.context or "", llm, system))
            )
    return build_docx(fragments, meta, output_path)
```

`__init__.py`:
```python
from epic_news.utils.docx_report.assemble import assemble_fragments
from epic_news.utils.docx_report.docx_builder import build_docx
from epic_news.utils.docx_report.fragments import generate_fragment
from epic_news.utils.docx_report.sections import Section

__all__ = ["Section", "assemble_fragments", "build_docx", "generate_fragment"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/utils/docx_report/test_assemble.py -v` → PASS.

- [ ] **Step 5: Lint, type, commit**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy src/epic_news/utils/docx_report
git add src/epic_news/utils/docx_report tests/utils/docx_report
git commit -m "feat(docx): shared docx_report framework (Section, assemble_fragments, build_docx)"
```

### Task 2: Refactor `holiday_report` onto `docx_report`

**Files:**
- Delete: `src/epic_news/utils/holiday_report/docx_builder.py`, `src/epic_news/utils/holiday_report/fragments.py`
- Modify: `src/epic_news/utils/holiday_report/assemble.py`
- Test: existing holiday tests (find with `git grep -l holiday tests/`) must stay green.

**Interfaces:**
- Consumes: `docx_report.{build_docx, generate_fragment, Section, assemble_fragments}` from Task 1.
- Produces: `assemble_holiday_docx(crew_result, inputs, output_path, llm=None) -> str` unchanged signature.

- [ ] **Step 1: Run the holiday tests to establish the green baseline**

Run: `uv run pytest -k holiday -v` → note the passing set (regression guard).

- [ ] **Step 2: Rewrite `holiday_report/assemble.py` to use the shared framework**

Replace the imports and the two holiday-local modules. Holiday keeps its travel persona and `skeleton.py`. The itinerary still expands per day. Concretely, change the top of `assemble.py`:

```python
from epic_news.config.llm_config import LLMConfig
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.holiday_report.skeleton import generate_skeleton

_PERSONA = (
    "Tu es un rédacteur de carnet de voyage. Rédige UNIQUEMENT la section demandée, "
    "en français, en Markdown propre (titres de niveau 2+, listes, gras, emojis). "
    "Pas de HTML, pas de JSON, pas de préambule."
)
```

Rewrite the body of `assemble_holiday_docx` to build a `list[Section]` (Introduction, per-day Itinéraire, Hébergements, Restauration, Budget, Informations pratiques) — narrated Sections with `instruction`+`context` mirroring the current fragment calls — then:

```python
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
```

Keep `_task_raw`, `_trip_summary`, the `MAX_ITINERARY_DAYS` cap, and the `generate_skeleton` call exactly as today.

- [ ] **Step 3: Delete the now-unused holiday modules**

```bash
git rm src/epic_news/utils/holiday_report/docx_builder.py src/epic_news/utils/holiday_report/fragments.py
```

- [ ] **Step 4: Run holiday tests → still green**

Run: `uv run pytest -k holiday -v` → same set passes. If a holiday test imported the deleted modules directly, update its import to `epic_news.utils.docx_report`.

- [ ] **Step 5: Lint, type, commit**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy src/epic_news/utils/holiday_report
git add src/epic_news/utils/holiday_report tests
git commit -m "refactor(holiday): consume shared docx_report framework; drop local docx modules"
```

### Task 3: Runtime format resolution + `output_format` state field

**Files:**
- Create: `src/epic_news/utils/docx_report/format_selection.py`
- Modify: `src/epic_news/models/content_state.py` (add field near `output_file`, ~line 122)
- Test: `tests/utils/docx_report/test_format_selection.py`

**Interfaces:**
- Produces:
  - `parse_output_format(request: str | None) -> str | None` — `"docx"` if DOCX intent detected, else `None`.
  - `resolve_output_format(state) -> str` — `"html"` | `"docx"`, precedence `OUTPUT_FORMAT` env > `state.output_format` > `"html"`.
- Modifies: `ContentState.output_format: str | None = None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/docx_report/test_format_selection.py
from types import SimpleNamespace

import pytest

from epic_news.utils.docx_report.format_selection import parse_output_format, resolve_output_format


@pytest.mark.parametrize("req", [
    "génère le rapport en DOCX", "give me a Word document", "je veux un fichier Word",
    "export as docx", "format docx s'il te plaît",
])
def test_parse_detects_docx(req):
    assert parse_output_format(req) == "docx"


@pytest.mark.parametrize("req", ["get the daily news report", "fais un rapport PESTEL", "", None])
def test_parse_defaults_none(req):
    assert parse_output_format(req) is None


def test_resolve_flag_wins(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    assert resolve_output_format(SimpleNamespace(output_format="html")) == "docx"


def test_resolve_parsed_then_default(monkeypatch):
    monkeypatch.delenv("OUTPUT_FORMAT", raising=False)
    assert resolve_output_format(SimpleNamespace(output_format="docx")) == "docx"
    assert resolve_output_format(SimpleNamespace(output_format=None)) == "html"


def test_resolve_ignores_invalid_flag(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "pdf")
    assert resolve_output_format(SimpleNamespace(output_format=None)) == "html"
```

- [ ] **Step 2: Run → fails** (`uv run pytest tests/utils/docx_report/test_format_selection.py -v`).

- [ ] **Step 3: Implement `format_selection.py`**

```python
"""Runtime HTML/DOCX selection: OUTPUT_FORMAT flag > parsed request intent > HTML."""

import os
import re
from typing import Any

_DOCX_PATTERN = re.compile(
    r"\b(docx|word\s+document|document\s+word|fichier\s+word|format\s+docx|en\s+docx|as\s+a\s+word\s+doc\w*)\b",
    re.IGNORECASE,
)


def parse_output_format(request: str | None) -> str | None:
    """Return "docx" if the request asks for a Word/DOCX document, else None."""
    if request and _DOCX_PATTERN.search(request):
        return "docx"
    return None


def resolve_output_format(state: Any) -> str:
    """Resolve the output format. Precedence: OUTPUT_FORMAT env > state.output_format > "html"."""
    env = os.getenv("OUTPUT_FORMAT")
    if env in ("html", "docx"):
        return env
    return getattr(state, "output_format", None) or "html"
```

Add to `ContentState` (content_state.py, in the CREW CONFIGURATION block by `output_file`):
```python
    output_format: str | None = None  # None → HTML; "docx" set by parse/flag
```

- [ ] **Step 4: Run → passes.** Also `uv run pytest tests/ -k content_state` if such tests exist.

- [ ] **Step 5: Lint, type, commit**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy src/epic_news/utils/docx_report src/epic_news/models/content_state.py
git add src/epic_news/utils/docx_report/format_selection.py src/epic_news/models/content_state.py tests/utils/docx_report/test_format_selection.py
git commit -m "feat(docx): runtime output-format resolver + ContentState.output_format"
```

### Task 4: Dispatch registry + `emit_report` helper

**Files:**
- Create: `src/epic_news/utils/docx_report/dispatch.py`
- Test: `tests/utils/docx_report/test_dispatch.py`

**Interfaces:**
- Consumes: `resolve_output_format` (Task 3).
- Produces:
  - `emit_report(state, selected_crew, render_html, assemble_docx=None) -> str` — if the resolved format is `"docx"` and `assemble_docx` is provided, call it (it returns the `.docx` path); else call `render_html()` (a zero-arg callback that runs the crew's existing HTML render and returns its path). Both callbacks are zero-arg closures built at the call site, so `emit_report` is decoupled from each assembler's own signature. Sets and returns `state.output_file`. Logs a warning when DOCX is requested but `assemble_docx is None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/docx_report/test_dispatch.py
from types import SimpleNamespace

from epic_news.utils.docx_report.dispatch import emit_report


def _state(fmt=None):
    return SimpleNamespace(output_format=fmt, output_file="")


def test_html_default_calls_render(monkeypatch):
    monkeypatch.delenv("OUTPUT_FORMAT", raising=False)
    st = _state(None)
    called = {}
    def render():
        called["html"] = True
        return "out/x.html"
    out = emit_report(st, "SAINT", render, assemble_docx=lambda: "out/x.docx")
    assert called.get("html") and out == "out/x.html" and st.output_file == "out/x.html"


def test_docx_requested_runs_assembler(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    st = _state(None)
    out = emit_report(st, "SAINT", lambda: "out/x.html", assemble_docx=lambda: "out/x.docx")
    assert out == "out/x.docx" and st.output_file == "out/x.docx"


def test_docx_requested_no_assembler_falls_back(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    st = _state(None)
    out = emit_report(st, "SAINT", lambda: "out/x.html", assemble_docx=None)
    assert out == "out/x.html" and st.output_file == "out/x.html"
```

- [ ] **Step 2: Run → fails.**

- [ ] **Step 3: Implement `dispatch.py`**

```python
"""Select and run the report renderer for a crew based on the resolved output format."""

from collections.abc import Callable
from typing import Any

from loguru import logger

from epic_news.utils.docx_report.format_selection import resolve_output_format


def emit_report(
    state: Any,
    selected_crew: str,
    render_html: Callable[[], str],
    assemble_docx: Callable[[], str] | None = None,
) -> str:
    """Run the DOCX assembler when DOCX is requested and provided; else render HTML.

    `render_html` runs the crew's existing HTML render and returns its path.
    `assemble_docx` builds the DOCX and returns its path. Both are zero-arg closures
    built at the call site. Sets and returns `state.output_file`.
    """
    fmt = resolve_output_format(state)
    if fmt == "docx" and assemble_docx is not None:
        state.output_file = assemble_docx()
    else:
        if fmt == "docx":
            logger.warning("⚠️ DOCX requested but no assembler for {}; rendering HTML", selected_crew)
        state.output_file = render_html()
    return state.output_file
```

- [ ] **Step 4: Run → passes.**

- [ ] **Step 5: Lint, type, commit**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run mypy src/epic_news/utils/docx_report/dispatch.py
git add src/epic_news/utils/docx_report/dispatch.py tests/utils/docx_report/test_dispatch.py
git commit -m "feat(docx): emit_report dispatch (format-aware HTML/DOCX selection)"
```

### Task 5: Reference **prose** assembler — DEEPRESEARCH

**Files:**
- Create: `src/epic_news/utils/docx_report/crews/__init__.py`
- Create: `src/epic_news/utils/docx_report/crews/deep_research.py`
- Test: `tests/utils/docx_report/crews/test_deep_research.py`

**Interfaces:**
- Consumes: `DeepResearchReport` (`models/crews/deep_research_report.py`) fields `title, topic, executive_summary, key_findings: list[str], research_sections: list[ResearchSection], methodology, sources_count, report_date, confidence_level`.
- Produces: `assemble_deep_research_docx(model: DeepResearchReport, inputs: dict, output_path: str, llm=None) -> str`.

**Section spec (this IS the per-crew deliverable):**
- `Résumé exécutif` — narrated (instruction: "Reformule le résumé en prose fluide.", context = `model.executive_summary`).
- `Principales conclusions` — **deterministic** Markdown bullet list from `model.key_findings`.
- One narrated Section per `model.research_sections` (heading = section title; instruction: "Développe cette section en prose."; context = the section's content). Cap at a sane max (e.g. 20) mirroring holiday's day cap.
- `Méthodologie` — narrated (context = `model.methodology`).
- `Sources` — **deterministic** (`f"{model.sources_count} sources — niveau de confiance : {model.confidence_level}"`).

Persona `_PERSONA`: `"Tu es un analyste de recherche. Rédige UNIQUEMENT la section demandée, en français, en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."`

- [ ] **Step 1: Write the failing test** (stub LLM; assert headings order, deterministic findings verbatim, no LLM call for deterministic sections, valid docx). Model the test on `tests/utils/docx_report/test_assemble.py`'s `_StubLLM` + `_docx_text` helpers.

```python
# tests/utils/docx_report/crews/test_deep_research.py
import zipfile
from epic_news.models.crews.deep_research_report import DeepResearchReport, ResearchSection
from epic_news.utils.docx_report.crews.deep_research import assemble_deep_research_docx


class _StubLLM:
    def __init__(self): self.calls = 0
    def call(self, m): self.calls += 1; return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z: return z.read("word/document.xml").decode()


def test_deep_research_docx(tmp_path):
    model = DeepResearchReport(
        title="T", topic="Quantum", executive_summary="ES",
        key_findings=["Finding-Alpha", "Finding-Beta"],
        research_sections=[ResearchSection(title="Sec1", content="c1")],
        methodology="method", sources_count=9, confidence_level="High",
    )
    llm = _StubLLM()
    out = assemble_deep_research_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    assert "Finding-Alpha" in txt and "Finding-Beta" in txt   # deterministic verbatim
    assert "9 sources" in txt                                  # deterministic sources line
    # narrated: exec summary + 1 research section + methodology = 3 llm calls
    assert llm.calls == 3
```

(Verify `ResearchSection`'s field names in `deep_research_report.py` and adjust `title`/`content` if they differ.)

- [ ] **Step 2: Run → fails.**
- [ ] **Step 3: Implement `crews/deep_research.py`**

```python
"""DEEPRESEARCH → DOCX: narrated prose + deterministic findings/sources."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un analyste de recherche. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."
)
_MAX_SECTIONS = 20


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def assemble_deep_research_docx(model: DeepResearchReport, inputs: dict, output_path: str, llm: Any = None) -> str:
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = [
        Section("Résumé exécutif", instruction="Reformule le résumé en prose fluide.", context=model.executive_summary or ""),
        Section("Principales conclusions", body=_bullets(list(model.key_findings or []))),
    ]
    for rs in (model.research_sections or [])[:_MAX_SECTIONS]:
        sections.append(
            Section(rs.title, instruction="Développe cette section en prose détaillée.", context=rs.content or "")
        )
    sections.append(Section("Méthodologie", instruction="Décris la méthodologie.", context=model.methodology or ""))
    sections.append(
        Section("Sources", body=f"{model.sources_count} sources — niveau de confiance : {model.confidence_level}.")
    )
    meta = {"title": model.title or model.topic or "Recherche", "date": inputs.get("current_date", ""), "author": "Epic News"}
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
```

- [ ] **Step 4: Run → passes.**
- [ ] **Step 5: Lint, type, commit** (`git commit -m "feat(docx): DEEPRESEARCH assembler (reference prose builder)"`).

### Task 6: Reference **tabular** assembler — FINDAILY

**Files:**
- Create: `src/epic_news/utils/docx_report/crews/fin_daily.py`
- Test: `tests/utils/docx_report/crews/test_fin_daily.py`

**Interfaces:**
- Consumes: `FinancialReport` (`models/crews/financial_report.py`) fields `title, executive_summary, analyses: list[AssetAnalysis], suggestions: list[AssetSuggestion], report_date`.
- Produces: `assemble_fin_daily_docx(model, inputs, output_path, llm=None) -> str`.

**Section spec — data is DETERMINISTIC (exact figures preserved):**
- `Résumé exécutif` — narrated (context = `model.executive_summary`).
- `Analyses` — **deterministic** Markdown table over `model.analyses` (read `AssetAnalysis` field names from the model file and build columns from them; every numeric value verbatim).
- `Suggestions` — **deterministic** Markdown table over `model.suggestions`.

Persona: `"Tu es un analyste financier. Rédige UNIQUEMENT la section demandée, en français, en Markdown propre. Pas de HTML, pas de JSON, pas de chiffres inventés."`

Provide a small `_md_table(rows: list[dict], columns: list[tuple[str, str]]) -> str` helper in this file (columns = `(header, attr)`), pipe-escaping cell values. This helper is duplicated per data-heavy crew OR (preferred) extracted to `docx_report/tables.py` in this task and imported by later data-heavy crews.

- [ ] **Step 1: Write the failing test** — build a `FinancialReport` with known figures, stub LLM, assert every figure appears verbatim in the docx, and that the table sections make **zero** LLM calls (only the exec summary narrates → `llm.calls == 1`).
- [ ] **Step 2: Run → fails.**
- [ ] **Step 3: Implement** `docx_report/tables.py` (`_md_table`) + `crews/fin_daily.py` using narrated exec summary + deterministic tables.
- [ ] **Step 4: Run → passes.**
- [ ] **Step 5: Lint, type, commit** (`"feat(docx): FINDAILY assembler + shared markdown table helper (reference tabular builder)"`).

### Task 7 [CONTROLLER]: Wire the parser + DEEPRESEARCH/FINDAILY dispatch into main.py

**Files:** Modify `src/epic_news/main.py` — **controller-only, sentinel-safe** (stash sentinel → edit → commit → restore).

- [ ] **Step 1:** In `classify` (main.py ~237), after `selected_crew` is set, add:
  `self.state.output_format = self.state.output_format or parse_output_format(self.state.user_request)`
  (import `parse_output_format` at top). This sets DOCX intent from the request; the `OUTPUT_FORMAT` flag still overrides at resolve time.
- [ ] **Step 2:** In `generate_deep_research` (main.py ~955), wrap the existing HTML render in `emit_report`: build the `DeepResearchReport` model as today, define `render_html` as a closure running the current `ContentExtractorFactory` + `TemplateManager.render_report` HTML path returning `html_file`, and pass `assemble_docx=lambda: assemble_deep_research_docx(model, current_inputs, "output/deep_research/report.docx")`. Set nothing else — `emit_report` sets `state.output_file`.
- [ ] **Step 3:** In `generate_findaily` (main.py ~512), same pattern: `render_html` runs the existing `render_and_write_html("FINDAILY", financial_report_model, "output/findaily/report.html")`; `assemble_docx=lambda: assemble_fin_daily_docx(financial_report_model, self.state.to_crew_inputs(), "output/findaily/report.docx")`.
- [ ] **Step 4: Manual e2e check** (both formats), per crew:
  `MODEL=... OUTPUT_FORMAT=html EPIC_NEWS_REQUEST="get the financial daily report" crewai flow kickoff` → HTML emailed;
  `OUTPUT_FORMAT=docx …` → DOCX emailed. Confirm `logs/epic_news_error.log` is empty and the attachment extension matches.
- [ ] **Step 5: Commit** (controller): stash sentinel, `git add src/epic_news/main.py`, `git commit -m "feat(docx): wire format parser + DEEPRESEARCH/FINDAILY dispatch"`, restore sentinel.

**Phase 1 exit criteria:** holiday still green; DEEPRESEARCH and FINDAILY each deliver HTML by default and a valid DOCX on `OUTPUT_FORMAT=docx` or a "…en DOCX" request; full suite green.

---

## Phase 2 — Rollout (remaining 12 crews)

Each rollout task follows the **reference pattern**: Task 5 (prose: `deep_research.py`) or Task 6 (tabular: `fin_daily.py` + `tables._md_table`). Per task: create `crews/{crew}.py` with `assemble_{crew}_docx(model, inputs, output_path, llm=None)` from the **section spec below**, write the stub-LLM test (headings/order + deterministic values verbatim + zero LLM calls on deterministic sections + valid docx), then a **[CONTROLLER]** step wires that crew's `generate_*` via `emit_report` and runs the two-format e2e check. Commit per crew. Read each model file for exact sub-object field names before building deterministic tables.

Follow the reference pattern (prose = Task 5, tabular = Task 6) for the boilerplate; only the section spec differs.

### Task 8: SAINT (prose) — model `SaintData`, method `generate_saint_daily` (main.py:610), out `output/saint_daily/report.docx`
Persona: hagiographe. Sections: `Biographie` narrated(`biography`), `Signification` narrated(`significance`), `Miracles` narrated(`miracles`), `Lien avec la Suisse` narrated(`swiss_connection`), `Prière & Réflexion` narrated(`prayer_reflection`), `Sources` **deterministic** bullets(`sources`). Meta title = `saint_name`.

### Task 9: COOKING (fidelity-critical) — model `PaprikaRecipe`, method `generate_recipe` (main.py:672), out `output/cooking/<slug>.docx`
Sections **mostly deterministic** (never let the LLM rewrite quantities): `Informations` deterministic table(`servings, prep_time, cook_time, difficulty, categories`), `Ingrédients` **deterministic** (the `ingredients` text block, line-per-item), `Préparation` **deterministic** (the `directions` text block), `Notes` narrated(`notes`) only if present. Meta title = `name`.

### Task 10: BOOK_SUMMARY (prose) — model `BookSummaryReport`, method `generate_book_summary` (main.py:828), out `output/library/book_summary.docx`
Persona: critique littéraire. Sections: `Résumé` narrated(`summary`), `Table des matières` **deterministic** bullets(`table_of_contents` entries), one narrated Section per `sections` (`BookSummarySection`), `Résumés de chapitres` narrated or deterministic per `chapter_summaries`, `Références` **deterministic** bullets(`references`). Meta title = `title`.

### Task 11: PESTEL (prose) — model `PestelReport`, method `generate_pestel` (main.py:1083), out `output/pestel/report.docx`
Persona: analyste stratégique. Sections: `Résumé exécutif` narrated(`executive_summary`); one narrated Section per dimension `Politique/Économique/Social/Technologique/Environnemental/Légal` (context = that `PestelDimension.summary + impact_analysis`, with `key_factors` appended as a deterministic bullet list inside the context); `Synthèse` narrated(`synthesis`). Meta title = `topic`. (Note: `generate_pestel` also writes `report.md` — leave that untouched.)

### Task 12: SALES_PROSPECTING (prose) — model `SalesProspectingReport`, method `generate_sales_prospecting_report` (main.py:948), out `output/sales_prospecting/report.docx`
Persona: consultant commercial. Sections: `Aperçu de l'entreprise` narrated(`company_overview`), `Contacts clés` **deterministic** table(`key_contacts` → read `KeyContact` fields), `Stratégie d'approche` narrated(`approach_strategy`), `Informations complémentaires` narrated(`remaining_information`).

### Task 13: SHOPPING (tabular) — model `ShoppingAdviceOutput`, method `generate_shopping_advice` (main.py:881), out `output/shopping_advisor/shopping-advice-<slug>.docx`
Sections: `Résumé` narrated(`executive_summary`), `Produit` **deterministic** (fields of `product_info`), `Prix Suisse` **deterministic** table(`switzerland_prices`), `Prix France` **deterministic** table(`france_prices`), `Concurrents` **deterministic** table(`competitors`), `Meilleures offres` **deterministic** bullets(`best_deals`), `Recommandations` narrated(`final_recommendations`). Read `ProductInfo`/`PriceInfo`/`CompetitorInfo` fields.

### Task 14: NEWSDAILY (tabular) — model `NewsDailyReport`, method `generate_news_daily` (main.py:575), out `output/news_daily/report.docx`
Sections: `Résumé` narrated(`summary`); one **deterministic** Section per region (`suisse_romande, suisse, france, europe, world, wars, economy`) rendering each `NewsItem` list (handle the `list | str` union: if str, use as body; if list, bullet each item's title/source/link). `Méthodologie` deterministic(`methodology`). (Email path: `generate_news_daily` renders to `output/news_daily/final_report.html` — keep that as the HTML path; DOCX path uses `report.docx`.)

### Task 15: COMPANY_NEWS (tabular) — model `CompanyNewsReport`, method `generate_news_company` (main.py:392), out `output/company_news/report.docx`
Sections: `Résumé` narrated(`summary`); one **deterministic** Section per `sections` (`Section` → bullet each `ArticleItem` with source/date/citation); `Notes` narrated(`notes`) if present. Read `Section`/`ArticleItem` fields.

### Task 16: MENU (tabular) — model `WeeklyMenuPlan`, method `generate_menu_designer` (main.py:712 and fallback 757), out `output/menu_designer/<slug>.docx`
Sections: `Aperçu` **deterministic**(`week_start_date, season`); `Menus quotidiens` **deterministic** — one sub-heading per `daily_menus` (`DailyMenu` → table of `DailyMeal`/`DishInfo`, exact dish names); `Équilibre nutritionnel` narrated(`nutritional_balance`), `Cohérence gustative` narrated(`gustative_coherence`), `Adaptations` narrated(`constraints_adaptation` + `preferences_integration`). **Two HTML call sites** (primary 712, fallback 757) — the controller step wires `emit_report` at both. Read `DailyMenu`/`DailyMeal`/`DishInfo` fields.

### Task 17: MEETING_PREP (tabular) — model `MeetingPrepReport`, method `generate_meeting_prep` (main.py:915), out `output/meeting/meeting_preparation.docx`
Sections: `Résumé` narrated(`summary`), `Profil de l'entreprise` **deterministic**(`company_profile` fields), `Participants` **deterministic** table(`participants`), `Aperçu du secteur` narrated(`industry_overview`), `Points de discussion` narrated per `talking_points` (or deterministic bullets), `Recommandations stratégiques` narrated per `strategic_recommendations`, `Ressources` **deterministic** bullets(`additional_resources`). Read the sub-object fields.

### Task 18: RSS (tabular, non-standard HTML path) — model `RssWeeklyReport`, method `generate_rss_weekly` (async, main.py:398), out `output/rss_weekly/report.docx`
Sections: `Résumé` narrated(`summary`), `Aperçu` **deterministic**(`total_feeds`, `total_articles`), one **deterministic** Section per `feeds` (`FeedDigest` → bullet each `ArticleSummary`). **Wiring caveat:** this method builds HTML via `report_utils.generate_rss_weekly_html_report`, not `render_and_write_html`, and is **async** — the controller step wraps that helper call as the `render_html` closure and calls `emit_report` inside the async method (no `await` needed for the assembler; it is sync).

### Task 19: OSINT (tabular, most complex) — 7 models, method `generate_osint` (async, main.py:1089), out `output/osint/report.docx`
The consolidated OSINT report combines `CrossReferenceReport` (global) + 6 sub-reports. Build `assemble_osint_docx(state, inputs, output_path, llm=None)` reading the models stored on `state` (`company_profile`, `tech_stack`, `web_presence`, plus HR/legal/geospatial and the cross-reference model). Sections: `Résumé exécutif` narrated(cross-ref `executive_summary`); `Constats détaillés` **deterministic** (render the `detailed_findings: dict` as nested bullets); then one **deterministic** Section per sub-report summarizing its key fields (exact values); `Évaluation de la confiance` narrated(`confidence_assessment`); `Lacunes d'information` **deterministic** bullets(`information_gaps`). **Wiring caveat:** `generate_osint` is async and produces several HTML files + a consolidated dict; the controller step adds a single `emit_report` deciding between the existing consolidated-HTML path (`render_html`) and `assemble_osint_docx`, setting `state.output_file` to the `.docx` when DOCX is requested (today it is `output/osint/global_report.html`). This is the largest task — budget extra review.

### Task 20 [CONTROLLER]: batch-wire the Phase-2 generate_* dispatch + final e2e sweep
For any rollout crews whose controller wiring was deferred, wire them here. Then run `scripts/verify_all_crews.sh` once with `OUTPUT_FORMAT=html` (all crews still deliver HTML, unchanged) and once with `OUTPUT_FORMAT=docx` (every crew with an assembler delivers a valid `.docx`; error log empty each run). Update `docs/sweep-runbook.md` with the `OUTPUT_FORMAT` variable.

---

## Final review
After all tasks: dispatch the whole-branch code review (superpowers:requesting-code-review), then finish via superpowers:finishing-a-development-branch. Confirm: HTML output byte-unchanged when no DOCX requested; every assembler has stub-LLM tests asserting deterministic values verbatim; `mypy`/`ruff` clean; full suite green.
