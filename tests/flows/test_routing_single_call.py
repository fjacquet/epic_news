# tests/flows/test_routing_single_call.py
from types import SimpleNamespace

import epic_news.main as main_mod
from epic_news.models.extracted_info import ExtractedInfo


def _flow_with(selected):
    flow = main_mod.ReceptionFlow(user_request="req")
    flow.state.user_request = "req"
    flow.state.extracted_info = ExtractedInfo(main_subject_or_activity="x", selected_crew=selected)
    return flow


def test_valid_extracted_crew_skips_classify_crew(monkeypatch):
    calls = []
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda crew, inputs: calls.append(crew) or None)
    flow = _flow_with("pestel ")
    flow.classify()
    assert flow.state.selected_crew == "PESTEL"
    assert calls == []


def test_unknown_extracted_crew_falls_back_to_classify_crew(monkeypatch):
    seen = {}

    def fake_kickoff(crew, inputs):
        seen["crew"] = type(crew).__name__
        seen["inputs"] = inputs
        return SimpleNamespace(pydantic=SimpleNamespace(selected_crew="cooking"))

    monkeypatch.setattr(main_mod, "kickoff_flow", fake_kickoff)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = _flow_with("NOT_A_CREW")
    flow.classify()
    assert seen["crew"] == "ClassifyCrew"
    assert "routing_guide" in seen["inputs"]
    assert flow.state.selected_crew == "COOKING"


def test_missing_extraction_falls_back(monkeypatch):
    monkeypatch.setattr(
        main_mod,
        "kickoff_flow",
        lambda crew, inputs: SimpleNamespace(pydantic=SimpleNamespace(selected_crew="POEM")),
    )
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = _flow_with(None)
    flow.classify()
    assert flow.state.selected_crew == "POEM"


def test_classification_without_pydantic_is_unknown():
    categories = {"POEM": "POEM", "UNKNOWN": "UNKNOWN"}
    assert (
        main_mod._category_from_classification(SimpleNamespace(pydantic=None, raw="POEM"), categories)
        == "UNKNOWN"
    )
    assert (
        main_mod._category_from_classification(
            SimpleNamespace(pydantic=SimpleNamespace(selected_crew="poem")), categories
        )
        == "POEM"
    )


def test_extraction_receives_categories_and_guide(monkeypatch):
    seen = {}

    def fake_kickoff(crew, inputs):
        seen.update(inputs)
        return SimpleNamespace(tasks_output=[SimpleNamespace(raw="brief")], pydantic=ExtractedInfo())

    monkeypatch.setattr(main_mod, "kickoff_flow", fake_kickoff)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = main_mod.ReceptionFlow(user_request="req")
    flow.state.user_request = "req"
    flow.extract_info()
    assert seen["user_request"] == "req"
    assert "PESTEL" in seen["categories"] and "UNKNOWN" not in seen["categories"]
    assert "IMPORTANT DISTINCTIONS" in seen["routing_guide"]
