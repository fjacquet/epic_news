"""The OSINT parallel run saves each report as JSON and clears stale ones first."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from epic_news import main as main_mod
from epic_news.main import ReceptionFlow


@pytest.fixture
def osint_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "osint").mkdir(parents=True)

    model = MagicMock()
    model.model_dump_json.return_value = '{"ok": true}'
    model.model_dump.return_value = {}
    renderer = MagicMock()
    renderer.render_report.return_value = "<html></html>"

    monkeypatch.setattr(main_mod, "TemplateManager", lambda: renderer)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "parse_crewai_output", lambda *a, **k: model)

    async def no_cross_reference(self, inputs, template_manager):
        return None

    monkeypatch.setattr(ReceptionFlow, "_run_cross_reference_report", no_cross_reference)

    def run(failing_crew: type | None = None) -> None:
        async def fake_kickoff(crew, inputs):
            if failing_crew is not None and isinstance(crew, failing_crew):
                raise RuntimeError("boom")
            return {"raw": "output"}

        monkeypatch.setattr(main_mod, "akickoff_flow", fake_kickoff)
        flow = ReceptionFlow(user_request="osint on Acme")
        asyncio.run(flow._run_osint_parallel())

    return tmp_path / "output" / "osint", run


@pytest.fixture(autouse=True)
def _stub_crew_constructors(monkeypatch: pytest.MonkeyPatch):
    """Crew classes are only handed to the (faked) kickoff; skip building real crews."""
    for name in (
        "CompanyProfilerCrew",
        "TechStackCrew",
        "WebPresenceCrew",
        "HRIntelligenceCrew",
        "LegalAnalysisCrew",
        "GeospatialAnalysisCrew",
    ):
        monkeypatch.setattr(main_mod, name, type(name, (), {}))


def test_successful_crew_model_is_written_as_json(osint_run):
    osint_dir, run = osint_run
    run()
    assert (osint_dir / "company_profile.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert (osint_dir / "geospatial_analysis.json").exists()


def test_stale_json_is_removed_when_its_crew_fails(osint_run):
    osint_dir, run = osint_run
    stale = osint_dir / "tech_stack.json"
    stale.write_text('{"company": "previous target"}', encoding="utf-8")

    run(failing_crew=main_mod.TechStackCrew)

    assert not stale.exists()
    assert (osint_dir / "company_profile.json").exists()
