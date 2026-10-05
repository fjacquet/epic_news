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
                sources=[
                    _source("Source-Alpha again", "https://a.example"),
                    _source("Source-Beta", "https://b.example"),
                ],
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
