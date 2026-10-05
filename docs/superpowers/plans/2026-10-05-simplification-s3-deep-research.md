# Simplification S3 — Deep Research on the Standard Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deep research uses one `DeepResearchReport` schema, loads it with `load_or_parse_model` like every other crew, and builds its DOCX from what the crew actually wrote; `utils/extractors/` and its fabricated fallback report are deleted.

**Architecture:** The crew's `output_pydantic` schema (today `models/crews/deep_research_report.py`) becomes the only schema and moves into `models/crews/deep_research.py`, replacing the flow schema that the crew never produces. A `mode="before"` validator accepts the old key names (section `title`, top-level `summary`) and nothing else; it never invents content. `generate_deep_research` deletes any stale `report.json`, runs the crew, calls `load_or_parse_model` (unusable output raises `ValueError` and stops the run) and `emit_report`. The DOCX assembler reads section titles from `section_title` and lists the unique sources gathered from the sections.

**Tech Stack:** Python 3.13, Pydantic 2, CrewAI 1.15.23, pandoc (system), pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S3, revised 2026-10-05 for DOCX only; decisions 4–6). Survey: `.superpowers/sdd/simplification-s3/deep-research-map.md` (taken before S5; S5 since removed the HTML closure, so only the extractor path and the DOCX path remain).

Facts this plan relies on (checked on `main` at `fca43a8`):

- The crew's `report_writing_task` has `output_pydantic=DeepResearchReport` from `deep_research_report.py` (crews/deep_research/deep_research.py:10) and writes `output/deep_research/report.json`. The flow (main.py:1003-1022) reads that file through `DeepResearchExtractor`, which adapts it to the *other* schema in `models/crews/deep_research.py` and, when it cannot, returns a placeholder report with a fake `https://example.com/source` URL and a 2023-01-01 date (never raises).
- The DOCX assembler (`utils/docx_report/crews/deep_research.py`) reads the flow schema: `rs.title`, `model.conclusions`, `model.recommendations`, `model.limitations`, top-level `model.sources`. The crew never produces conclusions, recommendations, limitations or top-level sources, so today the DOCX "Sources" section is always empty.
- Recorded crew output `debug/crewai_state_deep_research_1785774338.json` (`raw`, 19,018 chars, public research on BeeGFS) validates against the crew schema: 5 sections, 4 key findings, methodology present, 10 section sources of which 6 unique URLs, no `None` URL.
- `utils/extractors/` is 421 lines; its only callers are main.py:106/1011, `tests/utils/test_deep_research_extraction_integrity.py` and `tests/scripts/test_deep_research_extractor.py`.
- The crew settings snapshot (`tests/crews/snapshots/crew_settings.json`) records `"output_pydantic": "DeepResearchReport"` by class name only.

## Global Constraints

- One `DeepResearchReport` schema; its before-validator absorbs `_adapt_json_to_model` as key renames only — never its fabricated sources, dates or placeholder report (spec S3).
- `generate_deep_research` uses `load_or_parse_model` + `emit_report` like other crews; `utils/extractors/` is deleted (spec S3).
- Characterisation: the DOCX built from a recorded deep-research output (fake LLM) keeps every section title, finding and source of that output; unusable output stops the run (spec S3).
- A report-building error stops the run; nothing partial is emailed (decision 4). No placeholder or invented report content (user decision; ADR-017).
- Every crew keeps its own `@listen` Flow step; no helper layer around CrewAI `Agent`/`Task`/`Crew` (decisions 2, 5). No crew prompt change.
- The crew's `output_pydantic` contract keeps its resilience: `methodology` defaults to `""`, `confidence_level` to `"Medium"`, `sources_count` is computed from the sections (existing tests in `tests/models/test_deep_research_report_resilience.py`).
- Files written for reports stay under `output/` (ADR-015).
- The repo is PUBLIC: committed fixtures carry no personal data (emails, phone numbers, LinkedIn handles, private names).
- Project rules: `uv` only, imports at the top of the file, Loguru, Python 3.13 union syntax, mypy `warn_unused_ignores` (remove ignores your change makes unused), never `ruff format` the pre-existing unformatted Markdown files.

## Review Focus

1. A `report.json` left by an earlier run (possibly another topic) must not be reused when this run's crew does not write one: the step deletes it before the kickoff (test in Task 2).
2. The same source cited in several sections must be listed once in the DOCX "Sources" section; the recorded output has 10 citations of 6 URLs (test in Task 2).
3. A source without a URL must print its title alone, never `None` (test in Task 2).
4. Crew output that uses the old section key `title` instead of `section_title`, or `summary` instead of `executive_summary`, must keep its headings and summary (test in Task 2).
5. Crew output that is not usable JSON and no `report.json` on disk must raise `ValueError`, build no DOCX and leave `state.output_file` unchanged (test in Task 2).

---

### Task 1: Record the deep-research characterisation fixture

**Files:**
- Create: `tests/fixtures/raw_outputs/deep_research.txt`
- Create: `tests/fixtures/raw_outputs/expected/deep_research.json` (generated)
- Modify: `tests/utils/diagnostics/test_parsing_characterisation.py` (add the case)

**Interfaces:**
- Produces: the fixture file `tests/fixtures/raw_outputs/deep_research.txt` (the crew's raw JSON output) and its golden model dump, both used by Task 2.

- [ ] **Step 1: Copy the recorded raw output into the fixture**

```bash
env -u VIRTUAL_ENV uv run python - <<'EOF'
import json
from pathlib import Path
raw = json.loads(Path("debug/crewai_state_deep_research_1785774338.json").read_text(encoding="utf-8"))["raw"]
Path("tests/fixtures/raw_outputs/deep_research.txt").write_text(raw, encoding="utf-8")
print(len(raw))
EOF
```

Expected: prints `19018`. If `debug/` does not hold that file (it is gitignored), stop and report NEEDS_CONTEXT.

- [ ] **Step 2: Check the fixture for personal data (the repo is public)**

```bash
grep -nE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|linkedin\.com/in/|\+?[0-9][0-9 ().-]{8,}[0-9]" tests/fixtures/raw_outputs/deep_research.txt
```

Expected: no output (or only version numbers / benchmark figures, which you list in your report). Then read the fixture once and list in your report every person's name it contains. Authors of cited public papers or projects are acceptable; anything else (a private individual, an employee contact) gets replaced by `redacted` in the fixture before going further.

- [ ] **Step 3: Add the case to the parsing characterisation test**

In `tests/utils/diagnostics/test_parsing_characterisation.py`, add the import and the case (keep the other cases unchanged):

```python
from epic_news.models.crews.deep_research_report import DeepResearchReport
```

```python
CASES = {
    "company_profile": CompanyProfileReport,
    "tech_stack": TechStackReport,
    "web_presence": WebPresenceReport,
    "hr_intelligence": HRIntelligenceReport,
    "cross_reference_report": CrossReferenceReport,
    "deep_research": DeepResearchReport,
    "newsdaily": NewsDailyReport,
    "pestel": PestelReport,
    "sales_prospecting": SalesProspectingReport,
}
```

- [ ] **Step 4: Run it to see it fail (no golden yet)**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics/test_parsing_characterisation.py -k deep_research -v`
Expected: FAIL with `FileNotFoundError` on `expected/deep_research.json`.

- [ ] **Step 5: Generate the golden with today's crew schema**

Run: `UPDATE_PARSING_GOLDEN=1 env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics/test_parsing_characterisation.py -k deep_research -q`
Then: `env -u VIRTUAL_ENV uv run pytest tests/utils/diagnostics/test_parsing_characterisation.py -v`
Expected: all 9 cases PASS. Check with `git status` that only `expected/deep_research.json` was written among the goldens.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/raw_outputs/deep_research.txt tests/fixtures/raw_outputs/expected/deep_research.json tests/utils/diagnostics/test_parsing_characterisation.py
git commit -m "test: pin a recorded deep-research output (S3 characterisation)"
```

---

### Task 2: One schema, standard flow step, no extractor

**Files:**
- Modify: `src/epic_news/models/crews/deep_research.py` (replace its content with the crew schema + before-validator + `unique_sources`)
- Delete: `src/epic_news/models/crews/deep_research_report.py`
- Modify: `src/epic_news/crews/deep_research/deep_research.py:10` (import path)
- Modify: `src/epic_news/utils/docx_report/crews/deep_research.py`
- Modify: `src/epic_news/main.py` (`generate_deep_research`, ~975-1032; imports at lines 69 and 106)
- Delete: `src/epic_news/utils/extractors/` (whole package)
- Delete: `tests/utils/test_deep_research_extraction_integrity.py`, `tests/scripts/test_deep_research_extractor.py`
- Modify: `tests/models/test_deep_research_report_resilience.py` (import path), `tests/utils/diagnostics/test_parsing_characterisation.py` (import path), `tests/utils/docx_report/crews/test_deep_research.py` (rewrite)
- Create: `tests/models/test_deep_research_key_renames.py`, `tests/utils/docx_report/crews/test_deep_research_characterisation.py`, `tests/test_generate_deep_research_flow.py`

**Interfaces:**
- Consumes: Task 1's `tests/fixtures/raw_outputs/deep_research.txt` and `expected/deep_research.json`.
- Produces: `epic_news.models.crews.deep_research` exports `ResearchSource`, `ResearchSection`, `DeepResearchReport`; `DeepResearchReport.unique_sources -> list[ResearchSource]` (property). `ContentState.deep_research_report` keeps its import path and now holds this model.

- [ ] **Step 1: Write the failing model tests**

Create `tests/models/test_deep_research_key_renames.py`:

```python
"""The single DeepResearchReport accepts old key names but never invents content (S3)."""

from epic_news.models.crews.deep_research import DeepResearchReport

_SOURCE = {"title": "a", "url": "https://a", "source_type": "web", "summary": "s", "relevance_score": 8}


def test_section_title_key_is_accepted():
    report = DeepResearchReport.model_validate(
        {
            "title": "T",
            "topic": "Topic",
            "executive_summary": "Summary",
            "research_sections": [{"title": "Heading", "content": "body"}],
        }
    )
    assert report.research_sections[0].section_title == "Heading"


def test_summary_key_is_accepted_and_topic_falls_back_to_title():
    report = DeepResearchReport.model_validate({"title": "T", "summary": "Sum"})
    assert report.executive_summary == "Sum"
    assert report.topic == "T"


def test_nothing_is_invented():
    report = DeepResearchReport.model_validate(
        {"title": "T", "topic": "Topic", "executive_summary": "S", "research_sections": []}
    )
    assert report.key_findings == []
    assert report.research_sections == []
    assert report.report_date is None
    assert report.unique_sources == []


def test_unique_sources_dedupes_by_url_then_title():
    no_url = {**_SOURCE, "title": "offline", "url": None}
    report = DeepResearchReport.model_validate(
        {
            "title": "T",
            "topic": "Topic",
            "executive_summary": "S",
            "research_sections": [
                {"section_title": "A", "content": "x", "sources": [_SOURCE, no_url]},
                {"section_title": "B", "content": "y", "sources": [{**_SOURCE, "title": "a again"}, no_url]},
            ],
        }
    )
    assert [(s.title, s.url) for s in report.unique_sources] == [("a", "https://a"), ("offline", None)]
    assert report.sources_count == 4  # citations, unchanged contract
```

In `tests/models/test_deep_research_report_resilience.py` and `tests/utils/diagnostics/test_parsing_characterisation.py`, change the import to:

```python
from epic_news.models.crews.deep_research import DeepResearchReport
```

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/models/test_deep_research_key_renames.py tests/models/test_deep_research_report_resilience.py -q`
Expected: FAIL (the flow schema has no `topic`/`section_title`/`unique_sources`; `conclusions` is required).

- [ ] **Step 3: Replace the schema**

Replace the whole content of `src/epic_news/models/crews/deep_research.py` with:

```python
"""The deep-research report: the crew's output_pydantic contract and the DOCX input.

One schema (simplification S3). The before-validator accepts older key names; it never
invents content, so a field the crew did not write stays empty.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ResearchSource(BaseModel):
    """Individual research source information."""

    title: str = Field(..., description="Title of the source")
    url: str | None = Field(None, description="URL of the source")
    source_type: str = Field(..., description="Type: web, wikipedia, news, etc.")
    summary: str = Field(..., description="Key information from this source")
    relevance_score: int = Field(..., description="Relevance score 1-10", ge=1, le=10)


class ResearchSection(BaseModel):
    """Thematic section of research."""

    section_title: str = Field(..., description="Title of the research section")
    content: str = Field(..., description="Detailed content for this section")
    sources: list[ResearchSource] = Field(default_factory=list, description="Sources supporting this section")


class DeepResearchReport(BaseModel):
    """Comprehensive research report model.

    This is the crew's ``output_pydantic`` contract, so the LLM must produce it in one
    shot. Fields the model reliably supplies stay required; three that a small model
    intermittently omitted are made resilient, because a single omission failed the
    whole (~9-minute) research run via ``output_pydantic`` validation:

    * ``sources_count`` is *computed* from the sections below, never trusted from the
      LLM -- counting is a deterministic job a model should not be asked to do.
    * ``methodology`` and ``confidence_level`` default rather than hard-fail.
    """

    title: str = Field(..., description="Main title of the research report")
    topic: str = Field(..., description="Research topic")
    executive_summary: str = Field(..., description="High-level summary of findings")
    key_findings: list[str] = Field(default_factory=list, description="List of key discoveries")
    research_sections: list[ResearchSection] = Field(
        default_factory=list, description="Detailed research sections"
    )
    methodology: str = Field("", description="Research methodology used")
    sources_count: int = Field(0, description="Total number of sources consulted (computed)")
    report_date: str | None = Field(None, description="Report generation date")
    confidence_level: str = Field("Medium", description="Overall confidence in findings: High, Medium, Low")

    @model_validator(mode="before")
    @classmethod
    def _accept_old_key_names(cls, data: Any) -> Any:
        """Rename keys older outputs used (section ``title``, top-level ``summary``).

        ``topic`` falls back to the report ``title``. Nothing else is filled in.
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "executive_summary" not in data and "summary" in data:
            data["executive_summary"] = data["summary"]
        if "topic" not in data and "title" in data:
            data["topic"] = data["title"]
        sections = data.get("research_sections")
        if isinstance(sections, list):
            data["research_sections"] = [
                {**s, "section_title": s["title"]}
                if isinstance(s, dict) and "section_title" not in s and "title" in s
                else s
                for s in sections
            ]
        return data

    @model_validator(mode="after")
    def _count_sources(self) -> "DeepResearchReport":
        """Derive ``sources_count`` from the sections instead of trusting the LLM.

        Falls back to any value supplied on the model only when no section carries a
        source, so a hand-built report with an explicit count is preserved.
        """
        counted = sum(len(section.sources) for section in self.research_sections)
        self.sources_count = counted or self.sources_count
        return self

    @property
    def unique_sources(self) -> list[ResearchSource]:
        """Sources cited across sections, first occurrence kept, keyed by URL (else title)."""
        seen: set[str] = set()
        unique: list[ResearchSource] = []
        for section in self.research_sections:
            for source in section.sources:
                key = source.url or source.title
                if key not in seen:
                    seen.add(key)
                    unique.append(source)
        return unique
```

Then `git rm src/epic_news/models/crews/deep_research_report.py` and change `src/epic_news/crews/deep_research/deep_research.py:10` to:

```python
from epic_news.models.crews.deep_research import DeepResearchReport
```

The old `test_phantom_fields_from_the_old_instructions_are_ignored` (asserts `not hasattr(report, "conclusions")`) stays valid: the single schema has no `conclusions`.

- [ ] **Step 4: Run the model tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/models/test_deep_research_key_renames.py tests/models/test_deep_research_report_resilience.py tests/utils/diagnostics/test_parsing_characterisation.py tests/crews -q`
Expected: PASS, including the `deep_research` golden from Task 1 (the dump must be byte-identical: the schema is the crew schema plus a before-validator and a property, which `model_dump` ignores) and the crew settings snapshot.

- [ ] **Step 5: Write the failing DOCX tests**

Replace `tests/utils/docx_report/crews/test_deep_research.py` with:

```python
import zipfile

from epic_news.models.crews.deep_research import DeepResearchReport, ResearchSection, ResearchSource
from epic_news.utils.docx_report.crews.deep_research import assemble_deep_research_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def _source(title, url):
    return ResearchSource(title=title, url=url, source_type="web", summary="s", relevance_score=8)


def test_deep_research_docx(tmp_path):
    model = DeepResearchReport(
        title="T",
        topic="Topic",
        executive_summary="ES",
        methodology="method",
        key_findings=["Finding-Alpha", "Finding-Beta"],
        research_sections=[
            ResearchSection(
                section_title="Sec1",
                content="c1",
                sources=[_source("Source-Alpha", "https://a.example"), _source("Source-Offline", None)],
            ),
            ResearchSection(
                section_title="Sec2",
                content="c2",
                sources=[_source("Source-Alpha again", "https://a.example"), _source("Source-Beta", "https://b.example")],
            ),
        ],
    )
    llm = _StubLLM()
    out = assemble_deep_research_docx(
        model, {"current_date": "2026-10-05"}, str(tmp_path / "output" / "r.docx"), llm
    )
    txt = _text(out)
    assert "Finding-Alpha" in txt and "Finding-Beta" in txt
    assert "3 sources consultées" in txt  # https://a.example listed once
    assert "Source-Alpha" in txt and "Source-Beta" in txt and "Source-Offline" in txt
    assert "Source-Alpha again" not in txt
    assert "None" not in txt  # a source without URL prints its title alone
    # narrated: executive summary + 2 research sections + methodology
    assert llm.calls == 4
    headings = ["Résumé exécutif", "Principales découvertes", "Sec1", "Sec2", "Méthodologie", "Sources"]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
    for gone in ("Conclusions", "Recommandations", "Limitations"):
        assert gone not in txt
```

Create `tests/utils/docx_report/crews/test_deep_research_characterisation.py`:

```python
"""The DOCX built from a recorded deep-research output keeps its titles, findings and sources (S3)."""

import zipfile
from pathlib import Path
from types import SimpleNamespace

from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.utils.diagnostics import parse_crewai_output
from epic_news.utils.docx_report.crews.deep_research import assemble_deep_research_docx

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "raw_outputs" / "deep_research.txt"


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


_TYPOGRAPHY = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def _text(p):
    """document.xml with Pandoc's smart quotes straightened (the fixture has d'Hypothèses)."""
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode().translate(_TYPOGRAPHY)


def _xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def test_recorded_output_keeps_titles_findings_and_sources(tmp_path):
    raw = FIXTURE.read_text(encoding="utf-8")
    model = parse_crewai_output(SimpleNamespace(raw=raw, output=None), DeepResearchReport)
    llm = _StubLLM()
    out = assemble_deep_research_docx(
        model, {"current_date": "2026-10-05"}, str(tmp_path / "output" / "r.docx"), llm
    )
    txt = _text(out)
    assert len(model.research_sections) == 5
    for section in model.research_sections:
        assert _xml(section.section_title) in txt
    for finding in model.key_findings:
        assert _xml(finding) in txt
    assert len(model.unique_sources) == 6
    for source in model.unique_sources:
        assert _xml(source.url or source.title) in txt
    assert f"{len(model.unique_sources)} sources consultées" in txt
    assert llm.calls == 7  # executive summary + 5 sections + methodology
```

If a finding or title still fails only because Pandoc changed other typography (dashes, ellipses, non-breaking spaces), extend `_TYPOGRAPHY` for that character and say so in your report; do not weaken the assertion to a subset.

- [ ] **Step 6: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/docx_report/crews/test_deep_research.py tests/utils/docx_report/crews/test_deep_research_characterisation.py -q`
Expected: FAIL (`AttributeError: 'ResearchSection' object has no attribute 'title'` or `'DeepResearchReport' object has no attribute 'conclusions'`).

- [ ] **Step 7: Update the assembler**

In `src/epic_news/utils/docx_report/crews/deep_research.py`, replace the module docstring, the import, `_sources_block` and the body of `assemble_deep_research_docx` from the research-section loop to the Sources section:

```python
"""DEEPRESEARCH → DOCX: narrated prose + deterministic findings/sources.

Consumes ``DeepResearchReport`` (``models/crews/deep_research.py``), the crew's own
output schema. Sources are the unique sources cited across the research sections.
"""
```

```python
from epic_news.models.crews.deep_research import DeepResearchReport, ResearchSource
```

```python
def _sources_block(sources: list[ResearchSource]) -> str:
    """Deterministic Sources section: a count line plus a verbatim bullet per source."""
    if not sources:
        return "_Aucune source._"
    lines = [f"{len(sources)} sources consultées.", ""]
    lines += [f"- {s.title} — {s.url}" if s.url else f"- {s.title}" for s in sources]
    return "\n".join(lines)
```

```python
    for rs in research_sections[:_MAX_SECTIONS]:
        sections.append(
            Section(
                rs.section_title,
                instruction="Développe cette section en prose détaillée.",
                context=rs.content or "",
            )
        )
    sections.append(
        Section("Méthodologie", instruction="Décris la méthodologie.", context=model.methodology or "")
    )
    sections.append(Section("Sources", body=_sources_block(model.unique_sources)))
```

(The Conclusions / Recommandations / Limitations blocks go: the crew never writes those fields.)

- [ ] **Step 8: Run the DOCX tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/docx_report -q`
Expected: PASS.

- [ ] **Step 9: Write the failing flow tests**

Create `tests/test_generate_deep_research_flow.py`:

```python
"""generate_deep_research: standard load_or_parse_model + emit_report path (S3)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "raw_outputs" / "deep_research.txt"


class _StubCrew:
    pass


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str, write_file: bool) -> list[str]:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    (tmp_path / "output" / "deep_research").mkdir(parents=True)
    built: list[str] = []

    def _kickoff(_crew, inputs):
        if write_file:
            Path(inputs["output_file"]).write_text(raw, encoding="utf-8")
        return SimpleNamespace(raw=raw, output=None)

    def _assemble(model, _inputs, output_path, llm=None):
        built.append(model.title)
        Path(output_path).write_bytes(b"docx")
        return output_path

    monkeypatch.setattr(main_module, "DeepResearchCrew", _StubCrew)
    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    monkeypatch.setattr(main_module, "close_mcp", lambda _crew: None)
    monkeypatch.setattr(main_module, "dump_crewai_state", lambda *_a, **_k: None)
    monkeypatch.setattr(main_module, "assemble_deep_research_docx", _assemble)
    return built


def test_report_json_from_the_crew_builds_the_docx(tmp_path, monkeypatch):
    raw = FIXTURE.read_text(encoding="utf-8")
    built = _setup(tmp_path, monkeypatch, raw, write_file=True)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    flow.generate_deep_research()
    assert flow.state.output_file == "output/deep_research/report.docx"
    assert flow.state.deep_research_report is not None
    assert len(flow.state.deep_research_report.research_sections) == 5
    assert built == [flow.state.deep_research_report.title]


def test_stale_report_json_is_not_reused(tmp_path, monkeypatch):
    built = _setup(tmp_path, monkeypatch, "not json at all", write_file=False)
    stale = tmp_path / "output" / "deep_research" / "report.json"
    stale.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    flow = ReceptionFlow(user_request="deep research on something else")
    with pytest.raises(ValueError):
        flow.generate_deep_research()
    assert not stale.exists()
    assert built == []


def test_unusable_output_stops_the_run(tmp_path, monkeypatch):
    built = _setup(tmp_path, monkeypatch, "not json at all", write_file=False)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    before = flow.state.output_file
    with pytest.raises(ValueError):
        flow.generate_deep_research()
    assert built == []
    assert flow.state.output_file in (before, "output/deep_research/report.json")
    assert not (tmp_path / "output" / "deep_research" / "report.docx").exists()


def test_raw_output_is_used_when_the_crew_wrote_no_file(tmp_path, monkeypatch):
    raw = FIXTURE.read_text(encoding="utf-8")
    built = _setup(tmp_path, monkeypatch, raw, write_file=False)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    flow.generate_deep_research()
    assert flow.state.output_file == "output/deep_research/report.docx"
    assert len(built) == 1
```

If `ReceptionFlow(...)` construction or `dump_crewai_state` needs other patches in this repo (compare with `tests/test_generate_deep_research_mcp_cleanup.py`), add only those; keep the assertions.

- [ ] **Step 10: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_generate_deep_research_flow.py -q`
Expected: FAIL (`test_stale_report_json_is_not_reused`: the stale file is read by the extractor and a DOCX is built; `test_unusable_output_stops_the_run` may pass already through `parse_crewai_output`, which is fine).

- [ ] **Step 11: Rewrite the flow step**

In `src/epic_news/main.py`, replace the body of `generate_deep_research` from `# Kickoff-only orchestration` to the end of the method with:

```python
        # A report.json left by an earlier run must not be read as this run's output.
        Path(output_file).unlink(missing_ok=True)

        deep_research_crew = DeepResearchCrew()
        try:
            output = kickoff_flow(deep_research_crew, inputs)
        finally:
            # CrewBase stops the Wikipedia MCP server only after a successful kickoff.
            close_mcp(deep_research_crew)
        dump_crewai_state(output, "DEEP_RESEARCH")

        model = load_or_parse_model(output_file, DeepResearchReport, output, inputs, "deep_research")
        self.state.deep_research_report = model

        emit_report(
            self.state,
            lambda: assemble_deep_research_docx(model, inputs, "output/deep_research/report.docx"),
        )
        self.logger.info(f"✅ Deep research report generated → {self.state.output_file}")
```

Then:
- delete the import `from epic_news.utils.extractors.deep_research import DeepResearchExtractor` (main.py:106);
- keep `from epic_news.models.crews.deep_research import DeepResearchReport` (main.py:69);
- make sure `Path` and `load_or_parse_model` are imported at the top (they are used by other steps; add only if missing);
- remove `cast`, `parse_crewai_output` or `os` from the imports only if this change left them unused (`uv run ruff check` tells you).

- [ ] **Step 12: Delete the extractor package and its tests**

```bash
git rm -r src/epic_news/utils/extractors tests/utils/test_deep_research_extraction_integrity.py tests/scripts/test_deep_research_extractor.py
grep -rnE "extractors|DeepResearchExtractor|ContentExtractorFactory|GenericExtractor|deep_research_report import" src tests scripts --include='*.py'
```

Expected: the grep prints nothing. (The only test in the deleted integrity file worth keeping, "the state field holds the report class", is covered by `test_report_json_from_the_crew_builds_the_docx`.)

- [ ] **Step 13: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check .
uv run mypy src/epic_news
```
Expected: all tests pass; ruff and mypy clean. Report the before/after test counts and `git diff --shortstat <task base> HEAD`.

- [ ] **Step 14: Commit**

```bash
git add -A src/epic_news tests
git commit -m "refactor(deep_research): one schema, standard flow step, no extractor"
```

---

### Task 3: Docs

**Files:**
- Modify: `docs/adr/ADR-017-docx-only-reports.md` (remove the "known exception until S3" sentences in Decision and Consequences; update the deep-research LLM call count line if it changed)
- Modify: `CLAUDE.md` (root, line ~94: remove "Known exception until S3 ...")
- Modify: `src/epic_news/utils/CLAUDE.md` (remove the `extractors/` tree line ~17 and the `ContentExtractorFactory` paragraph ~96)
- Modify: `src/epic_news/crews/CLAUDE.md` only if it names `deep_research_report.py` or the extractor
- Modify: `docs/explanations/architecture.md`, `docs/reference/*.md`, `README.md` only where they name the extractor or the two deep-research schemas

**Interfaces:**
- Consumes: Task 2 (single schema in `models/crews/deep_research.py`; `generate_deep_research` uses `load_or_parse_model` + `emit_report`; `utils/extractors/` deleted).

- [ ] **Step 1: Find every stale statement**

```bash
grep -rnE "extractor|Extractor|deep_research_report|until S3|S3 \(" docs/adr docs/explanations docs/reference docs/how-to README.md CLAUDE.md src/epic_news/CLAUDE.md src/epic_news/*/CLAUDE.md
```

List the hits in your report. Leave `docs/superpowers/`, `docs/archive/`, `docs/pr_specs/`, `TODO.md` and `CHANGELOG.md` alone (historical).

- [ ] **Step 2: Rewrite each hit**

State what is true after Task 2, for example in ADR-017's Decision: "A report step that cannot build its file raises and stops the run, so nothing partial is emailed." with no exception clause, and in `utils/CLAUDE.md` no `extractors/` line. Keep each edit to the sentence that is wrong; do not restructure the documents.

- [ ] **Step 3: Check**

Run: the Step 1 grep again (only historical or still-true hits remain; say which), then `uv run ruff check .`.

- [ ] **Step 4: Commit**

```bash
git add docs README.md CLAUDE.md src/epic_news
git commit -m "docs: deep research has no extractor exception (S3)"
```

Do not stage `docs/audits/` (untracked, must stay out of git).

---

Controller, before the PR: live run with `EPIC_ENABLE_EMAIL=false` — add a `"deep_research"` request to `scripts/bench_requests.json` (for example `"Fais une recherche approfondie sur l'état de l'art des systèmes de fichiers parallèles en 2026"`), run `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py deep_research`, record wall clock and LiteLLM calls in `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md`, and open the DOCX: every section title, key finding and unique source URL from `output/deep_research/report.json` must appear in it. Report the radon complexity of `generate_deep_research` and the LOC delta in the PR description (spec Validation).
