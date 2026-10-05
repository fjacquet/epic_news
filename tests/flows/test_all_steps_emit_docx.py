"""Every report step leaves state.output_file on a DOCX under output/ and writes no HTML.

Crew kickoffs, model parsing and the DOCX assemblers are stubbed (no LLM, no pandoc);
the steps run from a tmp cwd so any file they write lands under tmp_path/output/.
"""

import asyncio
import dataclasses
from collections import defaultdict
from unittest.mock import MagicMock

import pytest

import epic_news.main as main_mod
from epic_news import crew_registry
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
    model = MagicMock()
    model.model_dump_json.return_value = '{"ok": true}'
    monkeypatch.setattr(main_mod, "load_or_parse_model", lambda *a, **k: model)
    monkeypatch.setattr(main_mod, "close_mcp", lambda crew: None)
    # Every assembler but OSINT takes (model, inputs, output_path, ...); OSINT takes (inputs, output_path).
    for name in dir(main_mod):
        if name.startswith("assemble_") and name.endswith("_docx"):
            monkeypatch.setattr(main_mod, name, lambda *a, **k: a[-1])
    # The standard steps take their assembler from the registry.
    for key, spec in crew_registry.CREW_REGISTRY.items():
        monkeypatch.setitem(
            crew_registry.CREW_REGISTRY, key, dataclasses.replace(spec, docx_assembler=lambda *a, **k: a[-1])
        )
    # Recipe step
    monkeypatch.setattr(main_mod, "recipe_from_result", lambda *a, **k: MagicMock())
    monkeypatch.setattr(main_mod, "export_recipe", lambda *a, **k: None)

    # RSS weekly step
    async def fake_fetch(**kwargs):
        return None

    monkeypatch.setattr(main_mod, "fetch_articles_from_opml", fake_fetch)
    monkeypatch.setattr(main_mod, "load_rss_weekly_report", lambda path: MagicMock())
    # Deep research step (no Wikipedia MCP)
    monkeypatch.setattr(main_mod, "DeepResearchCrew", type("DeepResearchCrew", (), {}))
    # Menu step: a validated plan, no recipe crews
    service = MagicMock()
    service.generate_menu_plan.return_value = MagicMock()
    monkeypatch.setattr(main_mod, "MenuDesignerService", lambda: service)
    monkeypatch.setattr(main_mod, "MenuGenerator", MagicMock)
    monkeypatch.setattr(ReceptionFlow, "_generate_menu_recipes", lambda self, specs: [])
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
    ("generate_rss_weekly", "output/rss_weekly/report.docx"),
    ("generate_deep_research", "output/deep_research/report.docx"),
    ("generate_menu_designer", "output/menu_designer/menu.docx"),
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


# step -> (assembler it calls, output_file the step sets before building the report)
ERROR_CASES = [
    ("generate_saint_daily", "assemble_saint_docx", "output/saint_daily/report.json"),
    ("generate_pestel", "assemble_pestel_docx", "output/pestel/report.json"),
    ("generate_rss_weekly", "assemble_rss_docx", ""),
    ("generate_osint", "assemble_osint_docx", "output/osint/global_report.json"),
]


_STANDARD_ASSEMBLER_KEYS = {"assemble_saint_docx": "SAINT", "assemble_pestel_docx": "PESTEL"}


@pytest.mark.parametrize("method,assembler,before", ERROR_CASES, ids=[c[0] for c in ERROR_CASES])
def test_assembler_error_stops_the_step(flow, monkeypatch, tmp_path, method, assembler, before):
    """A report that cannot be built raises out of the step; output_file never names a DOCX."""

    def boom(*a, **k):
        raise RuntimeError("pandoc failed")

    if assembler in _STANDARD_ASSEMBLER_KEYS:  # standard steps take their assembler from the registry
        key = _STANDARD_ASSEMBLER_KEYS[assembler]
        monkeypatch.setitem(
            crew_registry.CREW_REGISTRY,
            key,
            dataclasses.replace(crew_registry.CREW_REGISTRY[key], docx_assembler=boom),
        )
    else:
        monkeypatch.setattr(main_mod, assembler, boom)
    with pytest.raises(RuntimeError, match="pandoc failed"):
        result = getattr(flow, method)()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    assert flow.state.output_file == before
    assert not list((tmp_path / "output").rglob("*.docx"))
    assert flow.state.report is None  # a failed report step stores no result


def test_osint_keeps_sub_report_json(flow, tmp_path):
    asyncio.run(flow.generate_osint())

    osint = tmp_path / "output" / "osint"
    assert (osint / "company_profile.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert not list(osint.glob("*.html"))


def test_rss_undecodable_translation_stops_the_run(flow, monkeypatch):
    """A translated JSON that cannot be decoded raises; no report step runs after it."""

    class _BadOutput:
        raw = "not json at all"

    async def bad_akickoff(crew, inputs):
        return _BadOutput()

    monkeypatch.setattr(main_mod, "akickoff_flow", bad_akickoff)
    emitted = []
    monkeypatch.setattr(main_mod, "emit_report", lambda *a, **k: emitted.append(1))

    with pytest.raises(ValueError):
        asyncio.run(flow.generate_rss_weekly())

    assert emitted == []
