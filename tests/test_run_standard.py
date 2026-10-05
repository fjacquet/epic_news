"""ReceptionFlow._run_standard: the steps the standard crews share (simplification S4)."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.crew_registry import CREW_REGISTRY
from epic_news.main import ReceptionFlow

POEM = {"title": "Titre", "poem": "Vers un\nVers deux"}


@pytest.fixture
def flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ReceptionFlow:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    (tmp_path / "output" / "poem").mkdir(parents=True)
    monkeypatch.setattr(main_module, "dump_crewai_state", lambda *_a, **_k: None)
    return ReceptionFlow(user_request="un poème sur la mer")


def _spec_with(assembler):
    return dataclasses.replace(CREW_REGISTRY["POEM"], docx_assembler=assembler)


def test_writes_the_docx_and_returns_output_and_model(flow, monkeypatch):
    def _kickoff(_crew, inputs):
        Path(inputs["output_file"]).write_text(json.dumps(POEM), encoding="utf-8")
        return SimpleNamespace(raw=json.dumps(POEM), output=None)

    seen: dict = {}

    def _assemble(model, inputs, output_path, llm=None):
        seen["inputs"] = inputs
        Path(output_path).write_bytes(b"docx")
        return output_path

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    output, model = flow._run_standard(_spec_with(_assemble), object(), flow.state.to_crew_inputs())
    assert model.title == "Titre"
    assert output.raw == json.dumps(POEM)
    assert flow.state.output_file == "output/poem/poem.docx"
    assert seen["inputs"]["user_request"] == "un poème sur la mer"  # state inputs, not crew inputs
    assert "output_file" in seen["inputs"]


def test_stale_json_is_deleted_before_the_kickoff(flow, monkeypatch):
    stale = Path("output/poem/poem.json")
    stale.write_text(json.dumps({"title": "Ancien", "poem": "vieux"}), encoding="utf-8")
    built: list = []

    def _kickoff(_crew, _inputs):
        assert not stale.exists()
        return SimpleNamespace(raw="not json at all", output=None)

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    with pytest.raises(ValueError):
        flow._run_standard(_spec_with(lambda *a, **k: built.append(a)), object(), flow.state.to_crew_inputs())
    assert built == []


def test_mcp_is_closed_when_the_kickoff_fails(flow, monkeypatch):
    closed: list = []
    crew = object()

    def _kickoff(_crew, _inputs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(main_module, "kickoff_flow", _kickoff)
    monkeypatch.setattr(main_module, "close_mcp", closed.append)
    with pytest.raises(RuntimeError, match="provider down"):
        flow._run_standard(CREW_REGISTRY["POEM"], crew, flow.state.to_crew_inputs())
    assert closed == [crew]
