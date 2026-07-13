import zipfile

from epic_news.models.crews.company_news_report import ArticleItem, CompanyNewsReport
from epic_news.models.crews.company_news_report import Section as CompanyNewsSection
from epic_news.utils.docx_report.crews.company_news import assemble_company_news_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def _build_model(notes: str | None) -> CompanyNewsReport:
    return CompanyNewsReport(
        summary="Résumé société.",
        sections=[
            CompanyNewsSection(
                titre="Section-Finance",
                contenu=[
                    ArticleItem(
                        article="Article-Alpha",
                        date="2026-07-13",
                        source="Reuters",
                        citation="https://r.example/1",
                    ),
                    ArticleItem(
                        article="Article-Beta",
                        date="2026-07-12",
                        source="Bloomberg",
                        citation="https://b.example/2",
                    ),
                ],
            )
        ],
        notes=notes,
    )


def test_company_news_docx(tmp_path):
    model = _build_model(notes="Note-Finale.")
    llm = _StubLLM()
    out = assemble_company_news_docx(
        model,
        {"company": "ACME-Corp", "current_date": "2026-07-13"},
        str(tmp_path / "r.docx"),
        llm,
    )
    txt = _text(out)
    # deterministic article bullets, verbatim
    assert "Article-Alpha" in txt
    assert "Reuters" in txt
    assert "https://r.example/1" in txt
    assert "Article-Beta" in txt
    # narrated: Résumé + Notes = 2 llm calls (Section-Finance is deterministic)
    assert llm.calls == 2
    # section headings appear in the expected order
    headings = ["Résumé", "Section-Finance", "Notes"]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)
    # meta title falls back to inputs["company"]
    assert "ACME-Corp" in txt


def test_company_news_docx_no_notes(tmp_path):
    model = _build_model(notes=None)
    llm = _StubLLM()
    out = assemble_company_news_docx(
        model,
        {"company": "ACME-Corp", "current_date": "2026-07-13"},
        str(tmp_path / "r.docx"),
        llm,
    )
    txt = _text(out)
    assert "Notes" not in txt
    # narrated: Résumé only = 1 llm call (no Notes section when notes is falsy)
    assert llm.calls == 1
