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
