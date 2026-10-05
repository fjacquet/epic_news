# Simplification S2 — Parsing Through Model Validators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink `parse_crewai_output` from 242 lines (ruff C901 complexity 50) to about 40 lines (complexity < 10) by moving the one live model-specific fix into its Pydantic model and replacing the home-grown JSON repair with the `json_repair` library, while every recorded crew output still parses to the same model.

**Architecture:** `parse_crewai_output(report_content, model_class, inputs)` keeps its signature and its four error messages. It returns a pydantic passthrough, checks for empty or JSON-less output, sanitises thousand separators and smart quotes, hands the text from the first `{`/`[` to `json_repair.loads` (which also drops code fences, prose and trailing text), and validates with `model_class.model_validate`. The BookSummary `table_of_contents[].id` coercion becomes a `field_validator(mode="before")` on `TableOfContentsEntry`. The two Sales branches act on a field (`sales_metrics`) the real `SalesProspectingReport` does not have, so they are dead and are deleted. A characterisation test replays recorded raw outputs of 8 crews against golden model dumps taken before the change.

**Tech Stack:** Python 3.13, Pydantic v2, `json-repair` 0.60.1 (already in `uv.lock` through crewai; becomes a direct dependency), pytest, ruff (C901), uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (section S2). Survey (main at 89f44ba): `parse_crewai_output` is `src/epic_news/utils/diagnostics/parsing.py:135-376`; `_attempt_json_repair` lines 20-132 (regex pipeline, called only from there and from 11 tests); model branches keyed on `model_class.__name__`: `BookSummaryReport` (lines 272-275, duplicated at 346-349) and `SalesProspectingReport` (278-319, dead in production). Callers: `load_or_parse_model` (9 flow steps), `main.py` OSINT (:1355), cross-reference (:1421), deep research fallback (:1114, S3 — leave alone), `utils/recipe_export.py`.

## Global Constraints

- Move each model-specific fix in `parse_crewai_output` into a validator on that model (`@model_validator(mode="before")`, or a `field_validator(mode="before")` on the field's own model when that is simpler); replace the home-grown repair with `json_repair` and declare it (spec S2).
- Target: `parse_crewai_output` ≈40 lines, complexity < 10 (spec S2), measured with `uv run ruff check --select C901 --config lint.mccabe.max-complexity=9 src/epic_news/utils/diagnostics/parsing.py`.
- Characterisation: the recorded raw outputs that parse today must still parse to equal models (spec S2). Fixtures live in `tests/` (debug/ is gitignored).
- Behaviour preserved except where noted (spec Goal 4). Error messages kept: "<Model> crew produced no output", "<Model> crew produced no valid JSON", "Invalid JSON output from <Model> crew", "Invalid <Model> data structure". Every failure raises `ValueError`.
- Out of scope: deep research (S3: `main.py:1114`, `utils/extractors/`, both `DeepResearchReport` schemas — no validators added there); `load_or_parse_model` (unchanged).
- Project rules: `uv` only (`uv add`), imports at top, Loguru, no `os.makedirs` in logic, mypy `warn_unused_ignores`.

## Review Focus

1. A crew's raw output that parses today stops parsing, or parses to a different model, because `json_repair` reads it differently from `json.loads` → Task 1's characterisation test replays 8 recorded crew outputs against golden dumps; Task 3 runs it.
2. Output with no JSON at all ("Sorry, I could not…") must still raise "produced no valid JSON", not validate an empty string (`json_repair.loads` returns `""` for non-JSON) → Task 3 keeps the first-`{`/`[` check and a test.
3. A JSON array returned for an object model must still fail with "data structure", not crash differently → Task 3 test.
4. Python literals in LLM output: the old repair turned `None` into `null`; `json_repair` turns `{"b": None}` into `{"b": "None"}`. Any model field that is `X | None` would now receive the string "None" → Task 3 adds a test pinning what happens for one optional field and records it; if it validates as the string "None", the plan accepts it (old behaviour only applied when `json.loads` had already failed) and the report says so.
5. BookSummary ids now coerced by the model also on the file path (`load_or_parse_model` validates the JSON file first): an int `id` in the saved file now validates instead of falling back to re-parsing — intended; Task 2 tests both paths.

---

## File Structure

- Create `tests/fixtures/raw_outputs/*.txt` (8 recorded raw outputs) and `tests/fixtures/raw_outputs/expected/*.json` (golden model dumps).
- Create `tests/utils/diagnostics/test_parsing_characterisation.py`.
- Modify `src/epic_news/models/crews/book_summary_report.py` (`TableOfContentsEntry` validator); test `tests/models/test_book_summary_toc_id.py` (create).
- Rewrite `src/epic_news/utils/diagnostics/parsing.py`; rewrite `tests/utils/diagnostics/test_parsing.py`.
- Modify `pyproject.toml` / `uv.lock` (`json-repair` direct dependency), `src/epic_news/utils/CLAUDE.md`.

---

### Task 1: Characterisation fixtures from recorded crew outputs

**Files:**
- Create: `tests/fixtures/raw_outputs/<label>.txt` × 8 and `tests/fixtures/raw_outputs/expected/<label>.json` × 8
- Create: `tests/utils/diagnostics/test_parsing_characterisation.py`

**Interfaces:**
- Produces: `CASES: dict[str, type[BaseModel]]` (label → model) and the golden files; Task 3 must keep this test green without touching the golden files.

- [ ] **Step 1: Copy the raw outputs** (only the `raw` field of each dump; `debug/` is gitignored). Run once from the repo root:

```bash
env -u VIRTUAL_ENV uv run python - <<'EOF'
import json
from pathlib import Path

PICK = {
    "company_profile": "debug/crewai_state_company_profile_1791146966.json",
    "tech_stack": "debug/crewai_state_tech_stack_1791146374.json",
    "web_presence": "debug/crewai_state_web_presence_1791146522.json",
    "hr_intelligence": "debug/crewai_state_hr_intelligence_1791176211.json",
    "cross_reference_report": "debug/crewai_state_cross_reference_report_1791147951.json",
    "newsdaily": "debug/crewai_state_newsdaily_1791135840.json",
    "pestel": "debug/crewai_state_pestel_1791175153.json",
    "sales_prospecting": "debug/crewai_state_sales_prospecting_1791187951.json",
}
out = Path("tests/fixtures/raw_outputs")
out.mkdir(parents=True, exist_ok=True)
for label, path in PICK.items():
    raw = json.loads(Path(path).read_text(encoding="utf-8"))["raw"]
    (out / f"{label}.txt").write_text(raw, encoding="utf-8")
    print(label, len(raw))
EOF
```

If a listed dump file no longer exists, pick the newest `debug/crewai_state_<label>_*.json` for that label and say so in the report. Check each `.txt` contains no secret (API keys, tokens, e-mail addresses other than public corporate contacts): `rg -i "api[_-]?key|token|sk-|@gmail" tests/fixtures/raw_outputs` must print nothing relevant; if it does, stop and report.

- [ ] **Step 2: Write the characterisation test**

```python
# tests/utils/diagnostics/test_parsing_characterisation.py
"""Recorded crew outputs must keep parsing to the same models (simplification S2).

Golden files are model dumps taken with the parser as it was before S2. Regenerate
only on purpose: UPDATE_PARSING_GOLDEN=1 env -u VIRTUAL_ENV uv run pytest <this file>
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news.models.crews.company_profiler_report import CompanyProfileReport
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.hr_intelligence_report import HRIntelligenceReport
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.models.crews.web_presence_report import WebPresenceReport
from epic_news.utils.diagnostics import parse_crewai_output

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "raw_outputs"

CASES = {
    "company_profile": CompanyProfileReport,
    "tech_stack": TechStackReport,
    "web_presence": WebPresenceReport,
    "hr_intelligence": HRIntelligenceReport,
    "cross_reference_report": CrossReferenceReport,
    "newsdaily": NewsDailyReport,
    "pestel": PestelReport,
    "sales_prospecting": SalesProspectingReport,
}


@pytest.mark.parametrize("label", sorted(CASES))
def test_recorded_output_parses_to_golden_model(label, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the parser may write debug files relative to cwd
    raw = (FIXTURES / f"{label}.txt").read_text(encoding="utf-8")
    model = parse_crewai_output(SimpleNamespace(raw=raw, output=None), CASES[label])
    dumped = json.loads(model.model_dump_json())
    golden = FIXTURES / "expected" / f"{label}.json"
    if os.getenv("UPDATE_PARSING_GOLDEN") == "1":
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(json.dumps(dumped, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return
    assert dumped == json.loads(golden.read_text(encoding="utf-8"))
```

The import paths above are a best guess: before running, check each model's real module with `rg -n "class CompanyProfileReport|class TechStackReport|class WebPresenceReport|class HRIntelligenceReport|class CrossReferenceReport|class NewsDailyReport|class PestelReport|class SalesProspectingReport" src/epic_news/models` and use the real paths. Use the same model classes `main.py` uses for these crews (`rg -n "parse_crewai_output|load_or_parse_model" src/epic_news/main.py`).

- [ ] **Step 3: Generate the golden files with today's parser, then check stability**

Run: `UPDATE_PARSING_GOLDEN=1 env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics/test_parsing_characterisation.py -q`
Then twice: `env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics/test_parsing_characterisation.py -q` → 8 passed. If a golden file contains a non-deterministic value (e.g. a `generated_at` the model fills with `now()`), exclude that key in the test's comparison and say so.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/raw_outputs tests/utils/diagnostics/test_parsing_characterisation.py
git commit -m "test(parsing): replay recorded crew outputs against golden models"
```

---

### Task 2: BookSummary ids coerced by the model

**Files:**
- Modify: `src/epic_news/models/crews/book_summary_report.py` (`TableOfContentsEntry`)
- Test: `tests/models/test_book_summary_toc_id.py` (create)

**Interfaces:**
- Produces: `TableOfContentsEntry` accepts a non-string `id` and stores `str(id)`. Task 3 deletes the parser's two BookSummary branches relying on this.

- [ ] **Step 1: Write the failing tests**

```python
# tests/models/test_book_summary_toc_id.py
from types import SimpleNamespace

from epic_news.models.crews.book_summary_report import BookSummaryReport, TableOfContentsEntry
from epic_news.utils.diagnostics import parse_crewai_output


def test_entry_coerces_int_id():
    assert TableOfContentsEntry.model_validate({"id": 3, "title": "Chapter 3"}).id == "3"


def test_entry_keeps_string_id():
    assert TableOfContentsEntry.model_validate({"id": "intro", "title": "Intro"}).id == "intro"


def test_report_with_int_ids_parses():
    raw = (
        '{"topic": "t", "publication_date": "2020", "title": "T", "summary": "S",'
        ' "table_of_contents": [{"id": 1, "title": "One"}, {"id": 2, "title": "Two"}],'
        ' "sections": [], "chapter_summaries": [], "references": [], "author": "A"}'
    )
    report = parse_crewai_output(SimpleNamespace(raw=raw, output=None), BookSummaryReport)
    assert [e.id for e in report.table_of_contents] == ["1", "2"]
```

Adjust the entry's field names (`title` above) and the report's required fields to the real models (`src/epic_news/models/crews/book_summary_report.py`); keep the int ids.

- [ ] **Step 2: Run** — `env -u VIRTUAL_ENV uv run pytest tests/models/test_book_summary_toc_id.py -q` → the two entry tests FAIL (the report test passes today through the parser branch).

- [ ] **Step 3: Implement** — in `TableOfContentsEntry` add (import `field_validator` from pydantic at the top; `Any` from typing):

```python
    @field_validator("id", mode="before")
    @classmethod
    def _id_as_text(cls, value: Any) -> Any:
        """LLMs often number chapters with ints; ids are text."""
        return value if value is None or isinstance(value, str) else str(value)
```

- [ ] **Step 4: Run** — the three tests pass; `env -u VIRTUAL_ENV uv run pytest tests -q -k "book"` passes.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/models/crews/book_summary_report.py tests/models/test_book_summary_toc_id.py
git commit -m "feat(models): table-of-contents ids accept numbers"
```

---

### Task 3: `parse_crewai_output` on json_repair

**Files:**
- Modify: `pyproject.toml`, `uv.lock` (via `uv add`)
- Rewrite: `src/epic_news/utils/diagnostics/parsing.py`
- Rewrite: `tests/utils/diagnostics/test_parsing.py`
- Modify: `src/epic_news/utils/CLAUDE.md` (parsing paragraph)

**Interfaces:**
- Consumes: Task 1 characterisation test (must stay green, golden files untouched); Task 2 validator.
- Produces: `parse_crewai_output[T: BaseModel](report_content: Any, model_class: type[T], inputs: dict | None = None) -> T` — same signature, same exported name.

- [ ] **Step 1: Declare the dependency** — `uv add "json-repair>=0.60"`; check `git diff pyproject.toml uv.lock` shows the direct dependency and no unrelated upgrades (if `uv add` upgrades other packages, run `uv lock --upgrade-package json-repair` instead from a clean `uv.lock` and report).

- [ ] **Step 2: Rewrite the tests** — replace `tests/utils/diagnostics/test_parsing.py` with tests against the new behaviour. Keep these cases (from today's file) with the same inputs and assertions on the result: pydantic passthrough; valid JSON; fenced JSON with a `json` hint; preamble and trailing text; thousand separators (`{"value": 1,234,567}` → 1234567); smart quotes; empty output → "produced no output" (with inputs echoed); whitespace-only → same; no JSON → "produced no valid JSON"; JSON array for an object model → "data structure"; wrong schema → "data structure"; unrepairable garbage that contains a `{` (e.g. `"{ this is : : not json at all"`) → `ValueError` whose message starts with "Invalid". Replace the 11 `_attempt_json_repair` tests with parse-level tests feeding the same 11 broken inputs through `parse_crewai_output` with a small local model, asserting the same repaired values — for each input `json_repair` cannot repair to the same value, keep the test with the value `json_repair` produces and list it in your report. Delete the 5 tests that used local stand-in models named `BookSummaryReport` / `SalesProspectingReport` (Task 2 covers BookSummary on the real model; the Sales branches are deleted as dead: the real `SalesProspectingReport` has no `sales_metrics` field). Add the Review Focus 4 test:

```python
class OptionalNote(BaseModel):
    name: str
    note: str | None = None


def test_python_none_literal_is_read_by_json_repair():
    model = parse_crewai_output(SimpleNamespace(raw='{"name": "a", "note": None}', output=None), OptionalNote)
    # json_repair reads a bare None as the text "None" (the old regex repair produced null).
    assert model.note == "None"
```

If `json_repair` produces `None` instead, assert `None` and say so in the report.

- [ ] **Step 3: Run the new tests** — they fail where the old implementation differs (repair-path messages, deleted helpers).

- [ ] **Step 4: Rewrite `parsing.py`**

```python
"""Parse a CrewAI output into a Pydantic model.

Model-specific fixes live on the models as `mode="before"` validators; this module
only finds the JSON, repairs it with json_repair and validates.

Public API:
- parse_crewai_output
"""

import re
from typing import Any

import json_repair
from loguru import logger
from pydantic import BaseModel, ValidationError

_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
_SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def _sanitize(text: str) -> str:
    """Drop thousand separators inside numbers (1,234,567) and straighten smart quotes."""
    return _THOUSANDS.sub("", text).translate(_SMART_QUOTES)


def parse_crewai_output[T: BaseModel](report_content: Any, model_class: type[T], inputs: dict | None = None) -> T:
    """Return `model_class` from a CrewAI output (pydantic passthrough, or repaired raw JSON).

    Raises:
        ValueError: empty output, no JSON, unrepairable JSON, or data that does not fit the model.
    """
    name = model_class.__name__
    if isinstance(getattr(report_content, "output", None), model_class):
        return report_content.output

    raw = (getattr(report_content, "raw", "") or "").strip()
    if not raw:
        inputs_info = f" Inputs were: {inputs}" if inputs else ""
        raise ValueError(f"{name} crew produced no output. Check input variables and crew configuration.{inputs_info}")

    match = re.search(r"[\[{]", raw)
    if match is None:
        raise ValueError(f"{name} crew produced no valid JSON. Raw output started with: {raw[:200]!r}")
    if match.start():
        logger.debug(f"Skipping {match.start()} characters before the JSON in {name} output")

    try:
        data = json_repair.loads(_sanitize(raw[match.start():]))
    except Exception as exc:  # noqa: BLE001 - any repair failure is reported the same way
        raise ValueError(f"Invalid JSON output from {name} crew: {exc}") from exc
    if not isinstance(data, dict | list):
        raise ValueError(f"Invalid JSON output from {name} crew: could not read a JSON object")

    try:
        return model_class.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid {name} data structure: {exc}") from exc
```

This deletes `_attempt_json_repair`, the nested brace matcher, both model-specific branches, and the `debug/failed_json_*` / `debug/repair_attempt_*` file writes (the flow already dumps every crew's raw output with `dump_crewai_state` before parsing). Keep `from __future__ import annotations` only if the file needs it. Check `src/epic_news/utils/diagnostics/__init__.py` still exports `parse_crewai_output` and nothing it exported was deleted (if `_attempt_json_repair` or another helper is exported/imported elsewhere, remove that import — `rg -n "_attempt_json_repair|find_json_end" src tests`).

- [ ] **Step 5: Run everything**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics -q` → PASS, including the characterisation test (golden files unchanged — `git status tests/fixtures` shows nothing).
Run: `env -u VIRTUAL_ENV uv run pytest -q`, `uv run mypy src/epic_news`, `uv run ruff check .`.
Run: `uv run ruff check --select C901 --config lint.mccabe.max-complexity=9 src/epic_news/utils/diagnostics/parsing.py` → no finding. Report `parse_crewai_output`'s line count.

- [ ] **Step 6: Dead code your change orphaned** — `normalize_metric_type` and `normalize_structured_data_report` (`src/epic_news/utils/data_normalization.py`) lose their callers in `parsing.py`. `rg -n "normalize_metric_type|normalize_structured_data_report" src tests`: if the only remaining users are inside `data_normalization.py` itself and `tests/scripts/regenerate_sales_prospecting.py` (a one-off script for the removed `sales_metrics` shape), report them as candidates and leave them (pre-existing code outside this task's change; the user decides).

- [ ] **Step 7: Docs** — in `src/epic_news/utils/CLAUDE.md`, "Diagnostics and parsing": `parse_crewai_output` uses a pydantic output when present, else repairs the raw JSON with `json_repair` (fences, prose and trailing text are ignored) and validates; model-specific fixes belong on the model as `mode="before"` validators; it raises `ValueError` on empty/invalid output. Update the line in the directory tree if it mentions the repair.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock src/epic_news/utils/diagnostics src/epic_news/utils/CLAUDE.md tests/utils/diagnostics
git commit -m "refactor(parsing): repair crew JSON with json_repair; model fixes live on the models"
```

Controller: full suite, ruff, mypy; one live run of an affected crew (`EPIC_ENABLE_EMAIL=false env -u VIRTUAL_ENV uv run python scripts/bench_flow.py pestel` — goes through `load_or_parse_model`) before the PR; PR description with the line/complexity numbers and the Review Focus 4 outcome.
