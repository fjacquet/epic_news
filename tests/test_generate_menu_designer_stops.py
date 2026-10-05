"""generate_menu_designer runs the menu crew through kickoff_flow and stops when it gives no plan."""

from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow
from epic_news.utils.interrupt import RunCancelledError
from epic_news.utils.menu_plan_validator import MenuPlanError


def _flow_with(monkeypatch, kickoff) -> tuple[ReceptionFlow, list[str]]:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "kickoff_flow", kickoff)
    monkeypatch.setattr(main_module, "emit_report", lambda *a, **k: calls.append("emit_report"))
    monkeypatch.setattr(main_module, "assemble_menu_docx", lambda *a, **k: calls.append("docx"))
    monkeypatch.setattr(
        ReceptionFlow, "_generate_menu_recipes", lambda self, specs: calls.append("recipes") or []
    )
    return ReceptionFlow(user_request="menu de la semaine"), calls


def test_no_plan_stops_the_run_and_produces_nothing(monkeypatch):
    flow, calls = _flow_with(monkeypatch, lambda crew, inputs: SimpleNamespace(pydantic=None, raw="rien"))
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        flow.generate_menu_designer()
    assert calls == []
    assert flow.state.report is None


def test_crew_error_propagates_and_produces_nothing(monkeypatch):
    def _boom(crew, inputs):
        raise RuntimeError("llm down")

    flow, calls = _flow_with(monkeypatch, _boom)
    with pytest.raises(RuntimeError, match="llm down"):
        flow.generate_menu_designer()
    assert calls == []


def test_cancel_propagates_unchanged(monkeypatch):
    def _cancel(crew, inputs):
        raise RunCancelledError("menu")

    flow, calls = _flow_with(monkeypatch, _cancel)
    with pytest.raises(RunCancelledError):
        flow.generate_menu_designer()
    assert calls == []


def test_menu_crew_runs_through_kickoff_flow_with_its_inputs(monkeypatch):
    seen: dict = {}

    def _kickoff(crew, inputs):
        seen["crew"] = type(crew).__name__
        seen["inputs"] = inputs
        return SimpleNamespace(pydantic=None, raw="")

    flow, _ = _flow_with(monkeypatch, _kickoff)
    with pytest.raises(MenuPlanError):
        flow.generate_menu_designer()
    assert seen["crew"] == "MenuDesignerCrew"
    assert set(seen["inputs"]) == {
        "constraints",
        "preferences",
        "user_context",
        "season",
        "current_date",
        "menu_slug",
        "num_days",
    }
