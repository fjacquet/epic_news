import zipfile

from epic_news.models.crews.book_summary_report import (
    BookSummaryReport,
    BookSummarySection,
    ChapterSummary,
    TableOfContentsEntry,
)
from epic_news.utils.docx_report.crews.book_summary import assemble_book_summary_docx


class _StubLLM:
    def __init__(self):
        self.calls = 0

    def call(self, m):
        self.calls += 1
        return "prose"


def _text(p):
    with zipfile.ZipFile(p) as z:
        return z.read("word/document.xml").decode()


def test_book_summary_docx(tmp_path):
    model = BookSummaryReport(
        topic="Topic",
        publication_date="2026-07-13",
        title="T",
        author="A",
        summary="Un résumé global.",
        table_of_contents=[
            TableOfContentsEntry(id="a", title="TOC-Chapitre-Un"),
            TableOfContentsEntry(id="b", title="TOC-Chapitre-Deux"),
        ],
        sections=[BookSummarySection(id="s1", title="Section-Alpha", content="contenu alpha")],
        chapter_summaries=[ChapterSummary(chapter=1, title="Chap-Titre", focus="Chap-Focus")],
        references=["Ref-Un", "Ref-Deux"],
    )
    llm = _StubLLM()
    out = assemble_book_summary_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r.docx"), llm)
    txt = _text(out)
    # deterministic TOC verbatim
    assert "TOC-Chapitre-Un" in txt and "TOC-Chapitre-Deux" in txt
    # deterministic chapter summaries verbatim
    assert "Chap-Titre" in txt and "Chap-Focus" in txt
    # deterministic references verbatim
    assert "Ref-Un" in txt and "Ref-Deux" in txt
    # narrated: Résumé + 1 section = 2 llm calls (TOC/chapters/refs are deterministic)
    assert llm.calls == 2
    headings = [
        "Résumé",
        "Table des matières",
        "Section-Alpha",
        "Résumés de chapitres",
        "Références",
    ]
    indices = [txt.index(h) for h in headings]
    assert indices == sorted(indices)


def test_book_summary_docx_guards_none_summary_and_chapters(tmp_path):
    model = BookSummaryReport(
        topic="Topic",
        publication_date="2026-07-13",
        title="T",
        author="A",
        summary=None,
        table_of_contents=[TableOfContentsEntry(id="a", title="TOC-Only")],
        sections=[BookSummarySection(id="s1", title="Section-Alpha", content="contenu alpha")],
        chapter_summaries=None,
        references=["Ref-Un"],
    )
    llm = _StubLLM()
    out = assemble_book_summary_docx(model, {"current_date": "2026-07-13"}, str(tmp_path / "r2.docx"), llm)
    txt = _text(out)
    assert "Résumé" not in txt
    assert "Résumés de chapitres" not in txt
    # only the one section is narrated
    assert llm.calls == 1
