"""The OSINT parallel run saves each report as JSON (no HTML), clears stale ones first, and stops on a failed crew."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from epic_news import main as main_mod
from epic_news.main import ReceptionFlow


@pytest.fixture
def osint_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "osint").mkdir(parents=True)

    model = MagicMock()
    model.model_dump_json.return_value = '{"ok": true}'
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "parse_crewai_output", lambda *a, **k: model)

    async def no_cross_reference(self, inputs):
        return None

    monkeypatch.setattr(ReceptionFlow, "_run_cross_reference_report", no_cross_reference)

    def run(failing_crew: type | None = None) -> ReceptionFlow:
        async def fake_kickoff(crew, inputs):
            if failing_crew is not None and isinstance(crew, failing_crew):
                raise RuntimeError("boom")
            return {"raw": "output"}

        monkeypatch.setattr(main_mod, "akickoff_flow", fake_kickoff)
        flow = ReceptionFlow(user_request="osint on Acme")
        asyncio.run(flow._run_osint_parallel())
        return flow

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
    assert not list(osint_dir.glob("*.html"))


def test_stale_json_is_removed_when_its_crew_fails(osint_run):
    osint_dir, run = osint_run
    stale = osint_dir / "tech_stack.json"
    stale.write_text('{"company": "previous target"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="tech_stack"):
        run(failing_crew=main_mod.TechStackCrew)

    assert not stale.exists()
    assert (osint_dir / "company_profile.json").exists()


def test_state_osint_holds_one_model_per_crew(osint_run, monkeypatch):
    _, run = osint_run

    class Fake(BaseModel):
        ok: bool = True

    monkeypatch.setattr(main_mod, "parse_crewai_output", lambda *a, **k: Fake())
    flow = run()

    assert set(flow.state.osint) == {
        "company_profile",
        "tech_stack",
        "web_presence",
        "hr_intelligence",
        "legal_analysis",
        "geospatial_analysis",
    }
    assert all(isinstance(model, BaseModel) for model in flow.state.osint.values())


def test_a_failed_crew_stops_the_run_before_the_cross_reference(osint_run, monkeypatch):
    _, run = osint_run
    cross_reference_ran = []

    async def cross_reference(self, inputs):
        cross_reference_ran.append(True)

    monkeypatch.setattr(ReceptionFlow, "_run_cross_reference_report", cross_reference)

    with pytest.raises(RuntimeError, match="OSINT crews failed: tech_stack") as excinfo:
        run(failing_crew=main_mod.TechStackCrew)

    assert isinstance(excinfo.value.__cause__, RuntimeError)
    assert str(excinfo.value.__cause__) == "boom"
    assert cross_reference_ran == []
