"""The OSINT cross-reference step always leaves a validated global_report.json, never a stale one."""

import asyncio
import json
from pathlib import Path

import pytest

from epic_news import main as main_mod
from epic_news.main import ReceptionFlow
from epic_news.models.crews.cross_reference_report import CrossReferenceReport

_PAYLOAD = {
    "target": "ACME",
    "executive_summary": "Summary of ACME.",
    "detailed_findings": {"company_profile": "ok"},
    "confidence_assessment": "Medium.",
    "information_gaps": ["payroll"],
}


class _Output:
    def __init__(self, raw: str):
        self.raw = raw
        self.pydantic = None
        self.json_dict = None

    def __str__(self) -> str:
        return self.raw


@pytest.fixture
def osint_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "output" / "osint"
    d.mkdir(parents=True)
    monkeypatch.setattr(main_mod, "CrossReferenceReportCrew", type("Crew", (), {}))
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    return d


def _run(monkeypatch, kickoff) -> None:
    monkeypatch.setattr(main_mod, "akickoff_flow", kickoff)
    asyncio.run(ReceptionFlow(user_request="osint ACME")._run_cross_reference_report({"company": "ACME"}))


def test_raw_text_output_becomes_a_valid_global_report(osint_dir, monkeypatch):
    async def kickoff(crew, inputs):
        return _Output("Here is the report:\n" + json.dumps(_PAYLOAD))

    _run(monkeypatch, kickoff)

    saved = json.loads((osint_dir / "global_report.json").read_text(encoding="utf-8"))
    assert CrossReferenceReport.model_validate(saved).target == "ACME"


def test_stale_global_report_is_removed_before_the_kickoff(osint_dir, monkeypatch):
    stale = osint_dir / "global_report.json"
    stale.write_text(json.dumps({**_PAYLOAD, "target": "previous target"}), encoding="utf-8")
    seen = {}

    async def kickoff(crew, inputs):
        seen["stale_present"] = stale.exists()
        return _Output(json.dumps(_PAYLOAD))

    _run(monkeypatch, kickoff)

    assert seen["stale_present"] is False
    assert json.loads(stale.read_text(encoding="utf-8"))["target"] == "ACME"
