"""generate_deep_research: standard load_or_parse_model + emit_report path (S3)."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news import crew_registry
from epic_news import main as main_module
from epic_news.main import ReceptionFlow

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "raw_outputs" / "deep_research.txt"


class _StubCrew:
    pass


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str, write_file: bool) -> list[str]:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    (tmp_path / "output" / "deep_research").mkdir(parents=True)
    built: list[str] = []

    def _kickoff(_crew, inputs):
        if write_file:
            Path(inputs["output_file"]).write_text(raw, encoding="utf-8")
        return SimpleNamespace(raw=raw, output=None)

    def _assemble(model, _inputs, output_path, llm=None):
        built.append(model.title)
        Path(output_path).write_bytes(b"docx")
        return output_path

    monkeypatch.setattr(main_module, "DeepResearchCrew", _StubCrew)
    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    monkeypatch.setattr(main_module, "close_mcp", lambda _crew: None)
    monkeypatch.setattr(main_module, "dump_crewai_state", lambda *_a, **_k: None)
    monkeypatch.setitem(
        crew_registry.CREW_REGISTRY,
        "DEEPRESEARCH",
        dataclasses.replace(crew_registry.CREW_REGISTRY["DEEPRESEARCH"], docx_assembler=_assemble),
    )
    return built


def test_report_json_from_the_crew_builds_the_docx(tmp_path, monkeypatch):
    raw = FIXTURE.read_text(encoding="utf-8")
    built = _setup(tmp_path, monkeypatch, raw, write_file=True)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    flow.generate_deep_research()
    assert flow.state.output_file == "output/deep_research/report.docx"
    assert flow.state.deep_research_report is not None
    assert len(flow.state.deep_research_report.research_sections) == 5
    assert built == [flow.state.deep_research_report.title]


def test_stale_report_json_is_not_reused(tmp_path, monkeypatch):
    built = _setup(tmp_path, monkeypatch, "not json at all", write_file=False)
    stale = tmp_path / "output" / "deep_research" / "report.json"
    stale.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    flow = ReceptionFlow(user_request="deep research on something else")
    with pytest.raises(ValueError):
        flow.generate_deep_research()
    assert not stale.exists()
    assert built == []


def test_unusable_output_stops_the_run(tmp_path, monkeypatch):
    built = _setup(tmp_path, monkeypatch, "not json at all", write_file=False)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    before = flow.state.output_file
    with pytest.raises(ValueError):
        flow.generate_deep_research()
    assert built == []
    assert flow.state.output_file in (before, "output/deep_research/report.json")
    assert not (tmp_path / "output" / "deep_research" / "report.docx").exists()


def test_raw_output_is_used_when_the_crew_wrote_no_file(tmp_path, monkeypatch):
    raw = FIXTURE.read_text(encoding="utf-8")
    built = _setup(tmp_path, monkeypatch, raw, write_file=False)
    flow = ReceptionFlow(user_request="deep research on BeeGFS")
    flow.generate_deep_research()
    assert flow.state.output_file == "output/deep_research/report.docx"
    assert len(built) == 1
