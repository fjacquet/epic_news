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
