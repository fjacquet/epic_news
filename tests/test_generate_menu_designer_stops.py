"""generate_menu_designer must stop the run, not ship a placeholder menu, when no plan is produced."""

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow
from epic_news.services.menu_designer_service import MenuPlanError


def test_generate_menu_designer_raises_and_produces_nothing(monkeypatch):
    calls: list[str] = []

    class _FailingService:
        def generate_menu_plan(self, **_kwargs):
            raise MenuPlanError("no usable menu plan in the crew output")

    monkeypatch.setattr(main_module, "MenuDesignerService", _FailingService)
    monkeypatch.setattr(main_module, "emit_report", lambda *a, **k: calls.append("emit_report"))
    monkeypatch.setattr(main_module, "render_and_write_html", lambda *a, **k: calls.append("render"))
    monkeypatch.setattr(
        ReceptionFlow, "_generate_menu_recipes", lambda self, specs: calls.append("recipes") or []
    )

    flow = ReceptionFlow(user_request="menu de la semaine")
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        flow.generate_menu_designer()

    assert calls == []
    assert not flow.state.menu_designer_report
