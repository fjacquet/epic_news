from types import SimpleNamespace

from epic_news.models.crews.book_summary_report import BookSummaryReport, TableOfContentsEntry
from epic_news.utils.diagnostics import parse_crewai_output
from epic_news.utils.flow_helpers import load_or_parse_model


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


def test_saved_json_with_int_ids_loads_without_fallback(tmp_path):
    path = tmp_path / "book.json"
    path.write_text(
        '{"topic": "t", "publication_date": "2020", "title": "T", "summary": "S",'
        ' "table_of_contents": [{"id": 1, "title": "One"}, {"id": 2, "title": "Two"}],'
        ' "sections": [], "chapter_summaries": [], "references": [], "author": "A"}',
        encoding="utf-8",
    )
    # A fallback whose parsing would raise: reaching it fails the test.
    unusable = SimpleNamespace(raw="", output=None)
    report = load_or_parse_model(path, BookSummaryReport, unusable)
    assert [e.id for e in report.table_of_contents] == ["1", "2"]
