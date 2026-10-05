"""Every report step leaves state.output_file on a DOCX under output/ and writes no HTML.

Crew kickoffs, model parsing and the DOCX assemblers are stubbed (no LLM, no pandoc);
the steps run from a tmp cwd so any file they write lands under tmp_path/output/.
"""

import asyncio
from collections import defaultdict
from unittest.mock import MagicMock

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow


class _Output:
    raw = "{}"
    pydantic = None


@pytest.fixture
def flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "osint").mkdir(parents=True)  # ensure_output_directories() does this at startup
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda *a, **k: _Output())
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "load_or_parse_model", lambda *a, **k: MagicMock())
    monkeypatch.setattr(main_mod, "close_mcp", lambda crew: None)
    # Every assembler but OSINT takes (model, inputs, output_path, ...); OSINT takes (inputs, output_path).
    for name in dir(main_mod):
        if name.startswith("assemble_") and name.endswith("_docx"):
            monkeypatch.setattr(main_mod, name, lambda *a, **k: a[-1])
    # Recipe step
    monkeypatch.setattr(main_mod, "recipe_from_result", lambda *a, **k: MagicMock())
    monkeypatch.setattr(main_mod, "export_recipe", lambda *a, **k: None)
    # PESTEL step
    monkeypatch.setattr(main_mod, "_pestel_recent_research", lambda topic, geo: {})
    # OSINT step: crews are only handed to the faked async kickoff
    for crew in (
        "CompanyProfilerCrew",
        "TechStackCrew",
        "WebPresenceCrew",
        "HRIntelligenceCrew",
        "LegalAnalysisCrew",
        "GeospatialAnalysisCrew",
        "CrossReferenceReportCrew",
    ):
        monkeypatch.setattr(main_mod, crew, type(crew, (), {}))

    async def fake_akickoff(crew, inputs):
        return _Output()

    model = MagicMock()
    model.model_dump_json.return_value = '{"ok": true}'
    monkeypatch.setattr(main_mod, "akickoff_flow", fake_akickoff)
    monkeypatch.setattr(main_mod, "parse_crewai_output", lambda *a, **k: model)

    f = ReceptionFlow(user_request="x")
    monkeypatch.setattr(
        type(f.state),
        "to_crew_inputs",
        lambda self: defaultdict(str, {"company": "ACME", "topic": "t", "menu_slug": "menu"}),
    )
    f.state.topic_slug = "t"
    return f


CASES = [
    ("generate_poem", "output/poem/poem.docx"),
    ("generate_saint_daily", "output/saint_daily/report.docx"),
    ("generate_news_daily", "output/news_daily/report.docx"),
    ("generate_findaily", "output/findaily/report.docx"),
    ("generate_recipe", "output/cooking/t.docx"),
    ("generate_book_summary", "output/library/book_summary.docx"),
    ("generate_sales_prospecting_report", "output/sales_prospecting/report.docx"),
    ("generate_pestel", "output/pestel/report.docx"),
    ("generate_news_company", "output/company_news/report.docx"),
    ("generate_meeting_prep", "output/meeting/meeting_preparation.docx"),
    ("generate_osint", "output/osint/report.docx"),
]


@pytest.mark.parametrize("method,expected", CASES, ids=[c[0] for c in CASES])
def test_step_emits_docx_and_no_html(flow, method, expected, tmp_path):
    result = getattr(flow, method)()
    if asyncio.iscoroutine(result):
        asyncio.run(result)

    assert flow.state.output_file == expected
    assert flow.state.output_file.endswith(".docx")
    assert not list((tmp_path / "output").rglob("*.html"))
    assert not list((tmp_path / "output").rglob("*.md"))


def test_assembler_error_stops_the_step(flow, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("pandoc failed")

    monkeypatch.setattr(main_mod, "assemble_saint_docx", boom)
    with pytest.raises(RuntimeError, match="pandoc failed"):
        flow.generate_saint_daily()
    assert not flow.state.output_file.endswith(".docx")


def test_osint_keeps_sub_report_json(flow, tmp_path):
    asyncio.run(flow.generate_osint())

    osint = tmp_path / "output" / "osint"
    assert (osint / "company_profile.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert not list(osint.glob("*.html"))
