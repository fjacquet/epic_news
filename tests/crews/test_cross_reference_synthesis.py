import json
from pathlib import Path

import epic_news.main as main_mod
from epic_news.crews.cross_reference_report_crew.synthesis_crew import CrossReferenceSynthesisCrew
from epic_news.models.crews.cross_reference_report import CrossReferenceReport


def test_synthesis_crew_is_one_tool_free_task():
    crew = CrossReferenceSynthesisCrew().crew()
    assert len(crew.tasks) == 1 and len(crew.agents) == 1
    assert crew.agents[0].tools == []
    assert crew.tasks[0].output_pydantic is CrossReferenceReport


def test_osint_reports_json_reads_available_reports(tmp_path: Path):
    (tmp_path / "company_profile.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    (tmp_path / "tech_stack.json").write_text("not json", encoding="utf-8")
    payload = json.loads(main_mod._osint_reports_json(tmp_path))
    assert payload["company_profile"] == {"x": 1}
    assert "tech_stack" not in payload
    assert "legal_analysis" not in payload


def test_mode_defaults_to_research(monkeypatch):
    monkeypatch.delenv("CROSS_REFERENCE_MODE", raising=False)
    assert main_mod._cross_reference_mode() == "research"
    monkeypatch.setenv("CROSS_REFERENCE_MODE", " Synthesis ")
    assert main_mod._cross_reference_mode() == "synthesis"
    monkeypatch.setenv("CROSS_REFERENCE_MODE", "other")
    assert main_mod._cross_reference_mode() == "research"
