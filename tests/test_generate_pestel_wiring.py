"""End-to-end wiring test for ReceptionFlow.generate_pestel — no LLM calls.

Validates the plumbing between the PESTEL crew's JSON output, the
``PestelReport`` model, the markdown renderer, and ``ContentState`` —
without actually invoking any agent.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.extracted_info import ExtractedInfo


def _valid_pestel_payload() -> dict:
    dim = {
        "summary": "Summary text",
        "key_factors": ["factor-A", "factor-B"],
        "impact_analysis": "Strategic impact narrative",
        "sources": ["https://example.com/src"],
    }
    return {
        "topic": "Test Topic",
        "executive_summary": "Exec summary",
        "political": dim,
        "economic": dim,
        "social": dim,
        "technological": dim,
        "environmental": dim,
        "legal": dim,
        "synthesis": "Cross-dim synthesis",
        "generated_at": "2026-04-25",
    }


@pytest.fixture
def pestel_flow_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Run generate_pestel inside an isolated tmp cwd with stubbed crew/IO."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir(exist_ok=True)

    output_dir = tmp_path / "output" / "pestel"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(
        json.dumps(_valid_pestel_payload()), encoding="utf-8"
    )

    calls = {"kickoff": 0, "dump": 0, "pestel_init": 0}

    def _fake_kickoff_flow(crew, inputs):
        calls["kickoff"] += 1
        calls["last_inputs"] = inputs
        return SimpleNamespace(raw=json.dumps(_valid_pestel_payload()))

    def _fake_dump(_output, _label):
        calls["dump"] += 1

    class _StubPestelCrew:
        def __init__(self) -> None:
            calls["pestel_init"] += 1

    monkeypatch.setattr(main_module, "kickoff_flow", _fake_kickoff_flow)
    monkeypatch.setattr(main_module, "dump_crewai_state", _fake_dump)
    monkeypatch.setattr(main_module, "PestelCrew", _StubPestelCrew)

    return tmp_path, calls


def test_generate_pestel_populates_state_and_markdown(pestel_flow_env) -> None:
    tmp_path, calls = pestel_flow_env

    flow = ReceptionFlow(user_request="rapport PESTEL Reyl")
    flow.generate_pestel()

    assert calls["kickoff"] == 1
    assert calls["dump"] == 1
    assert calls["pestel_init"] == 1

    # State holds a fully-validated PestelReport instance.
    assert isinstance(flow.state.pestel_report, PestelReport)
    assert flow.state.pestel_report.topic == "Test Topic"

    # output_file ends pointing at the markdown, not the json.
    assert flow.state.output_file.endswith("report.md")
    md_path = tmp_path / "output" / "pestel" / "report.md"
    assert md_path.exists()


def test_generate_pestel_markdown_contains_all_sections(pestel_flow_env) -> None:
    tmp_path, _calls = pestel_flow_env

    flow = ReceptionFlow(user_request="PESTEL test")
    flow.generate_pestel()

    md = (tmp_path / "output" / "pestel" / "report.md").read_text(encoding="utf-8")

    assert "# PESTEL Analysis — Test Topic" in md
    for heading in (
        "🏛️ Political",
        "💰 Economic",
        "👥 Social",
        "💻 Technological",
        "🌍 Environmental",
        "⚖️ Legal",
        "🎯 Synthesis",
    ):
        assert heading in md
    assert "Cross-dim synthesis" in md
    assert "https://example.com/src" in md


def test_generate_pestel_injects_current_date(pestel_flow_env) -> None:
    """current_date must be added to inputs before kickoff."""
    _tmp_path, calls = pestel_flow_env

    flow = ReceptionFlow(user_request="PESTEL test")
    flow.generate_pestel()

    inputs = calls["last_inputs"]
    assert "current_date" in inputs
    # YYYY-MM-DD shape
    parts = inputs["current_date"].split("-")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)


def test_generate_pestel_falls_back_to_raw_when_json_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the crew's JSON file is missing, generate_pestel must hydrate the model
    from the crew output's raw attribute via load_or_parse_model fallback."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir(exist_ok=True)
    # Note: no report.json written.

    raw_payload = json.dumps(_valid_pestel_payload())

    def _fake_kickoff_flow(_crew, _inputs):
        return SimpleNamespace(raw=raw_payload)

    monkeypatch.setattr(main_module, "kickoff_flow", _fake_kickoff_flow)
    monkeypatch.setattr(main_module, "dump_crewai_state", lambda *_a, **_kw: None)
    monkeypatch.setattr(main_module, "PestelCrew", lambda: SimpleNamespace())

    flow = ReceptionFlow(user_request="PESTEL fallback")
    flow.generate_pestel()

    assert isinstance(flow.state.pestel_report, PestelReport)
    md = (tmp_path / "output" / "pestel" / "report.md").read_text(encoding="utf-8")
    assert "Test Topic" in md


def test_generate_pestel_uses_target_company_as_topic(pestel_flow_env) -> None:
    """When extracted_info.target_company is set, it overrides the topic
    coming from main_subject_or_activity, and language/geography are injected.
    """
    _tmp_path, calls = pestel_flow_env

    flow = ReceptionFlow(user_request="rapport PESTEL banque Reyl en français")
    flow.state.extracted_info = ExtractedInfo(
        main_subject_or_activity="rapport PESTEL",  # the *activity*, not the entity
        target_company="Reyl",
        destination_location="Switzerland",
        output_language="French",
    )
    flow.generate_pestel()

    sent_inputs = calls["last_inputs"]
    assert sent_inputs["topic"] == "Reyl"
    assert sent_inputs["geography"] == "Switzerland"
    assert sent_inputs["language"] == "French"


def test_generate_pestel_defaults_language_and_geography_when_missing(
    pestel_flow_env,
) -> None:
    """No extracted_info → safe defaults (English, global)."""
    _tmp_path, calls = pestel_flow_env

    flow = ReceptionFlow(user_request="give me a PESTEL on AI")
    flow.state.extracted_info = None
    flow.generate_pestel()

    sent = calls["last_inputs"]
    assert sent["language"] == "English"
    assert sent["geography"] == "global"


def test_generate_pestel_uses_destination_when_no_company(pestel_flow_env) -> None:
    """If only destination_location is set, it becomes the topic AND geography
    collapses to 'global' (no double-mention)."""
    _tmp_path, calls = pestel_flow_env

    flow = ReceptionFlow(user_request="PESTEL Switzerland")
    flow.state.extracted_info = ExtractedInfo(
        destination_location="Switzerland",
        output_language="English",
    )
    flow.generate_pestel()

    sent = calls["last_inputs"]
    assert sent["topic"] == "Switzerland"
    # destination == entity → geography falls back to 'global'
    assert sent["geography"] == "global"
