# Simplification S5 — DOCX Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every report is a DOCX built by the crew's assembler; the HTML rendering stack (`utils/html/`, `templates/`, theme, renderers, HTML helpers, their tests and dependencies) is deleted.

**Architecture:** `emit_report(state, assemble_docx)` runs the assembler and sets `state.output_file` to the DOCX path; there is no format choice. The poem gets a deterministic assembler. The email sends a short text body with the DOCX attached; the Streamlit app offers the DOCX for download. `build_docx` enforces the `output/` boundary that `render_and_write_html` enforced (ADR-015). Then the HTML code, tests, templates, dependencies and docs go, and a new ADR supersedes ADR-005 and ADR-011.

**Tech Stack:** Python 3.13, pandoc (system), pypandoc, CrewAI 1.15.23, Streamlit, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S5 revised 2026-10-05, decision 6). Survey (`.superpowers/sdd/simplification-s5/html-map.md`): 15 `emit_report` call sites; the poem is the only step without an assembler (and calls `render_and_write_html` directly); OSINT writes 6 sub-report HTMLs plus `global_report.html` and `consolidated_report.html`; deep research calls `TemplateManager` and `ContentExtractorFactory` inside its HTML closure; PESTEL also writes `report.md` via `pestel_to_markdown`; `classify()` sets `state.output_format`; `utils/html/` is 6,289 lines in 31 files, `templates/` 509 lines of HTML + 2,060 of CSS, `config/ui_theme.py` 91 lines; `nh3` and `markdown-it-py` become unused; about 195 HTML-only tests; `app.py` reads `output_file` as text and calls `st.html`.

## Global Constraints

- Reports are produced in one format, DOCX, through the existing assemblers; `emit_report`'s format choice, `OUTPUT_FORMAT` and `ContentState.output_format` go away (spec S5).
- The poem gets a deterministic DOCX assembler (no LLM) (spec S5).
- Removed: `utils/html/`, `templates/`, `config/ui_theme.py`, the report CSS, `render_and_write_html`, `resolve_report_html`, the RSS HTML report helper, HTML-only tests (spec S5).
- Email: short text body plus the DOCX attachment. Streamlit: download button for the DOCX instead of `st.html` (spec S5).
- A report-building error stops the run; nothing partial is emailed (spec decision 4).
- ADR-005 and ADR-011 are superseded by a new ADR (spec S5).
- Files written for reports stay under `output/` (ADR-015): `build_docx` refuses any other path.
- Crews keep CrewAI's documented form; no crew agent/task/prompt change, except prompt text that asks an agent to produce HTML (report it; change only if the agent's output would otherwise be wrong).
- Deep research keeps its extractor until S3; only its HTML closure goes.
- `pestel_to_markdown` / `report.md` go with the HTML stack (DOCX only; no second human-readable format) — controller ruling.
- Project rules: `uv` only (`uv remove`), imports at top, Loguru, mypy `warn_unused_ignores`, never `ruff format` the 3 pre-existing unformatted CLAUDE.md files.

## Review Focus

1. A report step still writes or returns an HTML path (state.output_file ending in `.html`), so the email attaches nothing or the app fails → Task 2 test: every `generate_*` step leaves `state.output_file` ending in `.docx`.
2. A DOCX assembler raises, and the flow emails anyway → Task 2 test: an assembler error propagates from the step (no email step runs).
3. `build_docx` asked to write outside `output/` (path from an LLM-filled input) → Task 2 test: `ValueError`.
4. The Streamlit app opens a DOCX as text and crashes → Task 3 test: the app offers the bytes for download with the DOCX MIME type.
5. Deleting the HTML stack leaves an import (`utils.html`, `TemplateManager`, `render_and_write_html`, `ui_theme`, `nh3`, `markdown_it`) somewhere in src, scripts or tests → Task 4 grep gate plus the full suite.

---

### Task 1: Deterministic poem assembler

**Files:**
- Create: `src/epic_news/utils/docx_report/crews/poem.py`
- Test: `tests/utils/docx_report/crews/test_poem.py`

**Interfaces:**
- Produces: `assemble_poem_docx(model: PoemJSONOutput, inputs: dict, output_path: str, llm: Any = None) -> str` (same signature shape as the other assemblers; `llm` unused).

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/docx_report/crews/test_poem.py
from epic_news.models.crews.poem_report import PoemJSONOutput  # check the real module path
from epic_news.utils.docx_report.crews import poem as poem_mod


def test_poem_docx_keeps_title_lines_and_stanzas(monkeypatch, tmp_path):
    captured = {}

    def fake_build(fragments, meta, output_path):
        captured.update(fragments=fragments, meta=meta)
        return output_path

    monkeypatch.setattr(poem_mod, "build_docx", fake_build)
    model = PoemJSONOutput(title="Automne", poem="Les feuilles tombent\nsur le lac\n\nle vent se tait")
    out = poem_mod.assemble_poem_docx(model, {}, "output/poem/poem.docx")

    assert out == "output/poem/poem.docx"
    assert captured["meta"]["title"] == "Automne"
    body = "\n".join(text for _, text in captured["fragments"])
    assert "Les feuilles tombent" in body and "le vent se tait" in body
    # Line breaks inside a stanza survive Markdown (two trailing spaces or a hard break); stanzas stay separate.
    assert "\n\n" in body


def test_poem_docx_makes_no_llm_call(monkeypatch):
    monkeypatch.setattr(poem_mod, "build_docx", lambda fragments, meta, output_path: output_path)

    class NoLLM:
        def call(self, *_a, **_k):
            raise AssertionError("the poem must not be narrated")

    poem_mod.assemble_poem_docx(PoemJSONOutput(title="T", poem="x"), {}, "output/poem/p.docx", llm=NoLLM())
```

Use the real module of `PoemJSONOutput` (`rg -n "class PoemJSONOutput" src`) and the meta keys other assemblers pass to `build_docx` (read `src/epic_news/utils/docx_report/crews/saint.py` or `cooking.py` and `docx_builder.py`).

- [ ] **Step 2: Run** — `env -u VIRTUAL_ENV uv run pytest tests/utils/docx_report/crews/test_poem.py -q` → FAIL (module missing).

- [ ] **Step 3: Implement** — `poem.py`: build one fragment whose Markdown keeps each line break inside a stanza (end each line with two spaces, or use Pandoc's hard line break `\` at line end — check which `build_docx`'s Markdown reader honours; test it with a real `build_docx` into `tmp_path` under an `output/` cwd if Task 2's boundary is already in place, otherwise only with the fake) and separates stanzas with a blank line; `meta` with the poem title as document title, author and date like the other assemblers; call `build_docx(fragments, meta, output_path)`; return its path. Module docstring: deterministic, no LLM.

- [ ] **Step 4: Run** — tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/docx_report/crews/poem.py tests/utils/docx_report/crews/test_poem.py
git commit -m "feat(docx): deterministic poem report"
```

---

### Task 2: Every report step writes DOCX only

**Files:**
- Modify: `src/epic_news/utils/docx_report/dispatch.py` (new `emit_report` signature), delete `src/epic_news/utils/docx_report/format_selection.py`
- Modify: `src/epic_news/utils/docx_report/docx_builder.py` (output/ boundary)
- Modify: `src/epic_news/main.py` (15 `emit_report` call sites, `generate_poem`, OSINT HTML writes, deep research HTML closure, PESTEL `report.md`, `classify()` `output_format`)
- Modify: `src/epic_news/models/content_state.py` (remove `output_format`; `MENU_REPORT_TEMPLATE` if it points at `templates/`)
- Tests: update the dispatch/format-selection tests (delete format-selection ones), `tests/flows/test_generate_output_file.py`, `tests/flows/test_reception_flow_e2e.py`, `tests/test_generate_pestel_wiring.py`, `tests/test_osint_parallel_json.py`, any other test asserting an `.html` `output_file`; create `tests/utils/docx_report/test_docx_boundary.py` and `tests/flows/test_all_steps_emit_docx.py`

**Interfaces:**
- Consumes: Task 1 `assemble_poem_docx`.
- Produces: `emit_report(state: Any, assemble_docx: Callable[[], str]) -> str` (sets and returns `state.output_file`).

- [ ] **Step 1: Failing tests**

```python
# tests/utils/docx_report/test_docx_boundary.py
import pytest

from epic_news.utils.docx_report.docx_builder import build_docx


def test_build_docx_refuses_paths_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, "../evil.docx")
```

```python
# tests/utils/docx_report/test_emit_report.py (replace the old dispatch tests)
from types import SimpleNamespace

import pytest

from epic_news.utils.docx_report.dispatch import emit_report


def test_emit_report_sets_output_file_to_the_docx():
    state = SimpleNamespace(output_file=None)
    assert emit_report(state, lambda: "output/x/report.docx") == "output/x/report.docx"
    assert state.output_file == "output/x/report.docx"


def test_emit_report_propagates_assembler_errors():
    state = SimpleNamespace(output_file="before")
    with pytest.raises(RuntimeError):
        emit_report(state, lambda: (_ for _ in ()).throw(RuntimeError("pandoc failed")))
    assert state.output_file == "before"
```

`tests/flows/test_all_steps_emit_docx.py`: for each report step that can be driven with monkeypatched crews (follow the existing flow tests' fixtures: `kickoff_flow` patched, `load_or_parse_model` patched to return a minimal valid model, the step's assembler patched to return its DOCX path), assert `state.output_file.endswith(".docx")` and no `.html` file is written under the tmp `output/`. Cover at least: poem, saint, news_daily, findaily, cooking (recipe), book summary, sales prospecting, pestel, OSINT. Parametrise where the setup is shared; it is acceptable to cover the remaining steps through the existing per-step tests you update in Step 4.

- [ ] **Step 2: Run** — the new tests fail.

- [ ] **Step 3: Implement**
  - `dispatch.py`:

```python
"""Write a crew's report: the DOCX assembler is the only output format (spec S5, decision 6)."""

from collections.abc import Callable
from typing import Any


def emit_report(state: Any, assemble_docx: Callable[[], str]) -> str:
    """Run the DOCX assembler and record its path in `state.output_file`.

    Errors propagate: a report that cannot be built stops the run (nothing is emailed).
    """
    path = assemble_docx()
    state.output_file = path
    return path
```

  - `docx_builder.build_docx`: before writing, resolve `output_path` and raise `ValueError(f"Refusing to write a report outside output/: {output_path}")` unless it is inside `Path("output").resolve()` (same rule as the deleted `render_and_write_html`; cwd-relative).
  - `main.py`: every `emit_report(self.state, "<KEY>", <html closure>, assemble_docx=<closure>)` becomes `emit_report(self.state, <docx closure>)`; `generate_poem` builds the poem DOCX with `assemble_poem_docx` (path `output/poem/poem.docx`) through `emit_report`; OSINT stops writing the six sub-report HTMLs, `global_report.html` and `consolidated_report.html` (the JSON files and the OSINT DOCX stay); deep research drops the `_render_html` closure, `TemplateManager` and `ContentExtractorFactory` (keep the extractor that builds the model until S3); PESTEL stops writing `report.md`; `classify()` stops setting `output_format`. Remove imports made unused. Keep every other behaviour of each step.
  - `content_state.py`: remove `output_format` (and its docs); handle `MENU_REPORT_TEMPLATE` (delete if only HTML uses it).
  - Delete `format_selection.py`.

- [ ] **Step 4: Update the mixed tests** listed under Files so they expect DOCX outputs (patch the assemblers where they used to patch HTML rendering). Do not delete a test that checks non-HTML behaviour; rewrite its HTML expectation.

- [ ] **Step 5: Verify** — `env -u VIRTUAL_ENV uv run pytest -q` (HTML-stack unit tests still pass at this point: the stack is deleted in Task 4), `uv run ruff check .`, `uv run mypy src/epic_news`. `rg -n "emit_report\(" src/epic_news/main.py` shows only two-argument calls.

- [ ] **Step 6: Commit**

```bash
git add -A src/epic_news tests
git commit -m "refactor(flow): every report step writes DOCX only"
```

---

### Task 3: Email and Streamlit app on DOCX

**Files:**
- Modify: `src/epic_news/utils/report_utils.py` (`prepare_email_params`), `src/epic_news/main.py` (`send_email` body selection ~1585-1640), `src/epic_news/utils/email_sender.py` (only if needed), `src/epic_news/app.py`
- Tests: the send-email tests, `tests/test_app.py` (or the real app test file)

**Interfaces:**
- Consumes: Task 2 (`state.output_file` is always a `.docx`).

- [ ] **Step 1: Failing tests** — (a) `prepare_email_params` for a state whose `output_file` is `output/x/report.docx` returns that path as `attachment_path` and the short text body ("Please find the report for '<request>' attached."); (b) `send_email` passes that short body and the attachment to `send_report_email` without reading the DOCX as text (patch `send_report_email`); (c) a missing DOCX → the step logs an error and does not send (current behaviour for a missing attachment: read it in main.py and keep it, or make it stop — the spec says nothing partial is emailed: a report email without its report is partial, so do not send; test it); (d) app: given a state/result pointing at a DOCX file, the page shows a download button with MIME `application/vnd.openxmlformats-officedocument.wordprocessingml.document` and the file's bytes, and never calls `st.html` (follow the existing app test's Streamlit mocking).

- [ ] **Step 2: Run** — they fail where HTML handling remains.

- [ ] **Step 3: Implement** — `prepare_email_params`: one branch (DOCX attachment + short body); remove the HTML branch and the `resolve_report_html` use. `send_email`: body is always the short body; delete the "read report as body" path and its `UnicodeDecodeError` fallback; a missing attachment → error log, `state.email_sent = False`, no send. `send_report_email`: if it hard-codes `is_html: True`, keep it only if the short body renders fine as HTML (it is plain text; leave as is unless a test shows a problem). `app.py`: read the report as bytes and offer `st.download_button` (label "Télécharger le rapport (DOCX)", file name = basename); remove `st.html` and the `.md` download; drop the BeautifulSoup use if it only served the HTML view.

- [ ] **Step 4: Verify** — full suite, ruff, mypy.

- [ ] **Step 5: Commit**

```bash
git add -A src/epic_news tests
git commit -m "feat(email,app): send and offer the DOCX report"
```

---

### Task 4: Delete the HTML stack

**Files:**
- Delete: `src/epic_news/utils/html/` (incl. `pestel_markdown.py`), `templates/` (repo root), `src/epic_news/config/ui_theme.py`, `render_and_write_html` (utils/flow_helpers.py), `resolve_report_html` and `generate_rss_weekly_html_report` (utils/report_utils.py), the `html_designer` entry in `ensure_output_directories`, HTML-only scripts (`scripts/analyze_library_crew.py`; the HTML checks in `scripts/validate_production_readiness.py` — remove those checks, keep the rest)
- Delete tests: `tests/utils/html/`, `tests/rendering/`, the HTML-only files in `tests/scripts/` (`regenerate_*` HTML helpers, `test_cooking_renderer.py`, `test_analyze_library_crew.py`), `tests/utils/test_report_html_resolution.py`, `tests/utils/test_html_to_markdown.py` (check it is HTML-only), the `pestel_markdown` tests
- Modify: `Dockerfile`, `.dockerignore` (templates lines), `pyproject.toml` / `uv.lock` (`uv remove nh3 markdown-it-py` if nothing else imports them; `beautifulsoup4` too if no import remains in src/scripts — it stays installed through crewai-tools, which is fine)

- [ ] **Step 1: Delete** the files and directories above (`git rm -r`).

- [ ] **Step 2: Grep gate** — this must print nothing:

```bash
rg -n "utils\.html|utils/html|TemplateManager|RendererFactory|render_and_write_html|resolve_report_html|ui_theme|generate_rss_weekly_html_report|pestel_to_markdown|import nh3|from nh3|markdown_it|templates/" src scripts tests Dockerfile .dockerignore Makefile pyproject.toml
```

Fix each hit (delete dead code, or update the reference). `bs4` imports: `rg -n "bs4|BeautifulSoup" src scripts` — remove the direct dependency only if empty.

- [ ] **Step 3: Dependencies** — `uv remove` the unused ones; check `git diff pyproject.toml uv.lock` touches only them. `uv run deptry src` if the project uses it (it flagged DEP002 before) must be clean.

- [ ] **Step 4: Verify** — `env -u VIRTUAL_ENV uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check src tests scripts`, `uv run mypy src/epic_news`, `uv run yamllint -s .`, `docker build` is NOT required locally (CI builds it; make sure the Dockerfile no longer copies `templates/`). Report `git diff --shortstat <task base> HEAD`.

- [ ] **Step 5: Commit**

```bash
git add -A src tests scripts templates Dockerfile .dockerignore pyproject.toml uv.lock
git commit -m "refactor: remove the HTML rendering stack"
```

---

### Task 5: Docs and ADR

**Files:**
- Create: `docs/adr/ADR-017-docx-only-reports.md`
- Modify: `docs/adr/ADR-005-*.md`, `docs/adr/ADR-011-*.md` (status: superseded by ADR-017), `docs/reference/RENDERING_ARCHITECTURE.md` (delete, or replace by a short DOCX page if other docs link to it — check links), `docs/reference/outputs.md`, `README.md`, root `CLAUDE.md` ("HTML Report Generation", "HTML Rendering Architecture", "Federated HTML Theme" sections → one short "Reports (DOCX)" section), `src/epic_news/utils/CLAUDE.md`, `src/epic_news/crews/CLAUDE.md` (two-agent pattern rationale mentions HTML)

- [ ] **Step 1: ADR-017** — context (two formats, HTML default, renderer/schema drift found in S3 survey, 6.3k lines), decision (DOCX only via assemblers; email attaches; app downloads; build errors stop the run; `build_docx` enforces `output/`), consequences (reports not readable in the email body; narrated sections cost LLM calls — per-assembler counts from the survey; pandoc mandatory; no HTML theme). Follow the format of ADR-016.

- [ ] **Step 2: Update the other docs** — remove or rewrite every statement about HTML rendering, `OUTPUT_FORMAT`, `render_and_write_html`, the theme and templates; keep links valid (`rg -n "RENDERING_ARCHITECTURE|ADR-005|ADR-011|render_and_write_html|OUTPUT_FORMAT|ui_theme|TemplateManager" docs README.md CLAUDE.md src/epic_news/**/CLAUDE.md`).

- [ ] **Step 3: Crew prompts** — `rg -n -i "html" src/epic_news/crews/*/config/*.yaml`: list each hit in the report; change only a prompt that asks an agent to produce HTML output (its output would now be wrong), never wording that merely mentions HTML.

- [ ] **Step 4: Commit**

```bash
git add docs README.md CLAUDE.md src/epic_news
git commit -m "docs: DOCX-only reports (ADR-017 supersedes ADR-005 and ADR-011)"
```

Controller: live runs before the PR, with `EPIC_ENABLE_EMAIL=false`: `scripts/bench_flow.py news_daily` and one more crew that used to be HTML by default (e.g. a `saint` request added to `scripts/bench_requests.json`); record wall clock and LiteLLM calls versus the earlier HTML runs in the results file of this wave (`docs/superpowers/plans/2026-10-04-efficiency-wave-results.md` has the HTML baselines for news_daily), and open each DOCX. One run with email ON is the user's call (it sends a real email).
