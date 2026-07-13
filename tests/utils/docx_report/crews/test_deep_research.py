import zipfile

from epic_news.models.crews.deep_research_report import DeepResearchReport, ResearchSection
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


def test_deep_research_docx(tmp_path):
    model = DeepResearchReport(
        title="T",
        topic="Quantum",
        executive_summary="ES",
        key_findings=["Finding-Alpha", "Finding-Beta"],
        research_sections=[ResearchSection(section_title="Sec1", content="c1")],
        methodology="method",
        sources_count=9,
        confidence_level="High",
    )
    llm = _StubLLM()
    out = assemble_deep_research_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    assert "Finding-Alpha" in txt and "Finding-Beta" in txt  # deterministic verbatim
    assert "9 sources" in txt  # deterministic sources line
    # narrated: exec summary + 1 research section + methodology = 3 llm calls
    assert llm.calls == 3
