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


def test_deep_research_docx(tmp_path):
    # Build the flow's actual model (models/crews/deep_research.py), not the
    # parallel deep_research_report.py model. This is what the ReceptionFlow emits.
    model = DeepResearchReport(
        title="T",
        executive_summary="ES",
        methodology="method",
        conclusions="ccl",
        key_findings=["Finding-Alpha", "Finding-Beta"],
        research_sections=[ResearchSection(title="Sec1", content="c1")],
        sources=[
            ResearchSource(
                url="https://a.example",
                title="Source-Alpha",
                credibility_score=0.9,
                extraction_date="2026-07-13",
            ),
            ResearchSource(
                url="https://b.example",
                title="Source-Beta",
                credibility_score=0.8,
                extraction_date="2026-07-13",
            ),
        ],
    )
    llm = _StubLLM()
    out = assemble_deep_research_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    assert "Finding-Alpha" in txt and "Finding-Beta" in txt  # deterministic findings verbatim
    assert "2 sources consultées" in txt  # deterministic sources count line
    assert "Source-Alpha" in txt and "Source-Beta" in txt  # deterministic source titles verbatim
    # narrated: exec summary + 1 research section + methodology = 3 llm calls
    # (Principales conclusions + Sources are deterministic bodies → no LLM)
    assert llm.calls == 3
    # section headings appear in the expected order
    headings = ["Résumé exécutif", "Principales conclusions", "Sec1", "Méthodologie", "Sources"]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
